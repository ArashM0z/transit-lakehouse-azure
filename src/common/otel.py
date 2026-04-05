"""OpenTelemetry initialisation for service-side traces, metrics, and logs."""

from __future__ import annotations

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.common.config import TelemetrySettings


def configure_otel(settings: TelemetrySettings) -> None:
    """Configure global OpenTelemetry providers for traces and metrics.

    Idempotent — safe to call multiple times during process startup.
    """
    resource = Resource.create({SERVICE_NAME: settings.service_name})

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.exporter_otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.exporter_otlp_endpoint, insecure=True),
        export_interval_millis=15_000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
