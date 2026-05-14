# 5. Power BI as the BI consumption layer

Date: 2026-05-13

## Status

Accepted

## Context

The gold layer in Databricks SQL needs a BI surface for two distinct audiences:

1. Marketing analysts who write ad-hoc queries and want a fast canvas for exploration.
2. Senior leadership who consume a small number of governed reports with KPIs, prediction intervals, and event-day overlays.

Candidate platforms considered: Power BI Service, Tableau Cloud, Looker, Apache Superset, Metabase.

## Decision

Power BI Service is the primary BI consumer.

Drivers:

- First-class Databricks SQL connector with predictable DirectQuery semantics and Entra ID credential pass-through.
- Semantic model with RLS and OLS as native tabular constructs. Star-schema gold marts map cleanly to a semantic model the analytics team can hand-edit.
- Deployment pipelines (Dev / Test / Prod) integrate with the same CI/CD discipline Terraform and Databricks Asset Bundles already use.
- Power BI Embedded available for downstream Next.js / React surfaces without re-implementing the visual layer.

Drivers against the alternatives:

- Tableau Cloud — the Databricks connector lags Power BI on DirectQuery composite models, calculation groups, and field parameters. Pricing less predictable for a growing analyst seat count.
- Looker — LookML cost ceiling for a small team; Databricks integration relies on a separate persistent connection layer.
- Superset / Metabase — fine for a smaller surface, but no comparable story for governed delivery to a non-technical executive audience.

## Consequences

- The semantic model lives in `powerbi/model/` as exported tabular metadata, versioned alongside the dbt-managed gold marts. Drift fails CI.
- A separate Power BI Embedded surface is available for any future customer-facing analytics product.
- DirectQuery is the default; import mode is used only for the executive KPI pack where freshness tolerates hourly refresh.
- We deliberately do not adopt Microsoft Fabric in the same step (see ADR-0002).

## See also

- [[adr-0002]] — Azure Databricks + Unity Catalog
- [[adr-0004]] — medallion architecture
