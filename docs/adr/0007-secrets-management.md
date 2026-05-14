# 7. Secrets management

Date: 2026-05-13

## Status

Accepted

## Context

Three places need credentials:

1. Databricks workspace — ADLS, Postgres metadata, Azure OpenAI.
2. AKS-deployed services — Postgres, Azure OpenAI, MLflow.
3. CI/CD pipelines — ACR / GHCR push, terraform plan / apply.

## Decision

Azure Key Vault is the single source of truth. Three retrieval paths:

- Databricks: Key Vault-backed secret scope, named `tlh-${env}`. Notebooks read with `dbutils.secrets.get`.
- AKS: Secrets Store CSI Driver with the Azure Provider. Each workload binds a SecretProviderClass that maps Key Vault secrets to env vars at pod start.
- CI/CD: GitHub OIDC -> Azure federation -> Key Vault. Zero static credentials in GitHub Secrets except the bootstrap service principal.

## Consequences

- Local development uses `.env` files (gitignored). The local `.env` never crosses an environment boundary.
- Secret rotation cadence: 90 days for high-sensitivity (CMK, database root), 365 days for low-sensitivity (read-only API tokens).
- An audit log of every secret read lives in Key Vault diagnostics, routed to Log Analytics.
- `helm/transit-lakehouse/templates/secretproviderclass.yaml` is the canonical mapping per environment.

## See also

- [[adr-0002]] — Azure Databricks + Unity Catalog
