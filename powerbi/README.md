# Power BI — transit-lakehouse

This directory holds the Power BI surface: semantic models, reports, deployment
automation, and full documentation. Every Power BI deliverable in the repo
follows the standards below.

## Layout

```
powerbi/
├── reports/                # .pbix / .pbip source files
├── model/                  # Tabular model export via Tabular Editor
│   ├── tables/
│   ├── measures/
│   └── relationships.json
├── theme.json              # custom theme
├── docs/                   # full Power BI documentation set
│   ├── datamodel.md        # star schema + DAX measure dictionary
│   ├── refresh.md          # refresh strategy, incremental refresh
│   ├── rls.md              # row-level security model + test users
│   ├── perf.md             # VertiPaq Analyzer + DAX Studio artefacts
│   └── embedding.md        # Power BI Embedded in Next.js
├── screenshots/            # one screenshot per page
└── deploy/
    ├── pipeline.json       # deployment pipeline definition
    └── pbi_deploy.py       # pbi-tools + Tabular Editor automation
```

## Reports

| Report | Audience | Purpose |
|--------|----------|---------|
| `network_overview.pbix` | Executive / SMT | System-wide ridership and revenue KPIs |
| `event_demand_uplift.pbix` | Marketing / Operations | Baseline vs event-day comparison with map overlays |
| `fare_revenue_forecast.pbix` | Finance / Revenue Strategy | Forecasts with prediction intervals + what-if sliders |

## Standards every report follows

- **Star-schema** semantic model (no flat fact tables).
- **DAX measure dictionary** in `docs/datamodel.md`.
- **Calculation groups** for time intelligence (MTD, YTD, vs prior year, vs prior period).
- **Field parameters** for dynamic measure / dimension switching.
- **Composite models** demonstrating mixed Import + DirectQuery for performance.
- **Aggregations + incremental refresh** for large fact tables.
- **Row-Level Security** with a dynamic `USERPRINCIPALNAME()` filter on the user-access dimension.
- **Object-Level Security** for sensitive fields.
- **Custom theme** and certified-visuals-only.
- **Power BI deployment pipelines** (Dev → Test → Prod) driven by `pbi-tools` and Tabular Editor in GitHub Actions.
- **Power BI REST API** automation: workspace creation, dataset refresh, pipeline deploy, tile embedding.
- **Tabular Editor 3 best-practice analyser** rules passing.
- **DAX Studio** query-plan and timing screenshots before/after performance tuning.
- **VertiPaq Analyzer** dictionary-size and column-cardinality screenshots.

## Refresh strategy

- Composite models with Import-mode aggregations for the latest 30 days; DirectQuery for the long tail.
- Incremental refresh on `fact_ridership_hourly` and `fact_fare_revenue`: 30-day rolling window, hourly trigger via Databricks job webhook calling the Power BI REST API.
- Refresh failures route to PagerDuty.

## Quickstart

```bash
# publish the report set to the configured workspace
make powerbi-publish ENV=dev

# Or directly
python deploy/pbi_deploy.py --env dev
```
 ## Refresh strategy  Incremental refresh windows: 24 months of historical + 7 days rolling. Power BI partition pruning keeps refresh times under 2 minutes.
