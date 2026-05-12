import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the end-to-end stack:
 *   - FastAPI scoring service at http://localhost:8000
 *   - Power BI public dashboard (proxied via Caddy at http://localhost:8090)
 *   - Genie data-assistant Chainlit UI at http://localhost:8500
 *
 * Tests must be deterministic: no real-time clock dependencies, no random
 * sampling without a fixed seed. Fixtures are managed via `tests/e2e/fixtures/`.
 */

export default defineConfig({
  testDir: "./specs",
  outputDir: "../../../target/playwright",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
    toHaveScreenshot: { maxDiffPixelRatio: 0.01 },
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "../../../target/playwright-report", open: "never" }],
    ["junit", { outputFile: "../../../target/playwright/junit.xml" }],
    ["@playwright/test/reporter"],
  ],
  use: {
    baseURL: process.env.SCORING_API_URL ?? "http://localhost:8000",
    trace: "retain-on-failure",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
    ignoreHTTPSErrors: true,
    extraHTTPHeaders: {
      "User-Agent": "tlh-e2e/0.1 (+playwright)",
    },
  },
  projects: [
    {
      name: "api",
      testMatch: /api\/.*\.spec\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "ui-chromium",
      testMatch: /ui\/.*\.spec\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "ui-firefox",
      testMatch: /ui\/.*\.spec\.ts$/,
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "ui-webkit",
      testMatch: /ui\/.*\.spec\.ts$/,
      use: { ...devices["Desktop Safari"] },
    },
  ],
  webServer: process.env.SKIP_WEB_SERVER
    ? undefined
    : {
        command: "docker compose up scoring-api",
        url: "http://localhost:8000/health",
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});

// end of playwright config
