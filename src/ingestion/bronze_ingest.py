"""Consume the AFC tap stream from Kafka and land it in the bronze zone.

Local development uses MinIO as an ADLS Gen2 stand-in. In production the same
process is replaced by Databricks Auto Loader running against Azure Event Hubs
into ADLS Gen2 — the bronze data layout below is bit-identical so silver/gold
transformations don't change.

Layout: ``bronze/afc_taps/dt=YYYY-MM-DD/hour=HH/part-<uuid>.parquet``
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from confluent_kafka import Consumer, KafkaException
from opentelemetry import metrics, trace

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.otel import configure_otel

app = typer.Typer(help="Bronze-zone ingester for the synthetic AFC tap stream.")
log = get_logger(__name__)
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)


_SCHEMA = pa.schema(
    [
        pa.field("tap_id", pa.string(), nullable=False),
        pa.field("card_token", pa.string(), nullable=False),
        pa.field("station_id", pa.string(), nullable=False),
        pa.field("line", pa.string(), nullable=False),
        pa.field("zone", pa.int32(), nullable=False),
        pa.field("fare_class", pa.string(), nullable=False),
        pa.field("fare_amount_cad", pa.float64(), nullable=False),
        pa.field("tap_type", pa.string(), nullable=False),
        pa.field("tap_timestamp_utc", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("device_id", pa.string(), nullable=False),
        pa.field("schema_version", pa.string(), nullable=False),
        pa.field("ingest_timestamp_utc", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)


def _normalise_record(payload: dict[str, Any], *, ingest_ts: datetime) -> dict[str, Any]:
    return {
        **payload,
        "tap_timestamp_utc": datetime.fromisoformat(payload["tap_timestamp_utc"]),
        "ingest_timestamp_utc": ingest_ts,
    }


def _write_batch(records: list[dict[str, Any]], s3_client: Any, bucket: str) -> str:
    batch = pa.Table.from_pylist(records, schema=_SCHEMA)
    ts = records[0]["tap_timestamp_utc"]
    key = (
        "bronze/afc_taps/"
        f"dt={ts.strftime('%Y-%m-%d')}/"
        f"hour={ts.strftime('%H')}/"
        f"part-{uuid.uuid4().hex}.parquet"
    )
    buffer = BytesIO()
    pq.write_table(batch, buffer, compression="zstd")
    buffer.seek(0)
    s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    return key


@app.command()
def run(
    batch_size: int = typer.Option(500, help="Records per parquet file."),
    flush_interval_seconds: float = typer.Option(30.0, help="Force flush on time even if batch is under-full."),
    max_runtime_seconds: int | None = typer.Option(None, help="Stop after N seconds."),
) -> None:
    """Run the bronze ingester. Idempotent at the message level (per-tap uuid)."""
    settings = get_settings()
    configure_logging(level=settings.telemetry.log_level)
    configure_otel(settings.telemetry)

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka.bootstrap,
            "group.id": f"{settings.kafka.client_id}-bronze-ingest",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "session.timeout.ms": 45_000,
        }
    )
    consumer.subscribe([settings.kafka.topic_afc_taps])

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.storage.endpoint,
        aws_access_key_id=settings.storage.access_key,
        aws_secret_access_key=settings.storage.secret_key.get_secret_value(),
        region_name="us-east-1",
        use_ssl=settings.storage.use_ssl,
    )

    files_written = meter.create_counter(
        "lakehouse_bronze_files_written_total",
        description="Parquet files written to the bronze zone.",
    )

    batch: list[dict[str, Any]] = []
    last_flush = time.monotonic()
    start_at = time.monotonic()

    log.info(
        "bronze_ingest_started",
        topic=settings.kafka.topic_afc_taps,
        bucket=settings.storage.bucket,
        batch_size=batch_size,
    )

    try:
        while True:
            if max_runtime_seconds and time.monotonic() - start_at >= max_runtime_seconds:
                log.info("bronze_ingest_max_runtime_reached")
                break

            msg = consumer.poll(1.0)
            if msg is None:
                if batch and (time.monotonic() - last_flush) > flush_interval_seconds:
                    with tracer.start_as_current_span("flush_batch"):
                        key = _write_batch(batch, s3, settings.storage.bucket)
                        log.info("bronze_batch_flushed", key=key, records=len(batch), reason="time")
                        files_written.add(1, {"reason": "time"})
                        consumer.commit(asynchronous=False)
                        batch.clear()
                        last_flush = time.monotonic()
                continue
            if msg.error():
                raise KafkaException(msg.error())

            payload = json.loads(msg.value())
            batch.append(_normalise_record(payload, ingest_ts=datetime.now(tz=UTC)))

            if len(batch) >= batch_size:
                with tracer.start_as_current_span("flush_batch"):
                    key = _write_batch(batch, s3, settings.storage.bucket)
                    log.info("bronze_batch_flushed", key=key, records=len(batch), reason="size")
                    files_written.add(1, {"reason": "size"})
                    consumer.commit(asynchronous=False)
                    batch.clear()
                    last_flush = time.monotonic()
    finally:
        if batch:
            try:
                _write_batch(batch, s3, settings.storage.bucket)
            except Exception:  # noqa: BLE001
                log.exception("bronze_final_flush_failed")
        consumer.close()
        log.info("bronze_ingest_stopped")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

# end of bronze consumer
