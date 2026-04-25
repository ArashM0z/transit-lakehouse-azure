# 4. Medallion (bronze / silver / gold) architecture

Date: 2026-03-26

## Status

Accepted

## Context

We need a clear zonal layout for data in the lakehouse with stable contracts between zones, so that:

- Bronze is the system of record for raw inbound data (replayable).
- Silver is conformed, deduplicated, typed, with PII tagged.
- Gold is consumer-ready: dimensional, aggregated, joined.

The team's downstream consumers (Power BI, scoring API, Genie data assistant) all sit at the gold layer; everything below is implementation detail.

## Decision

Adopt Databricks' medallion architecture verbatim with the following operationalisation:

- **Bronze** — Auto Loader files-as-they-arrive ingestion. Schema evolution allowed; everything is captured even if downstream can't yet handle it. Immutable; lifecycle to cool then archive at 30 / 180 days.
- **Silver** — Delta Live Tables (DLT) with declarative quality expectations. Failures route to a quarantine path; the pipeline never silently drops rows. Conforms event time, dedupes by natural key, tags PII columns via Unity Catalog.
- **Gold** — dbt-databricks. Star-schema fact + dim marts. Tests are mandatory; freshness is monitored.

The marts:

- `fact_ridership_hourly` — station × hour.
- `fact_fare_revenue` — station × hour × fare_class.
- `mart_event_demand_uplift` — event × station × hour.
- `mart_station_kpis` — station × day, for the Power BI executive view.
- `mart_line_performance` — line × day.
- `mart_station_catchment` — spatial: each station's catchment polygon and rider-population estimate.
- `mart_equity_access` — spatial: service-area equity scoring against census-tract income/age/mobility.

## Consequences

- Three distinct teams or stages can work concurrently against stable interfaces.
- Disaster recovery is straightforward: re-derive silver and gold from bronze.
- Storage cost is approximately 1.6× single-copy; lifecycle policies bring effective cost close to 1.05× over 12 months.
- Adding a new mart never requires changing silver — silver is the contract.
 ## References  - Transport for NSW Operational Data Lake (Azure Databricks + Power BI + medallion) - MTA New York Data and Analytics blog series
