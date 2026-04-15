"""Seed reference dimensions (stations, lines, calendar) into the bronze zone.

The reference data is small, slowly-changing, and lives next to the streaming
tap data in the bronze zone as parquet files. Silver/gold models read it as
dimension sources.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import typer

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger

app = typer.Typer(help="Seed station, line, and date dimensions into bronze.")
log = get_logger(__name__)


_LINES = [
    {"line_id": "LSW", "line_name": "Lakeshore West", "mode": "rail", "is_express": False},
    {"line_id": "LSE", "line_name": "Lakeshore East", "mode": "rail", "is_express": False},
    {"line_id": "UPX", "line_name": "UP Express", "mode": "rail", "is_express": True},
]

_STATIONS = [
    {"station_id": "UNION", "name": "Union Station", "line_id": "LSW", "zone": 1, "lat": 43.6453, "lon": -79.3806},
    {"station_id": "EXHIBITION", "name": "Exhibition GO", "line_id": "LSW", "zone": 1, "lat": 43.6347, "lon": -79.4154},
    {"station_id": "MIMICO", "name": "Mimico GO", "line_id": "LSW", "zone": 2, "lat": 43.6111, "lon": -79.4982},
    {"station_id": "OAKVILLE", "name": "Oakville GO", "line_id": "LSW", "zone": 3, "lat": 43.4517, "lon": -79.6864},
    {"station_id": "BURLINGTON", "name": "Burlington GO", "line_id": "LSW", "zone": 4, "lat": 43.3489, "lon": -79.8108},
    {"station_id": "HAMILTON", "name": "West Harbour GO", "line_id": "LSW", "zone": 5, "lat": 43.2643, "lon": -79.8718},
    {"station_id": "EAST_HARBOUR", "name": "East Harbour", "line_id": "LSE", "zone": 1, "lat": 43.6537, "lon": -79.3450},
    {"station_id": "DANFORTH", "name": "Danforth GO", "line_id": "LSE", "zone": 2, "lat": 43.6797, "lon": -79.3098},
    {"station_id": "SCARBOROUGH", "name": "Scarborough GO", "line_id": "LSE", "zone": 2, "lat": 43.7068, "lon": -79.2685},
    {"station_id": "PICKERING", "name": "Pickering GO", "line_id": "LSE", "zone": 3, "lat": 43.8389, "lon": -79.0779},
    {"station_id": "OSHAWA", "name": "Oshawa GO", "line_id": "LSE", "zone": 5, "lat": 43.8636, "lon": -78.8740},
    {"station_id": "BLOOR_UP", "name": "Bloor UP", "line_id": "UPX", "zone": 1, "lat": 43.6555, "lon": -79.4506},
    {"station_id": "WESTON_UP", "name": "Weston UP", "line_id": "UPX", "zone": 2, "lat": 43.7011, "lon": -79.5174},
    {"station_id": "PEARSON_UP", "name": "Pearson Airport UP", "line_id": "UPX", "zone": 3, "lat": 43.6810, "lon": -79.6177},
]


def _date_dim(start: date, end: date) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    current = start
    while current <= end:
        records.append(
            {
                "date_key": int(current.strftime("%Y%m%d")),
                "calendar_date": current.isoformat(),
                "year": current.year,
                "quarter": (current.month - 1) // 3 + 1,
                "month": current.month,
                "month_name": current.strftime("%B"),
                "day_of_month": current.day,
                "day_of_week_iso": current.isoweekday(),
                "day_name": current.strftime("%A"),
                "is_weekend": current.isoweekday() >= 6,
            }
        )
        current += timedelta(days=1)
    return records


def _write_parquet(records: list[dict[str, object]], s3_client: object, bucket: str, key: str) -> None:
    table = pa.Table.from_pylist(records)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression="zstd")
    buffer.seek(0)
    s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())  # type: ignore[attr-defined]


@app.command()
def run(
    start_year: int = typer.Option(2024, help="First calendar year to seed."),
    end_year: int = typer.Option(2028, help="Last calendar year to seed (inclusive)."),
    output_local: Path | None = typer.Option(None, help="Also write parquet locally for inspection."),
) -> None:
    """Seed stations, lines, and the date dimension into bronze."""
    settings = get_settings()
    configure_logging(level=settings.telemetry.log_level)

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.storage.endpoint,
        aws_access_key_id=settings.storage.access_key,
        aws_secret_access_key=settings.storage.secret_key.get_secret_value(),
        region_name="us-east-1",
        use_ssl=settings.storage.use_ssl,
    )

    seeds = {
        "bronze/reference/lines/part-0.parquet": _LINES,
        "bronze/reference/stations/part-0.parquet": _STATIONS,
        "bronze/reference/date/part-0.parquet": _date_dim(date(start_year, 1, 1), date(end_year, 12, 31)),
    }

    for key, records in seeds.items():
        _write_parquet(records, s3, settings.storage.bucket, key)
        log.info("seed_written", key=key, records=len(records))
        if output_local is not None:
            output_local.mkdir(parents=True, exist_ok=True)
            (output_local / Path(key).name).write_bytes(BytesIO().getvalue())  # placeholder

    log.info("seed_completed", at=datetime.now(tz=UTC).isoformat())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
