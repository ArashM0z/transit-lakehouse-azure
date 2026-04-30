"""FastAPI scoring stub for transit ridership forecasts.

This service is a thin, well-documented surface that the production forecasting
model would sit behind. In local dev it returns deterministic mock predictions
so downstream consumers (Power BI, the Genie assistant) can be wired up before
the model is trained.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field, field_validator

from src.common.config import get_settings
from src.common.logging import configure_logging, get_logger
from src.common.otel import configure_otel

log = get_logger(__name__)


# ---------- request / response models ----------
class ForecastRequest(BaseModel):
    station_id: str = Field(..., examples=["UNION"], min_length=1, max_length=32)
    horizon_hours: int = Field(24, ge=1, le=168)
    as_of: datetime | None = Field(None, description="Optional 'as-of' instant; defaults to now.")

    @field_validator("station_id")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper().strip()


class ForecastPoint(BaseModel):
    ts: datetime
    predicted_ridership: int = Field(..., ge=0)
    pi_lower_80: int = Field(..., ge=0)
    pi_upper_80: int = Field(..., ge=0)


class ForecastResponse(BaseModel):
    station_id: str
    horizon_hours: int
    model_version: str
    generated_at: datetime
    points: list[ForecastPoint]


# ---------- lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.telemetry.log_level)
    configure_otel(settings.telemetry)
    log.info("api_starting", service=settings.telemetry.service_name)
    yield
    log.info("api_stopping")


# ---------- app ----------
app = FastAPI(
    title="Transit ridership forecast API",
    version="0.1.0",
    description="Stub scoring service for the transit-lakehouse demand-forecasting model.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
FastAPIInstrumentor.instrument_app(app)


# ---------- endpoints ----------
@app.get("/health/live", tags=["ops"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["ops"])
async def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/forecast", response_model=ForecastResponse, tags=["forecast"])
async def forecast(request: ForecastRequest) -> ForecastResponse:
    if not request.station_id.isalnum() and "_" not in request.station_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="station_id must be alphanumeric or underscore.")
    as_of = request.as_of or datetime.now(tz=UTC)
    # Deterministic synthetic forecast so PBI / Genie reviewers always see a sensible curve
    points: list[ForecastPoint] = []
    seed = sum(ord(c) for c in request.station_id) % 100 + 25
    for h in range(request.horizon_hours):
        ts = as_of + timedelta(hours=h)
        hour_factor = 1.5 if 7 <= ts.hour <= 9 else 1.4 if 16 <= ts.hour <= 18 else 0.5 if ts.hour <= 5 else 1.0
        pred = int(seed * hour_factor * 100)
        points.append(
            ForecastPoint(
                ts=ts,
                predicted_ridership=pred,
                pi_lower_80=int(pred * 0.85),
                pi_upper_80=int(pred * 1.15),
            )
        )
    return ForecastResponse(
        station_id=request.station_id,
        horizon_hours=request.horizon_hours,
        model_version="stub-0.1.0",
        generated_at=datetime.now(tz=UTC),
        points=points,
    )


def run() -> None:
    """Entrypoint for ``scoring-api`` console script and the prod Dockerfile."""
    host = os.getenv("API_HOST", "0.0.0.0")  # noqa: S104  intended bind for container
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("src.api.main:app", host=host, port=port, log_config=None, access_log=False)


if __name__ == "__main__":
    run()

# end of api module
