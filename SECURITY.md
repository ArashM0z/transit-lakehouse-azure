# Security

## Reporting a vulnerability

Please report security vulnerabilities by emailing `ArashM0z@users.noreply.github.com` with subject line `SECURITY: transit-lakehouse-azure`. Do not open a public GitHub issue.

You should receive an acknowledgement within 48 hours. We will work with you to understand and resolve the issue.

## Threat model summary

This repository scaffolds a transit ridership lakehouse. The threat model assumes:

- **Multi-tenant analyst access** to the gold layer via Power BI Service with row-level security.
- **Service-to-service mTLS** between containerised components.
- **No PII in non-production environments** — synthetic data only.
- **Secrets in Azure Key Vault** with managed-identity access; zero secrets in code, CI, or commits.

## Security baseline

| Control | Implementation |
|---------|----------------|
| Secret detection | `gitleaks` in pre-commit and CI |
| Container scanning | `trivy` filesystem + image scan in CI |
| Image signing | `cosign` keyless signing with GitHub OIDC; SLSA L3 provenance attestations |
| SBOM | `syft` generates CycloneDX SBOM published with each release |
| Dependency review | `dependency-review-action` on every PR; Dependabot weekly |
| IaC scanning | `tfsec` + `checkov` in pre-commit and CI |
| Python SAST | `bandit` via `ruff` rule set S |
| Cluster admission | OPA/Gatekeeper restricting non-compliant manifests |
| Network policy | Default-deny + explicit egress allowlist |
| Pod security | Restricted Pod Security admission profile |
| Image baseline | Multi-stage build; distroless final stage; non-root user |
| Identity | Workload Identity / Managed Identity — no static credentials |
| Encryption at rest | ADLS Gen2 SSE with customer-managed keys (Key Vault) |
| Encryption in transit | TLS 1.3; mTLS between services in the cluster |
| Data classification | Documented in `docs/data_contracts/*.yaml` per zone |
| Audit logging | Azure Monitor + Unity Catalog audit logs |

## Supported versions

This is a portfolio repository — the `main` branch is the only supported version. Tagged releases follow semantic versioning.

<!-- security policy revised 2026-05-12 -->
