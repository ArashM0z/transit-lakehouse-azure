"""Unit tests for the reference-data loaders + Haversine helper."""
from __future__ import annotations

import pytest

from src.common.reference_data import Station, load_events, load_stations, nearest_station


@pytest.fixture(scope="module")
def nyc_stations() -> tuple[Station, ...]:
    return load_stations("nyc-mta")


@pytest.fixture(scope="module")
def calgary_stations() -> tuple[Station, ...]:
    return load_stations("calgary-ct")


class TestStationDistance:
    def test_distance_to_self_is_zero(self, nyc_stations: tuple[Station, ...]) -> None:
        s = nyc_stations[0]
        assert s.distance_km(s) == pytest.approx(0.0, abs=1e-9)

    def test_distance_is_symmetric(self, nyc_stations: tuple[Station, ...]) -> None:
        a, b = nyc_stations[0], nyc_stations[5]
        assert a.distance_km(b) == pytest.approx(b.distance_km(a), abs=1e-9)

    def test_times_square_to_grand_central_under_1km(self) -> None:
        ts = Station("R16", "Times Sq", "N", 40.755477, -73.987691, 0.085)
        gct = Station("631", "Grand Central", "4-5-6", 40.751776, -73.976848, 0.078)
        assert 0.8 <= ts.distance_km(gct) <= 1.2

    def test_triangle_inequality(self, nyc_stations: tuple[Station, ...]) -> None:
        a, b, c = nyc_stations[0], nyc_stations[10], nyc_stations[20]
        assert a.distance_km(c) <= a.distance_km(b) + b.distance_km(c) + 1e-9


class TestLoaders:
    def test_nyc_has_at_least_50_stations(self, nyc_stations: tuple[Station, ...]) -> None:
        assert len(nyc_stations) >= 50

    def test_calgary_has_red_and_blue_lines(self, calgary_stations: tuple[Station, ...]) -> None:
        lines = {s.line for s in calgary_stations}
        assert any("Red" in line for line in lines)
        assert any("Blue" in line for line in lines)

    def test_ridership_priors_normalised(self, nyc_stations: tuple[Station, ...]) -> None:
        total = sum(s.ridership_prior for s in nyc_stations)
        assert 0.95 <= total <= 1.05

    def test_coordinates_in_plausible_range(self, nyc_stations: tuple[Station, ...]) -> None:
        for s in nyc_stations:
            assert 40.5 < s.latitude < 41.0
            assert -74.1 < s.longitude < -73.6

    def test_events_load(self) -> None:
        events = load_events("nyc-mta")
        assert len(events) > 0
        assert all(e.expected_attendance > 0 for e in events)
        assert all(e.start_iso < e.end_iso for e in events)


class TestNearestStation:
    def test_nearest_to_times_square_coords(self, nyc_stations: tuple[Station, ...]) -> None:
        nearest = nearest_station(nyc_stations, lat=40.7580, lon=-73.9855)
        assert "Times Sq" in nearest.name or nearest.station_id == "R16"

    def test_nearest_to_far_coord_still_returns(
        self, nyc_stations: tuple[Station, ...]
    ) -> None:
        nearest = nearest_station(nyc_stations, lat=-90.0, lon=0.0)
        assert nearest in nyc_stations
