"""Unit tests for the synthetic AFC tap-stream generator."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.ingestion.afc_tap_generator import (
    _DEFAULT_STATIONS,
    _FARE_BY_CLASS,
    _FARE_CLASS_DISTRIBUTION,
    _hourly_demand_curve,
    Event,
)


def test_hourly_demand_curve_has_peaks_at_8_and_17() -> None:
    by_hour = [_hourly_demand_curve(h) for h in range(24)]
    assert by_hour.index(max(by_hour)) in (8, 17)
    # The trough should be in the small hours
    assert by_hour.index(min(by_hour)) in (2, 3, 4)


@pytest.mark.parametrize("hour", list(range(24)))
def test_demand_curve_is_strictly_positive(hour: int) -> None:
    assert _hourly_demand_curve(hour) > 0


def test_fare_class_distribution_sums_to_one() -> None:
    total = sum(weight for _, weight in _FARE_CLASS_DISTRIBUTION)
    assert total == pytest.approx(1.0, rel=1e-9)


def test_fare_by_class_covers_every_class() -> None:
    classes = {c for c, _ in _FARE_CLASS_DISTRIBUTION}
    assert classes == set(_FARE_BY_CLASS)


def test_default_stations_have_unique_ids() -> None:
    ids = [s.id for s in _DEFAULT_STATIONS]
    assert len(ids) == len(set(ids))


def test_event_applies() -> None:
    event = Event(
        name="test",
        start=datetime(2026, 6, 12, 20, 0, tzinfo=UTC),
        end=datetime(2026, 6, 13, 1, 0, tzinfo=UTC),
        station_ids=("UNION", "EXHIBITION"),
        uplift_multiplier=4.0,
    )
    assert event.applies(datetime(2026, 6, 12, 21, 0, tzinfo=UTC), "UNION")
    assert not event.applies(datetime(2026, 6, 12, 21, 0, tzinfo=UTC), "OSHAWA")
    assert not event.applies(datetime(2026, 6, 11, 21, 0, tzinfo=UTC), "UNION")
