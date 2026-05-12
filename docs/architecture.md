# Architecture

This document captures the system at three levels of detail using the
[C4 model](https://c4model.com/): **system context**, **container**, and
**component**.

## 1. System context

```mermaid
C4Context
    title transit-lakehouse — system context

    Person(analyst, "Analyst / Data Scientist", "Explores ridership, designs forecasts, builds reports")
    Person(stakeholder, "Marketing / Operations stakeholder", "Consumes Power BI reports, asks Genie questions")

    System(lakehouse, "transit-lakehouse", "Azure Databricks lakehouse with Power BI consumer")

    System_Ext(presto, "PRESTO AFC", "Fare-tap events")
    System_Ext(gtfs, "GTFS-Realtime feed", "Vehicle positions, trip updates, alerts")
    System_Ext(eventcal, "Event calendar", "Sports, concerts, scheduled service changes")
    System_Ext(weather, "Environment Canada", "Weather observations for feature enrichment")

    System_Ext(pbiservice, "Power BI Service", "Reports + Embedded for downstream consumption")
    System_Ext(azureml, "Azure ML", "Hosted forecast model endpoints")

    Rel(presto, lakehouse, "tap events", "Event Hubs (Kafka)")
    Rel(gtfs, lakehouse, "vehicle positions, trips", "HTTPS / Protobuf")
    Rel(eventcal, lakehouse, "event metadata", "REST / JSON")
    Rel(weather, lakehouse, "weather observations", "REST / JSON")

    Rel(lakehouse, pbiservice, "publishes datasets and reports")
    Rel(lakehouse, azureml, "publishes feature tables and consumes inference results")

    Rel(analyst, lakehouse, "Notebooks, SQL, dbt")
    Rel(stakeholder, pbiservice, "Power BI reports + AI/BI Genie")
```

## 2. Containers

```mermaid
C4Container
    title transit-lakehouse — containers
    Container(eh, "Azure Event Hubs", "Managed Kafka", "Streaming AFC and GTFS-RT ingress")
    ContainerDb(adls, "ADLS Gen2", "Storage", "bronze / silver / gold / checkpoints zones")
    Container(dbw, "Azure Databricks Workspace", "Spark + Photon", "Auto Loader, DLT, Workflows, Unity Catalog")
    Container(uc, "Unity Catalog", "Governance", "Privileges, lineage, RLS, audit")
    Container(dbtsql, "Databricks SQL Warehouse", "Serverless SQL", "Power BI DirectQuery target")
    Container(dbt, "dbt-databricks", "Transform", "Silver → gold marts")
    Container(api, "Forecast API", "FastAPI", "Stub scoring service")
    Container(pbi, "Power BI Service", "BI", "Reports + deployment pipelines + RLS")
    Container(otel, "OpenTelemetry + Azure Monitor", "Observability", "Traces, metrics, logs")
    Container(kv, "Azure Key Vault", "Secrets")

    Rel(eh, dbw, "stream")
    Rel(dbw, adls, "writes Delta")
    Rel(dbw, uc, "registers tables and privileges")
    Rel(dbt, dbtsql, "runs SQL transformations")
    Rel(dbtsql, adls, "reads Delta")
    Rel(pbi, dbtsql, "DirectQuery")
    Rel(api, dbtsql, "reads gold")
    Rel(dbw, otel, "exports traces and metrics")
    Rel(api, otel, "exports traces and metrics")
    Rel(dbw, kv, "retrieves secrets")
    Rel(api, kv, "retrieves secrets")
```

## 3. Components (FastAPI scoring service)

```mermaid
C4Component
    title Forecast API — components
    Container_Boundary(api, "Forecast API (FastAPI)") {
        Component(router, "Router", "FastAPI", "/health, /v1/forecast")
        Component(svc, "Forecast service", "Python", "Calls the registered model")
        Component(model, "Model client", "MLflow / Azure ML", "Pulls champion model")
        Component(otelc, "Telemetry client", "OpenTelemetry", "Spans, metrics, events")
        Component(cfg, "Config", "Pydantic Settings", "Typed runtime configuration")
    }
    Rel(router, svc, "calls")
    Rel(svc, model, "infers")
    Rel(router, otelc, "instruments")
    Rel(svc, otelc, "instruments")
    Rel(model, otelc, "instruments")
```

## 4. Data flow

```mermaid
sequenceDiagram
    participant Source as PRESTO / GTFS-RT
    participant EH as Event Hubs
    participant AL as Auto Loader
    participant Bronze as ADLS bronze
    participant DLT as Delta Live Tables
    participant Silver as ADLS silver
    participant DBT as dbt-databricks
    participant Gold as ADLS gold
    participant SQL as Databricks SQL
    participant PBI as Power BI Service
    Source->>EH: AFC tap / GTFS-RT
    EH->>AL: stream
    AL->>Bronze: Delta append
    Bronze->>DLT: stream
    DLT->>Silver: conformed Delta
    Silver->>DBT: SQL
    DBT->>Gold: marts (table)
    Gold->>SQL: query
    SQL->>PBI: DirectQuery
```

## 5. Cross-cutting concerns

| Concern | How it's addressed |
|---------|--------------------|
| Identity | Workload Identity / Managed Identity for compute; Azure AD groups for analyst access |
| Secrets | Azure Key Vault + Databricks secret scopes |
| Encryption at rest | ADLS Gen2 SSE with customer-managed keys |
| Encryption in transit | TLS 1.3; mTLS between in-cluster services |
| Lineage | Unity Catalog + dbt-generated graph in `dbt docs` |
| Audit | Unity Catalog audit + Azure Monitor diagnostic settings |
| RLS | Dynamic view masking on PII columns; row-level filters bound to `current_user()` |
| SLOs | Bronze < 5 min, Silver < 15 min, Gold < 1 h; Power BI < 3 s query p95 |

## 6. Architectural decisions

ADRs live in [`docs/adr/`](adr/) using a lightweight Markdown template. Open a
PR adding `0NNN-short-title.md` for any new decision.
