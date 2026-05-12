# End-to-end tests (Playwright)

Cross-browser end-to-end tests against the scoring API and (optionally) the Genie data-assistant UI.

## Running

```bash
cd tests/e2e/playwright
npm ci
npx playwright install --with-deps
SCORING_API_URL=http://localhost:8000 npm test
```

In CI:

- `api` project runs against the FastAPI container brought up by `docker compose up scoring-api`.
- `ui-chromium`, `ui-firefox`, `ui-webkit` projects run against the Chainlit-based Genie UI when present.
- The HTML report lands in `target/playwright-report/`.
- JUnit XML lands in `target/playwright/junit.xml` for CI test result publishing.
- Traces, videos, and screenshots are retained only on failure.

## Spec layout

```
specs/
├── api/        # FastAPI scoring service contracts
│   ├── forecast.spec.ts
│   ├── health.spec.ts
│   └── uplift-attribution.spec.ts  # included in forecast.spec.ts groups
└── ui/         # Genie chat UI and Power BI embed
    └── genie-chat.spec.ts          # added once Genie UI is deployed
```

## Fixtures

Reference station/event IDs come from `scripts/reference_data/`. The specs deliberately use **real public station IDs** (NYC MTA `R16`, Calgary `ct-7ave-1st`, etc.) so that the contract tests catch silent ID-renaming regressions in upstream feeds.

## Visual regression

UI specs that exercise the Genie chat and Power BI embed use Playwright's `toHaveScreenshot` with a 1% diff tolerance. Baselines live under `tests/e2e/playwright/__screenshots__/` and are regenerated on demand via `npx playwright test --update-snapshots`.
