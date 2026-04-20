# dbt — transit-lakehouse

Transformations from silver → gold marts. Bronze is landed by upstream
ingestion (Auto Loader in production; the `bronze_ingest` Python runner
locally).

## Profiles

- `dev` — local docker-compose Postgres
- `ci` — DuckDB, no external services
- `prod` — Azure Databricks SQL warehouse

## Layout

```
dbt/
├── dbt_project.yml
├── packages.yml
├── profiles/profiles.yml
├── models/
│   ├── sources.yml
│   ├── bronze/
│   │   └── bronze__afc_taps.sql          # passthrough view over the source
│   ├── silver/
│   │   └── silver__afc_taps.sql          # deduped, dimension-aware
│   ├── gold/
│   │   ├── fact_ridership_hourly.sql
│   │   ├── fact_fare_revenue.sql
│   │   ├── dim_station.sql
│   │   ├── dim_date.sql
│   │   └── schema.yml                    # tests + docs
│   └── marts/
│       ├── mart_event_demand_uplift.sql  # the FIFA-style mart
│       └── schema.yml
└── macros/
    └── generate_schema_name.sql
```

## Quickstart

```bash
make dbt-build        # build everything against the dev profile
make dbt-test         # only tests
make dbt-docs         # generate + serve docs at http://localhost:8080
```
 ## Targets  The `ci` target uses DuckDB so CI runs do not need a live Databricks workspace. `dev` and `prod` target the Databricks SQL warehouse provisioned by Terraform.
