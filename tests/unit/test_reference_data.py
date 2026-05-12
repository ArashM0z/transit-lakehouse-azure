"""Unit tests for the reference data loaders."""

from __future__ import annotations

import pytest

from src.common.reference_data import (
    Station,
    load_events,
    load_stations,
    nearest_station,
)


@pytest.mark.parametrize("network", ["nyc-mta", "calgary-ct"])
def test_load_stations_returns_non_empty(network: str) -> None:
    stations = load_stations(network)  # type: ignore[arg-type]
    assert len(stations) > 0
    assert all(isinstance(s, Station) for s in stations)


@pytest.mark.parametrize("network", ["nyc-mta", "calgary-ct"])
def test_ridership_priors_normalised(network: str) -> None:
    stations = load_stations(network)  # type: ignore[arg-type]
    total = sum(s.ridership_prior for s in stations)
    # Priors should sum close to 1.0 (allow some tail to be unaccounted-for).
    assert 0.85 <= total <= 1.05, f"priors sum {total:.3f} for {network}"


def test_distance_km_is_symmetric_and_positive() -> None:
    stations = load_stations("nyc-mta")
    a, b = stations[0], stations[1]
    assert a.distance_km(b) > 0
    assert abs(a.distance_km(b) - b.distance_km(a)) < 1e-9


def test_nearest_station_returns_closest() -> None:
    stations = load_stations("nyc-mta")
    times_sq = next(s for s in stations if "Times Sq" in s.name)
    found = nearest_station(stations, lat=times_sq.latitude, lon=times_sq.longitude)
    assert found.station_id == times_sq.station_id


def test_calgary_events_within_2026() -> None:
    events = load_events("calgary-ct")
    assert len(events) > 0
    for ev in events:
        assert ev.start_iso.startswith("2026")


def test_nyc_events_include_fifa_final() -> None:
    events = load_events("nyc-mta")
    fifa = [e for e in events if "FIFA" in e.name]
    assert len(fifa) >= 1
    assert fifa[0].venue_name == "MetLife Stadium"
