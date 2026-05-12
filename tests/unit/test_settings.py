"""Unit tests for src.common.settings."""

from __future__ import annotations

from src.common.settings import (
    AppSettings,
    GeneratorSettings,
    KafkaSettings,
    PostgresSettings,
    StorageSettings,
    TelemetrySettings,
    get_settings,
)


def test_app_settings_defaults_compose() -> None:
    s = AppSettings()
    assert s.environment == "local"
    assert isinstance(s.storage, StorageSettings)
    assert isinstance(s.kafka, KafkaSettings)
    assert isinstance(s.postgres, PostgresSettings)
    assert isinstance(s.telemetry, TelemetrySettings)
    assert isinstance(s.generator, GeneratorSettings)


def test_postgres_dsn_format() -> None:
    s = PostgresSettings()
    assert "postgresql://" in s.dsn
    assert "@postgres:5432" in s.dsn


def test_get_settings_is_cached() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2  # @lru_cache should return the same instance


def test_generator_network_validation() -> None:
    s = GeneratorSettings(network="nyc-mta")
    assert s.network == "nyc-mta"
    s2 = GeneratorSettings(network="calgary-ct")
    assert s2.network == "calgary-ct"


def test_kafka_topics_present() -> None:
    s = KafkaSettings()
    assert s.topic_afc_taps == "afc.taps"
    assert "gtfs.realtime" in s.topic_gtfs_rt_vehicles
