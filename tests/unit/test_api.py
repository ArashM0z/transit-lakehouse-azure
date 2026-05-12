"""Unit tests for the FastAPI scoring stub."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app


def test_liveness() -> None:
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness() -> None:
    client = TestClient(app)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_forecast_returns_horizon_points() -> None:
    client = TestClient(app)
    response = client.post("/v1/forecast", json={"station_id": "union", "horizon_hours": 24})
    assert response.status_code == 200
    payload = response.json()
    assert payload["station_id"] == "UNION"
    assert payload["horizon_hours"] == 24
    assert len(payload["points"]) == 24
    point = payload["points"][0]
    assert point["pi_lower_80"] <= point["predicted_ridership"] <= point["pi_upper_80"]


def test_forecast_validates_horizon_bounds() -> None:
    client = TestClient(app)
    response = client.post("/v1/forecast", json={"station_id": "UNION", "horizon_hours": 0})
    assert response.status_code == 422
    response = client.post("/v1/forecast", json={"station_id": "UNION", "horizon_hours": 999})
    assert response.status_code == 422
