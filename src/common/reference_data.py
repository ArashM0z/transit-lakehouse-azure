"""Reference data loaders for the synthetic AFC tap generator.

Two networks ship with the repo:

* **nyc-mta** — a curated subset of NYC MTA subway stations (the busiest 60
  by 2024 ridership) with their lat/lon and parent line. Real station IDs from
  the GTFS schedule; ridership priors derived from the public hourly ridership
  dataset (data.ny.gov).
* **calgary-ct** — Calgary Transit's CTrain Red Line + Blue Line stations with
  real coordinates from the GTFS feed and ridership priors estimated from
  Calgary's open-data quarterly snapshots.

The generator picks a station-pair sample weighted by these priors, which
reproduces realistic origin-destination patterns without needing to ship real
disaggregated data.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

Network = Literal["nyc-mta", "calgary-ct"]

REFERENCE_ROOT = Path(__file__).resolve().parents[2] / "scripts" / "reference_data"


@dataclass(frozen=True, slots=True)
class Station:
    """A station in the reference network."""

    station_id: str
    name: str
    line: str
    latitude: float
    longitude: float
    ridership_prior: float  # 0..1 — relative likelihood of being a tap origin

    def distance_km(self, other: Station) -> float:
        """Great-circle distance in km to another station (Haversine)."""
        r_km = 6371.0
        phi1 = math.radians(self.latitude)
        phi2 = math.radians(other.latitude)
        dphi = math.radians(other.latitude - self.latitude)
        dlam = math.radians(other.longitude - self.longitude)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return 2 * r_km * math.asin(math.sqrt(a))


@dataclass(frozen=True, slots=True)
class Event:
    """A reference special-event with a venue location and time window."""

    event_id: str
    name: str
    venue_name: str
    venue_latitude: float
    venue_longitude: float
    start_iso: str
    end_iso: str
    expected_attendance: int


@lru_cache(maxsize=4)
def load_stations(network: Network) -> tuple[Station, ...]:
    """Load the station catalogue for a network. Cached for the life of the process."""
    path = REFERENCE_ROOT / network / "stations.csv"
    if not path.exists():
        # The reference data is shipped with the repo; missing it is a setup bug.
        raise FileNotFoundError(
            f"Reference data missing: {path}. Ship the CSV in scripts/reference_data/{network}/."
        )

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        stations = tuple(
            Station(
                station_id=row["station_id"],
                name=row["name"],
                line=row["line"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                ridership_prior=float(row["ridership_prior"]),
            )
            for row in reader
        )

    if not stations:
        raise ValueError(f"No stations parsed from {path}.")
    return stations


@lru_cache(maxsize=4)
def load_events(network: Network) -> tuple[Event, ...]:
    """Load the reference event catalogue (concerts, ballgames, etc.)."""
    path = REFERENCE_ROOT / network / "events.csv"
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return tuple(
            Event(
                event_id=row["event_id"],
                name=row["name"],
                venue_name=row["venue_name"],
                venue_latitude=float(row["venue_latitude"]),
                venue_longitude=float(row["venue_longitude"]),
                start_iso=row["start_iso"],
                end_iso=row["end_iso"],
                expected_attendance=int(row["expected_attendance"]),
            )
            for row in reader
        )


def nearest_station(stations: tuple[Station, ...], lat: float, lon: float) -> Station:
    """Return the station closest (great-circle) to a given coordinate."""
    pivot = Station(
        station_id="_pivot",
        name="_pivot",
        line="_pivot",
        latitude=lat,
        longitude=lon,
        ridership_prior=0.0,
    )
    return min(stations, key=pivot.distance_km)

# end of reference data module
