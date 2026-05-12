"""Unit tests for the typed configuration layer."""

from __future__ import annotations

import pytest

from src.common.config import Settings, get_settings


def test_settings_defaults_work_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(monkeypatch._setenv.keys()) if hasattr(monkeypatch, "_setenv") else []:
        monkeypatch.delenv(key, raising=False)
    settings = Settings()
    assert settings.env == "local"
    assert settings.kafka.bootstrap.startswith("redpanda") or settings.kafka.bootstrap.startswith("localhost")
    assert settings.storage.bucket == "lakehouse"
    assert settings.telemetry.service_name == "transit-lakehouse"


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KAFKA_TOPIC_AFC_TAPS", "afc.taps.override")
    monkeypatch.setenv("GEN_TAPS_PER_SECOND", "999.0")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.kafka.topic_afc_taps == "afc.taps.override"
    assert settings.generator.taps_per_second == pytest.approx(999.0)


def test_postgres_url_is_well_formed() -> None:
    settings = Settings()
    assert settings.postgres.url.startswith("postgresql+psycopg://")
    assert f"@{settings.postgres.host}:{settings.postgres.port}/{settings.postgres.db}" in settings.postgres.url
