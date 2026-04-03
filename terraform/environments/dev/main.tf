terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.59"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "azurerm" {
    resource_group_name  = "transit-lakehouse-tfstate"
    storage_account_name = "tlhtfstate"
    container_name       = "tfstate"
    key                  = "transit-lakehouse-dev.tfstate"
    use_oidc             = true
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

provider "databricks" {
  host = module.databricks.workspace_url
}

locals {
  env  = "dev"
  tags = {
    project     = "transit-lakehouse"
    environment = local.env
    owner       = "arash.mozhdehi"
    managed_by  = "terraform"
    cost_center = "portfolio"
  }
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_resource_group" "main" {
  name     = "rg-transit-lakehouse-${local.env}-${random_string.suffix.result}"
  location = var.location
  tags     = local.tags
}

module "networking" {
  source = "../../modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  env                 = local.env
  vnet_cidr           = "10.20.0.0/16"
  tags                = local.tags
}

module "storage" {
  source = "../../modules/storage"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  env                 = local.env
  suffix              = random_string.suffix.result
  subnet_id           = module.networking.endpoints_subnet_id
  tags                = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  env                 = local.env
  suffix              = random_string.suffix.result
  tags                = local.tags
}

module "databricks" {
  source = "../../modules/databricks"

  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  env                        = local.env
  suffix                     = random_string.suffix.result
  public_subnet_id           = module.networking.databricks_public_subnet_id
  private_subnet_id          = module.networking.databricks_private_subnet_id
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
  storage_account_id         = module.storage.storage_account_id
  storage_container_name     = module.storage.containers["bronze"]
  tags                       = local.tags
}
