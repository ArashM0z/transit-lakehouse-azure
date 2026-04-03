terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.4" # AzureRM 4.x for managed-identity native CMK
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

provider "azuread" {}

# The Databricks provider is configured against the workspace once the workspace
# module has produced its URL. See `databricks.tf` for the workspace-scoped provider.
provider "databricks" {
  alias                       = "account"
  host                        = "https://accounts.azuredatabricks.net"
  azure_workspace_resource_id = module.databricks.workspace_resource_id
}

# end of providers
