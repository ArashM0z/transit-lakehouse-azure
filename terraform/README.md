# Terraform — transit-lakehouse-azure

Modular Azure footprint provisioned per environment.

```
terraform/
├── modules/
│   ├── networking/    VNet, subnets, NSGs, Databricks subnet delegations
│   ├── storage/       ADLS Gen2 (HNS), zones, Key Vault, private endpoints, lifecycle policy
│   ├── monitoring/    Log Analytics, App Insights, action group, KQL alerts
│   └── databricks/    Premium workspace (no-public-IP), diagnostic settings, cluster policy
└── environments/
    ├── dev/           dev composition (10.20.0.0/16)
    └── prod/          prod composition (10.30.0.0/16)
```

## Prerequisites

- Terraform ≥ 1.7
- Azure CLI (`az login`)
- Pre-existing remote state bucket (resource group `transit-lakehouse-tfstate`, storage account `tlhtfstate`, container `tfstate`)

## Quickstart

```bash
cd terraform/environments/dev
terraform init
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

## Notes

- Workspaces use **Premium** SKU because Unity Catalog and Genie require it.
- All subnets that host Databricks are explicitly delegated to `Microsoft.Databricks/workspaces`.
- Storage default action is **Deny** with VNet exception + private endpoint; expect a one-time public-network-disable rule from `azurerm_storage_account_network_rules`.
- Workspace deploys with `no_public_ip = true`. Reach it via Azure private link.
- Cluster policy caps autotermination ≤ 60 min and workers ≤ 4 in dev to prevent runaway cost.

## CI

The `terraform.yml` workflow runs `fmt-check`, `validate` per environment, `tfsec`, `checkov`, and `plan` on every PR. Apply happens manually from `main` after merge.
 ## VNet sizing  The default /16 leaves room for 16 /20-sized subnets per spoke, plenty for the AKS + Databricks + private-endpoints split we use.

## VNet sizing rationale
