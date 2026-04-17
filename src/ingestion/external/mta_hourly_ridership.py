"""MTA Subway Hourly Ridership loader.

Pulls real NYC MTA subway hourly ridership data from the State of New York's
Socrata Open Data API (`data.ny.gov`) into the lakehouse bronze zone. The
upstream dataset is *MTA Subway Hourly Ridership: Beginning 2025*
(resource ID `wujg-7c2s`), refreshed daily.

This is the real public record — 50M+ rows by 2025 year-end, partitioned by
the agency itself by transit timestamp. Joshua Oh's team at Metrolinx is on
the equivalent PRESTO tap stream; the methodology this loader demonstrates is
the same shape, just with the authoritative dataset that's actually publishable.

Run:
    python -m src.ingestion.external.mta_hourly_ridership \
        --start 2025-01-01 --end 2025-01-07 --out /tmp/bronze/mta_hourly
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import typer
from tenacity import retry, stop_after_attempt, wait_exponential

from src.common.logging import configure_logging
from src.common.telemetry import meter, tracer

SOCRATA_BASE = "https://data.ny.gov/resource/wujg-7c2s.json"
DEFAULT_PAGE_SIZE = 50_000
USER_AGENT = "transit-lakehouse-azure/0.1 (+https://github.com/ArashM0z/transit-lakehouse-azure)"

app = typer.Typer(help="MTA Subway Hourly Ridership ingester.", add_completion=False)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def _fetch_page(
    client: httpx.Client,
    *,
    where: str,
    offset: int,
    limit: int,
    app_token: str | None,
) -> list[dict[str, Any]]:
    """Fetch one page of rows from Socrata. Retries on transient failure."""
    params = {
        "$where": where,
        "$limit": str(limit),
        "$offset": str(offset),
        "$order": "transit_timestamp",
    }
    headers = {"User-Agent": USER_AGENT}
    if app_token:
        headers["X-App-Token"] = app_token
    r = client.get(SOCRATA_BASE, params=params, headers=headers, timeout=60.0)
    r.raise_for_status()
    data: list[dict[str, Any]] = r.json()
    return data


def _coerce_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise types for the bronze parquet schema."""
    return {
        "transit_timestamp": raw.get("transit_timestamp"),
        "transit_mode": raw.get("transit_mode"),
        "station_complex_id": raw.get("station_complex_id"),
        "station_complex": raw.get("station_complex"),
        "borough": raw.get("borough"),
        "payment_method": raw.get("payment_method"),
        "fare_class_category": raw.get("fare_class_category"),
        "ridership": float(raw.get("ridership", 0) or 0),
        "transfers": float(raw.get("transfers", 0) or 0),
        "latitude": float(raw["latitude"]) if raw.get("latitude") else None,
        "longitude": float(raw["longitude"]) if raw.get("longitude") else None,
    }


@app.command()
def load(
    start: datetime = typer.Option(..., "--start", formats=["%Y-%m-%d", "%Y-%m-%dT%H"]),
    end: datetime = typer.Option(..., "--end", formats=["%Y-%m-%d", "%Y-%m-%dT%H"]),
    out: Path = typer.Option(Path("/tmp/bronze/mta_hourly"), "--out"),
    page_size: int = typer.Option(DEFAULT_PAGE_SIZE, "--page-size"),
    app_token: str = typer.Option("", "--app-token", envvar="SOCRATA_APP_TOKEN"),
) -> None:
    """Pull the MTA hourly ridership feed for a date range and land it as Parquet."""
    logger = configure_logging(level="INFO", service_name="mta-hourly-loader")
    span_tracer = tracer("mta-hourly-loader")
    rows_counter = meter("mta-hourly-loader").create_counter(
        "mta_rows_ingested_total", description="MTA hourly rows ingested", unit="1"
    )

    out.mkdir(parents=True, exist_ok=True)

    if end <= start:
        raise typer.BadParameter("--end must be after --start")

    # Iterate by day to keep memory bounded and align partitioning with the
    # downstream silver model.
    cursor = date.fromordinal(start.toordinal())
    end_date = date.fromordinal(end.toordinal())
    total_rows = 0
    with httpx.Client() as client:
        while cursor <= end_date:
            next_day = cursor + timedelta(days=1)
            where = (
                f"transit_timestamp between '{cursor.isoformat()}T00:00:00' "
                f"and '{next_day.isoformat()}T00:00:00'"
            )
            partition_dir = out / f"event_date={cursor.isoformat()}"
            partition_dir.mkdir(parents=True, exist_ok=True)

            day_rows: list[dict[str, Any]] = []
            offset = 0
            with span_tracer.start_as_current_span("mta_day_fetch") as span:
                span.set_attribute("event_date", cursor.isoformat())
                while True:
                    page = _fetch_page(
                        client,
                        where=where,
                        offset=offset,
                        limit=page_size,
                        app_token=app_token or None,
                    )
                    if not page:
                        break
                    day_rows.extend(_coerce_row(r) for r in page)
                    offset += len(page)
                    logger.debug(
                        "mta_page_fetched",
                        event_date=cursor.isoformat(),
                        offset=offset,
                        page_size=len(page),
                    )
                    if len(page) < page_size:
                        break

            if day_rows:
                table = pa.Table.from_pylist(day_rows)
                out_path = partition_dir / f"part-{cursor.isoformat()}.parquet"
                pq.write_table(table, out_path, compression="zstd")
                rows_counter.add(len(day_rows), attributes={"event_date": cursor.isoformat()})
                total_rows += len(day_rows)
                logger.info(
                    "mta_day_landed",
                    event_date=cursor.isoformat(),
                    rows=len(day_rows),
                    file=str(out_path),
                )
            else:
                logger.warning("mta_day_empty", event_date=cursor.isoformat())

            cursor = next_day

    logger.info("mta_load_complete", total_rows=total_rows, days=(end_date - start.date()).days + 1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
