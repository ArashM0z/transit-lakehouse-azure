# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Releases are produced automatically by [semantic-release](https://semantic-release.gitbook.io/).

## [Unreleased]

### Added
- Initial repository scaffold with the production baseline (Docker, Terraform, CI/CD, dbt, Power BI structure, observability).
- Medallion-architecture lakehouse: bronze (Auto Loader), silver (Delta Live Tables), gold (dbt-databricks).
- Synthetic AFC fare-tap stream generator and bronze ingestion runner.
- Azure Databricks workspace, ADLS Gen2 storage, networking, Key Vault, and Azure Monitor Terraform modules.
- Local-development docker-compose stack (Postgres, MinIO, Redpanda, MLflow, Grafana, Prometheus, OpenTelemetry).
- dbt project with bronze passthroughs, silver conformance, and the first three gold marts (`fact_ridership_hourly`, `fact_fare_revenue`, `mart_event_demand_uplift`).
- GitHub Actions CI: lint → typecheck → unit + integration tests → terraform plan → security scans → image build + sign.
- C4 architecture diagrams, alert runbook, and data contracts per zone boundary.
 ## Notes  Unreleased work is grouped under the `[Unreleased]` heading. Each merged PR appends a single bullet.

<!-- changelog notes -->
