"""Shared pytest fixtures and configuration."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _local_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Pin a local-development environment unless overridden by the test."""
    monkeypatch.setenv("ENV", "local")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    monkeypatch.setenv("KAFKA_BOOTSTRAP", os.environ.get("KAFKA_BOOTSTRAP", "localhost:19092"))
    yield


@pytest.fixture
def sample_tap() -> dict[str, object]:
    return {
        "tap_id": "00000000-0000-0000-0000-000000000001",
        "card_token": "card-0000001",
        "station_id": "UNION",
        "line": "Lakeshore West",
        "zone": 1,
        "fare_class": "ADULT",
        "fare_amount_cad": 6.05,
        "tap_type": "TAP_ON",
        "tap_timestamp_utc": "2026-06-12T20:15:00+00:00",
        "device_id": "reader-UNION-1",
        "schema_version": "v1",
    }
