# 2. Azure Databricks with Unity Catalog

Date: 2026-03-19

## Status

Accepted

## Context

We need a lakehouse compute and governance layer that:

1. Lives on Azure (the Crown-agency and comparable public-sector default in Canada and a stated direction at peer transit agencies).
2. Runs PySpark workloads efficiently on terabyte-scale ridership data.
3. Provides table-level governance, fine-grained ACLs, row filters, and column masks for PII in fare-tap streams.
4. Supports a natural-language analytics surface ("Genie-style") for non-technical Marketing stakeholders.

Candidates considered:

- **Azure Databricks + Unity Catalog**.
- **Microsoft Fabric** (OneLake + Direct Lake).
- **Azure Synapse Analytics**.
- **Snowflake on Azure**.

## Decision

Azure Databricks with Unity Catalog as the metastore. Workloads land in ADLS Gen2 as Delta Lake tables across the bronze / silver / gold zones.

### Why

- Unity Catalog is the only option in this list that gives us **row filters and column masks as first-class governance primitives** — a hard requirement for PII in fare-tap data.
- The Spark runtime is consistent with the open-source PySpark stack the team already knows; no proprietary SQL dialect lock-in.
- **Databricks AI/BI Genie** maps cleanly onto our target self-serve analytics use case and runs natively against Unity Catalog. Joshua Oh's posted direction explicitly champions this pattern.
- Customer expansion path: a parallel **Calgary Transit** or **MTA** workspace would share metastore patterns and skill — the architecture is portable across public-transit agencies.

### Why not the alternatives

- **Microsoft Fabric**: Direct Lake is excellent for Power BI integration but the governance model is less mature for row/column-level controls; we'd be early on the maturity curve.
- **Synapse**: Slower to evolve, no equivalent to AI/BI Genie, weaker open-format story than Delta Lake.
- **Snowflake**: Excellent product, but every Crown-agency procurement we benchmarked landed on Azure-native — Snowflake adds vendor surface area that is hard to justify against parity with the platform direction.

## Consequences

- We bind to Azure Databricks. Workloads are Spark — portable to other Spark runtimes (Synapse Spark, EMR, GCP Dataproc) at the cost of some Databricks-specific features (Liquid Clustering, Predictive I/O).
- **Premium SKU is required** for Unity Catalog + row filters. Trial / Standard cannot be used past the prototype stage.
- We commit to dbt-databricks for SQL transformations rather than Databricks SQL views, because dbt's testing and lineage story is stronger than Databricks-native equivalents.
- Power BI consumes via DirectQuery against the Databricks SQL warehouse — composite models offset performance penalties for high-cardinality dimensions.

## Notes
