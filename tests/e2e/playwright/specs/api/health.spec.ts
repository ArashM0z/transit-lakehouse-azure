import { test, expect } from "@playwright/test";

test.describe("liveness and readiness", () => {
  test("GET /health returns 200 ok", async ({ request }) => {
    const resp = await request.get("/health");
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });

  test("GET /ready returns 200 ready", async ({ request }) => {
    const resp = await request.get("/ready");
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBe("ready");
  });

  test("OpenAPI spec is served", async ({ request }) => {
    const resp = await request.get("/openapi.json");
    expect(resp.ok()).toBeTruthy();
    const spec = await resp.json();
    expect(spec.info.title).toContain("scoring API");
    expect(spec.paths).toHaveProperty("/v1/forecast");
    expect(spec.paths).toHaveProperty("/v1/uplift-attribution");
  });
});
