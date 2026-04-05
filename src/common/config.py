"""Typed configuration loaded from environment variables and .env files.

All knobs the application needs to know about live here. Components import
``get_settings()`` and read fields off the returned ``Settings`` instance —
never read environment variables directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    """Kafka / Redpanda / Event Hubs configuration."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_", extra="ignore")

    bootstrap: str = Field(default="redpanda:9092", description="Comma-separated bootstrap servers.")
    topic_afc_taps: str = Field(default="afc.taps")
    topic_gtfs_rt: str = Field(default="gtfs.realtime")
    client_id: str = Field(default="transit-lakehouse")
    security_protocol: Literal["PLAINTEXT", "SASL_SSL"] = "PLAINTEXT"
    sasl_username: str | None = None
    sasl_password: SecretStr | None = None


class StorageSettings(BaseSettings):
    """ADLS Gen2 / MinIO configuration."""

    model_config = SettingsConfigDict(env_prefix="MINIO_", extra="ignore")

    endpoint: str = Field(default="http://minio:9000")
    access_key: str = Field(default="minioadmin")
    secret_key: SecretStr = Field(default=SecretStr("minioadmin"))
    bucket: str = Field(default="lakehouse")
    use_ssl: bool = False


class PostgresSettings(BaseSettings):
    """Postgres metadata store for local dev (MLflow, dbt-postgres profile)."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    host: str = "postgres"
    port: int = 5432
    db: str = "lakehouse"
    user: str = "lakehouse"
    password: SecretStr = SecretStr("lakehouse")

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class TelemetrySettings(BaseSettings):
    """OpenTelemetry exporter configuration."""

    model_config = SettingsConfigDict(env_prefix="OTEL_", extra="ignore")

    service_name: str = "transit-lakehouse"
    exporter_otlp_endpoint: str = "http://otel-collector:4317"
    exporter_otlp_protocol: Literal["grpc", "http/protobuf"] = "grpc"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class GeneratorSettings(BaseSettings):
    """Synthetic AFC tap-stream generator knobs."""

    model_config = SettingsConfigDict(env_prefix="GEN_", extra="ignore")

    taps_per_second: float = 50.0
    seed: int = 42
    duration_seconds: int | None = None  # None = run forever
    event_calendar_path: str = "scripts/event_calendar.json"
    station_catalog_path: str = "scripts/stations.json"
    line_catalog_path: str = "scripts/lines.json"


class Settings(BaseSettings):
    """Top-level settings, composed from the per-domain sub-settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["local", "dev", "prod"] = "local"
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    generator: GeneratorSettings = Field(default_factory=GeneratorSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Cached so tests can override via ``get_settings.cache_clear()`` followed by
    monkeypatching the environment.
    """
    return Settings()
