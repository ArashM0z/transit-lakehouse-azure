terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

locals {
  name_prefix       = "transit-lakehouse-${var.env}"
  storage_acct_name = "stlake${var.env}${var.suffix}"
}

data "azurerm_client_config" "current" {}

# ---------------- ADLS Gen2 ----------------
resource "azurerm_storage_account" "lake" {
  name                            = local.storage_acct_name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  account_kind                    = "StorageV2"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  public_network_access_enabled   = false
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true
    delete_retention_policy { days = 30 }
    container_delete_retention_policy { days = 30 }
  }

  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices", "Logging", "Metrics"]
    virtual_network_subnet_ids = [var.subnet_id]
  }

  tags = var.tags
}

resource "azurerm_storage_container" "zones" {
  for_each              = toset(["bronze", "silver", "gold", "checkpoints", "artefacts"])
  name                  = each.value
  storage_account_id    = azurerm_storage_account.lake.id
  container_access_type = "private"
}

# Lifecycle policy — bronze immutable for 7 days, archive after 90.
resource "azurerm_storage_management_policy" "lake" {
  storage_account_id = azurerm_storage_account.lake.id

  rule {
    name    = "bronze-tiering"
    enabled = true
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["bronze/"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
        delete_after_days_since_modification_greater_than          = 730
      }
    }
  }
}

resource "azurerm_storage_account_network_rules" "default_deny" {
  storage_account_id         = azurerm_storage_account.lake.id
  default_action             = "Deny"
  bypass                     = ["AzureServices", "Logging", "Metrics"]
  virtual_network_subnet_ids = [var.subnet_id]
  depends_on                 = [azurerm_storage_account.lake]
}

# ---------------- Key Vault ----------------
resource "azurerm_key_vault" "main" {
  name                          = substr("kv${var.env}${var.suffix}", 0, 24)
  resource_group_name           = var.resource_group_name
  location                      = var.location
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = "standard"
  purge_protection_enabled      = true
  soft_delete_retention_days    = 90
  enable_rbac_authorization     = true
  public_network_access_enabled = false

  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    virtual_network_subnet_ids = [var.subnet_id]
  }

  tags = var.tags
}

# Private endpoint for the storage account (DFS sub-resource)
resource "azurerm_private_endpoint" "storage_dfs" {
  name                = "pe-${local.storage_acct_name}-dfs"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${local.storage_acct_name}-dfs"
    private_connection_resource_id = azurerm_storage_account.lake.id
    is_manual_connection           = false
    subresource_names              = ["dfs"]
  }

  tags = var.tags
}
