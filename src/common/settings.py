"""Application configuration.

All configuration is read from environment variables (12-factor). In production
the values are sourced from Azure Key Vault via the CSI driver; in local
development they come from the .env file consumed by docker-compose.

Settings are immutable Pydantic models — passing them around is type-safe and
each component declares just the slice it depends on.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "staging", "prod"]


class StorageSettings(BaseSettings):
    """Object-storage configuration (ADLS Gen2 in prod, MinIO locally)."""

    model_config = SettingsConfigDict(env_prefix="MINIO_", env_file=".env", extra="ignore")

    endpoint: HttpUrl = Field(default=HttpUrl("http://minio:9000"))
    access_key: SecretStr = Field(default=SecretStr("minioadmin"))
    secret_key: SecretStr = Field(default=SecretStr("minioadmin"))
    bucket: str = Field(default="lakehouse")
    region: str = Field(default="us-east-1")  # immaterial for MinIO; matches Azure CC for prod


class KafkaSettings(BaseSettings):
    """Kafka / Event Hubs configuration."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env", extra="ignore")

    bootstrap: str = Field(default="redpanda:9092")
    topic_afc_taps: str = Field(default="afc.taps")
    topic_gtfs_rt_vehicles: str = Field(default="gtfs.realtime.vehicles")
    topic_gtfs_rt_trip_updates: str = Field(default="gtfs.realtime.trip_updates")
    topic_gtfs_rt_alerts: str = Field(default="gtfs.realtime.alerts")
    schema_registry_url: HttpUrl = Field(default=HttpUrl("http://redpanda:8081"))


class PostgresSettings(BaseSettings):
    """Postgres / PostGIS configuration (operational metadata + spatial)."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")

    host: str = Field(default="postgres")
    port: int = Field(default=5432)
    database: str = Field(default="lakehouse")
    user: str = Field(default="lakehouse")
    password: SecretStr = Field(default=SecretStr("lakehouse"))

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class TelemetrySettings(BaseSettings):
    """OpenTelemetry export configuration."""

    model_config = SettingsConfigDict(env_prefix="OTEL_", env_file=".env", extra="ignore")

    exporter_otlp_endpoint: HttpUrl = Field(default=HttpUrl("http://otel-collector:4317"))
    service_name: str = Field(default="transit-lakehouse")
    deployment_environment: Environment = Field(default="local")


class GeneratorSettings(BaseSettings):
    """Synthetic AFC tap generator behaviour."""

    model_config = SettingsConfigDict(env_prefix="GENERATOR_", env_file=".env", extra="ignore")

    # Which public transit network to simulate. The reference data for the chosen
    # network drives station IDs, line codes, geo coordinates, and ridership
    # priors. Adding a new network is a matter of dropping a CSV into
    # scripts/reference_data/<network>/ and adding it to the enum.
    network: Literal["nyc-mta", "calgary-ct"] = Field(default="nyc-mta")
    taps_per_minute: int = Field(default=600, ge=1, le=200_000)
    event_uplift_multiplier: float = Field(default=2.5, ge=1.0, le=10.0)
    seed: int = Field(default=20260513)


class AppSettings(BaseSettings):
    """Composite settings handed to long-lived services."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Environment = Field(default="local")
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])

    storage: StorageSettings = Field(default_factory=StorageSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    generator: GeneratorSettings = Field(default_factory=GeneratorSettings)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return process-wide settings, cached for the life of the process."""
    return AppSettings()

# end of settings module
