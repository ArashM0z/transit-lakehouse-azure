# Remote state in an Azure Storage Account.
# Pass the backend configuration via `terraform init -backend-config=...` or env vars.
# The storage account itself is bootstrapped manually (chicken-and-egg) — see
# scripts/bootstrap-tf-state.sh.

terraform {
  required_version = ">= 1.7.0"

  backend "azurerm" {
    # set by `terraform init -backend-config` so we can target dev / prod cleanly
    resource_group_name  = "tfstate"
    storage_account_name = "tfstatemetrolinxportfolio"
    container_name       = "tlh-state"
    use_azuread_auth     = true
  }
}
