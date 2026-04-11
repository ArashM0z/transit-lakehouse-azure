"""Synthetic AFC fare-tap stream generator.

Produces realistic tap events to Kafka modelling:

* Hourly demand curves with morning and afternoon commute peaks.
* Heterogeneous fare classes (adult, senior, youth, child, concession).
* Event-day uplift drawn from a configurable event calendar.
* Per-station weighting reflecting line and zone.

The intent is to mirror the shape of a real PRESTO-tap stream closely enough
that downstream silver/gold transformations and forecasting models behave
exactly as they would against production data.
"""

from __future__ import annotations

import json
import math
import random
import signal
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import typer
from confluent_kafka import Producer
from opentelemetry import metrics, trace
from rich.console import Console

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.otel import configure_otel

app = typer.Typer(help="Synthetic AFC fare-tap stream generator.")
console = Console()
log = get_logger(__name__)
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)


@dataclass(slots=True, frozen=True)
class Station:
    """A station node in the synthetic network."""

    id: str
    name: str
    line: str
    zone: int
    latitude: float
    longitude: float
    base_weight: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Station:
        return cls(
            id=payload["id"],
            name=payload["name"],
            line=payload["line"],
            zone=int(payload["zone"]),
            latitude=float(payload["latitude"]),
            longitude=float(payload["longitude"]),
            base_weight=float(payload["base_weight"]),
        )


@dataclass(slots=True, frozen=True)
class Event:
    """A special event that uplifts demand at one or more stations."""

    name: str
    start: datetime
    end: datetime
    station_ids: tuple[str, ...]
    uplift_multiplier: float

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Event:
        return cls(
            name=payload["name"],
            start=datetime.fromisoformat(payload["start"]).replace(tzinfo=UTC),
            end=datetime.fromisoformat(payload["end"]).replace(tzinfo=UTC),
            station_ids=tuple(payload["station_ids"]),
            uplift_multiplier=float(payload["uplift_multiplier"]),
        )

    def applies(self, ts: datetime, station_id: str) -> bool:
        return self.start <= ts <= self.end and station_id in self.station_ids


_FARE_CLASS_DISTRIBUTION: tuple[tuple[str, float], ...] = (
    ("ADULT", 0.62),
    ("SENIOR", 0.14),
    ("YOUTH", 0.10),
    ("CHILD", 0.04),
    ("CONCESSION", 0.10),
)

_FARE_BY_CLASS: dict[str, float] = {
    "ADULT": 6.05,
    "SENIOR": 4.50,
    "YOUTH": 4.20,
    "CHILD": 0.00,
    "CONCESSION": 3.10,
}


def _hourly_demand_curve(hour: int) -> float:
    """Return a unitless multiplier reflecting demand by hour of day.

    Two-peak commuter curve: morning peak around 08:00, evening peak around
    17:00, overnight trough near 03:00.
    """
    morning = math.exp(-((hour - 8) ** 2) / 6.0)
    evening = math.exp(-((hour - 17) ** 2) / 8.0)
    base = 0.08
    return base + 0.50 * morning + 0.60 * evening


def _weighted_pick(items: list[tuple[Any, float]], rng: random.Random) -> Any:
    total = sum(weight for _, weight in items)
    pick = rng.uniform(0, total)
    cumulative = 0.0
    for value, weight in items:
        cumulative += weight
        if pick <= cumulative:
            return value
    return items[-1][0]


def _load_stations(path: Path) -> list[Station]:
    if not path.exists():
        log.warning("station_catalog_missing", path=str(path), action="using_default_stations")
        return _DEFAULT_STATIONS
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Station.from_dict(item) for item in payload]


def _load_events(path: Path) -> list[Event]:
    if not path.exists():
        log.warning("event_calendar_missing", path=str(path), action="empty_event_calendar")
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Event.from_dict(item) for item in payload]


# --- baked-in fall-back catalogue so the generator runs with zero config ---
_DEFAULT_STATIONS: list[Station] = [
    Station("UNION", "Union Station", "Lakeshore West", 1, 43.6453, -79.3806, 5.0),
    Station("EXHIBITION", "Exhibition GO", "Lakeshore West", 1, 43.6347, -79.4154, 2.5),
    Station("MIMICO", "Mimico GO", "Lakeshore West", 2, 43.6111, -79.4982, 1.0),
    Station("OAKVILLE", "Oakville GO", "Lakeshore West", 3, 43.4517, -79.6864, 1.2),
    Station("BURLINGTON", "Burlington GO", "Lakeshore West", 4, 43.3489, -79.8108, 1.0),
    Station("HAMILTON", "West Harbour GO", "Lakeshore West", 5, 43.2643, -79.8718, 0.8),
    Station("EAST_HARBOUR", "East Harbour", "Lakeshore East", 1, 43.6537, -79.3450, 1.5),
    Station("DANFORTH", "Danforth GO", "Lakeshore East", 2, 43.6797, -79.3098, 1.0),
    Station("SCARBOROUGH", "Scarborough GO", "Lakeshore East", 2, 43.7068, -79.2685, 0.9),
    Station("PICKERING", "Pickering GO", "Lakeshore East", 3, 43.8389, -79.0779, 1.0),
    Station("OSHAWA", "Oshawa GO", "Lakeshore East", 5, 43.8636, -78.8740, 0.9),
    Station("BLOOR_UP", "Bloor UP", "UP Express", 1, 43.6555, -79.4506, 1.4),
    Station("WESTON_UP", "Weston UP", "UP Express", 2, 43.7011, -79.5174, 0.8),
    Station("PEARSON_UP", "Pearson Airport UP", "UP Express", 3, 43.6810, -79.6177, 1.8),
]


