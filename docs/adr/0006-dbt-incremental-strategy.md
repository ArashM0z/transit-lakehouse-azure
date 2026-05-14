# 6. dbt incremental strategy for fact tables

Date: 2026-05-13

## Status

Accepted

## Context

`fact_ridership_hourly` aggregates ~30M tap events per day into ~10K rows per day at hour grain. The Power BI station-overview page expects fresh data within 15 minutes during the operational window.

Three dbt-databricks incremental strategies were considered:

- `merge` — upsert semantics, handles late-arriving silver records, more compute.
- `append` — cheaper writes, but late arrivals produce duplicates.
- `insert_overwrite` — replaces affected partitions, fast on partition-pruned data.

## Decision

Use `insert_overwrite` with `partition_by=service_date`.

Drivers:

- Silver guarantees AFC events are partitioned by `event_date` with at most a 2-hour late watermark.
- The 7-day trailing window in the model body matches the late-arrival watermark with margin.
- `insert_overwrite` on a partition-pruned write is roughly 3x faster than `merge` on this volume on the dev gold layer.

## Consequences

- Late-arriving records older than 7 days are dropped on the floor (rare in practice — silver enforces the 2-hour watermark).
- A daily reconciliation job runs `dbt build --full-refresh --select fact_ridership_hourly` at 03:00 America/Toronto to fix any drift.
- The same pattern is applied to `fact_fare_revenue` and `mart_station_kpis`.

## See also

- [[adr-0004]] — medallion architecture
