import { test, expect } from "@playwright/test";

const nycStationIds = ["R16", "631", "A27", "127", "R20"];
const calgaryStationIds = ["ct-7ave-1st", "ct-city-hall", "ct-chinook"];

test.describe("POST /v1/forecast", () => {
  test("returns a deterministic shape for NYC stations", async ({ request }) => {
    const resp = await request.post("/v1/forecast", {
      data: {
        network: "nyc-mta",
        station_ids: nycStationIds,
        forecast_start_iso: "2026-06-12T18:00:00+00:00",
        horizon_hours: 6,
        include_event_uplift: true,
      },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.model_version).toMatch(/^event-uplift-/);
    expect(body.backtest_event_day_mape).toBeLessThan(15);
    expect(Array.isArray(body.points)).toBeTruthy();
    expect(body.points.length).toBe(nycStationIds.length);
    for (const p of body.points) {
      expect(p.expected_taps).toBeGreaterThan(0);
      expect(p.pi_lower_80).toBeLessThanOrEqual(p.expected_taps);
      expect(p.pi_upper_80).toBeGreaterThanOrEqual(p.expected_taps);
      expect(p.drivers).toHaveProperty("baseline");
    }
  });

  test("accepts Calgary CTrain stations", async ({ request }) => {
    const resp = await request.post("/v1/forecast", {
      data: {
        network: "calgary-ct",
        station_ids: calgaryStationIds,
        forecast_start_iso: "2026-07-03T09:00:00+00:00",
        horizon_hours: 4,
        include_event_uplift: true,
      },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.points.length).toBe(calgaryStationIds.length);
  });

  test("rejects an empty station list", async ({ request }) => {
    const resp = await request.post("/v1/forecast", {
      data: {
        network: "nyc-mta",
        station_ids: [],
        forecast_start_iso: "2026-06-12T18:00:00+00:00",
      },
    });
    // Pydantic catches it before the handler — 422.
    expect([400, 422]).toContain(resp.status());
  });

  test("rejects an invalid horizon", async ({ request }) => {
    const resp = await request.post("/v1/forecast", {
      data: {
        network: "nyc-mta",
        station_ids: nycStationIds,
        forecast_start_iso: "2026-06-12T18:00:00+00:00",
        horizon_hours: 9999,
      },
    });
    expect(resp.status()).toBe(422);
  });
});

test.describe("POST /v1/uplift-attribution", () => {
  test("returns synthetic-control attribution for an NYC event", async ({ request }) => {
    const resp = await request.post("/v1/uplift-attribution", {
      data: {
        network: "nyc-mta",
        event_id: "yankees-home-2026-04-10",
        observed_window_start_iso: "2026-04-10T17:00:00+00:00",
        observed_window_end_iso: "2026-04-10T23:00:00+00:00",
      },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.method).toBe("synthetic_control");
    expect(body.uplift_ratio).toBeGreaterThan(1.0);
    expect(body.confidence_95.length).toBe(2);
    expect(body.confidence_95[0]).toBeLessThan(body.confidence_95[1]);
  });
});
