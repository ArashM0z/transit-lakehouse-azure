"""OpenTelemetry setup for traces, metrics, and logs export.

Spans are emitted to the OTLP collector defined in TelemetrySettings; in
production this is the Azure Monitor OTLP endpoint, locally it is the
in-cluster collector that fans out to Tempo / Prometheus / Loki.

This module installs:
- Tracer provider with a batch span exporter
- Meter provider exporting at 30-second intervals
- Resource attributes shared across all signals (service name, environment)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from .settings import TelemetrySettings


def configure_telemetry(settings: TelemetrySettings) -> None:
    """Configure global OpenTelemetry providers. Idempotent on repeated calls."""
    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "deployment.environment": settings.deployment_environment,
        }
    )

    # Tracing -----------------------------------------------------------------
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=str(settings.exporter_otlp_endpoint), insecure=True)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics -----------------------------------------------------------------
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=str(settings.exporter_otlp_endpoint), insecure=True),
        export_interval_millis=30_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)


def tracer(name: str = __name__) -> trace.Tracer:
    return trace.get_tracer(name)


def meter(name: str = __name__) -> metrics.Meter:
    return metrics.get_meter(name)