class AfcTapGenerator:
    """Streaming generator that emits AFC tap events to Kafka."""

    def __init__(self, *, taps_per_second: float, seed: int, stations: list[Station], events: list[Event], producer: Producer, topic: str) -> None:
        self._rate = max(0.1, float(taps_per_second))
        self._rng = random.Random(seed)
        self._stations = stations
        self._events = events
        self._producer = producer
        self._topic = topic
        self._stop = False
        self._taps_emitted = meter.create_counter(
            "lakehouse_taps_emitted_total",
            description="Total number of synthetic AFC taps emitted.",
        )

    def stop(self, *_args: object) -> None:
        log.info("generator_stop_signal_received")
        self._stop = True

    def _build_event(self) -> dict[str, Any]:
        now = datetime.now(tz=UTC)
        hour_factor = _hourly_demand_curve(now.hour)
        station_weights: list[tuple[Station, float]] = []
        for station in self._stations:
            weight = station.base_weight * hour_factor
            for event in self._events:
                if event.applies(now, station.id):
                    weight *= event.uplift_multiplier
            station_weights.append((station, weight))

        station: Station = _weighted_pick(station_weights, self._rng)
        fare_class: str = _weighted_pick(list(_FARE_CLASS_DISTRIBUTION), self._rng)

        tap_jitter_seconds = self._rng.uniform(-30, 30)
        ts = now + timedelta(seconds=tap_jitter_seconds)

        return {
            "tap_id": str(uuid.uuid4()),
            "card_token": f"card-{self._rng.randint(1, 5_000_000):07d}",
            "station_id": station.id,
            "line": station.line,
            "zone": station.zone,
            "fare_class": fare_class,
            "fare_amount_cad": _FARE_BY_CLASS[fare_class],
            "tap_type": "TAP_ON" if self._rng.random() < 0.55 else "TAP_OFF",
            "tap_timestamp_utc": ts.isoformat(),
            "device_id": f"reader-{station.id}-{self._rng.randint(1, 4)}",
            "schema_version": "v1",
        }

    def run(self, *, duration_seconds: int | None) -> None:
        end_at = time.monotonic() + duration_seconds if duration_seconds else math.inf
        period = 1.0 / self._rate
        log.info(
            "generator_started",
            rate_taps_per_second=self._rate,
            topic=self._topic,
            stations=len(self._stations),
            events=len(self._events),
            duration_seconds=duration_seconds or "infinite",
        )
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        emitted = 0
        try:
            while not self._stop and time.monotonic() < end_at:
                with tracer.start_as_current_span("generate_tap"):
                    payload = self._build_event()
                    self._producer.produce(
                        topic=self._topic,
                        key=payload["station_id"].encode("utf-8"),
                        value=json.dumps(payload).encode("utf-8"),
                    )
                    self._taps_emitted.add(1, {"line": payload["line"], "fare_class": payload["fare_class"]})
                    emitted += 1
                    if emitted % 500 == 0:
                        self._producer.poll(0)
                        log.info("generator_progress", emitted=emitted)
                time.sleep(period)
        finally:
            self._producer.flush(timeout=10)
            log.info("generator_stopped", total_emitted=emitted)


@app.command()
def run(
    duration: int | None = typer.Option(None, help="Stop after N seconds. Default: run forever."),
    rate: float | None = typer.Option(None, help="Override taps-per-second."),
    seed: int | None = typer.Option(None, help="Override RNG seed."),
) -> None:
    """Run the synthetic AFC tap-stream generator."""
    settings = get_settings()
    configure_logging(level=settings.telemetry.log_level)
    configure_otel(settings.telemetry)

    stations = _load_stations(Path(settings.generator.station_catalog_path))
    events = _load_events(Path(settings.generator.event_calendar_path))

    producer = Producer(
        {
            "bootstrap.servers": settings.kafka.bootstrap,
            "client.id": f"{settings.kafka.client_id}-generator",
            "linger.ms": 100,
            "compression.type": "zstd",
            "enable.idempotence": True,
            "acks": "all",
        }
    )

    generator = AfcTapGenerator(
        taps_per_second=rate if rate is not None else settings.generator.taps_per_second,
        seed=seed if seed is not None else settings.generator.seed,
        stations=stations,
        events=events,
        producer=producer,
        topic=settings.kafka.topic_afc_taps,
    )
    generator.run(duration_seconds=duration if duration is not None else settings.generator.duration_seconds)


def main() -> None:
    """Console-script entry point (see ``[project.scripts]`` in pyproject.toml)."""
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()

# end of generator module
