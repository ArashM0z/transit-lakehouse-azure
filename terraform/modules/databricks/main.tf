terraform {
  required_providers {
    azurerm    = { source = "hashicorp/azurerm", version = "~> 4.14" }
    databricks = { source = "databricks/databricks", version = "~> 1.59" }
  }
}

locals {
  name_prefix = "transit-lakehouse-${var.env}"
}

resource "azurerm_databricks_workspace" "main" {
  name                          = "dbw-${local.name_prefix}-${var.suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku                           = "premium"
  managed_resource_group_name   = "rg-dbw-${local.name_prefix}-${var.suffix}-managed"
  public_network_access_enabled = true

  custom_parameters {
    virtual_network_id                                   = data.azurerm_subnet.public.virtual_network_id
    public_subnet_name                                   = data.azurerm_subnet.public.name
    private_subnet_name                                  = data.azurerm_subnet.private.name
    public_subnet_network_security_group_association_id  = "${data.azurerm_subnet.public.id}/networkSecurityGroupAssociation"
    private_subnet_network_security_group_association_id = "${data.azurerm_subnet.private.id}/networkSecurityGroupAssociation"
    no_public_ip                                         = true
    storage_account_sku_name                             = "Standard_ZRS"
  }

  tags = var.tags
}

data "azurerm_subnet" "public" {
  name                 = element(reverse(split("/", var.public_subnet_id)), 0)
  virtual_network_name = element(reverse(split("/", var.public_subnet_id)), 2)
  resource_group_name  = var.resource_group_name
}

data "azurerm_subnet" "private" {
  name                 = element(reverse(split("/", var.private_subnet_id)), 0)
  virtual_network_name = element(reverse(split("/", var.private_subnet_id)), 2)
  resource_group_name  = var.resource_group_name
}

# ---------------- Diagnostic Settings ----------------
resource "azurerm_monitor_diagnostic_setting" "dbw" {
  name                       = "diag-dbw"
  target_resource_id         = azurerm_databricks_workspace.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log { category = "dbfs" }
  enabled_log { category = "clusters" }
  enabled_log { category = "accounts" }
  enabled_log { category = "jobs" }
  enabled_log { category = "notebook" }
  enabled_log { category = "ssh" }
  enabled_log { category = "workspace" }
  enabled_log { category = "secrets" }
  enabled_log { category = "sqlPermissions" }
  enabled_log { category = "instancePools" }
  enabled_log { category = "sqlanalytics" }
  enabled_log { category = "genie" }
  enabled_log { category = "globalInitScripts" }
  enabled_log { category = "iamRole" }
  enabled_log { category = "mlflowExperiment" }
  enabled_log { category = "mlflowAcledArtifact" }
  enabled_log { category = "modelRegistry" }
  enabled_log { category = "repos" }
  enabled_log { category = "unityCatalog" }
}

# ---------------- Cluster policy ----------------
resource "databricks_cluster_policy" "cost_capped" {
  name = "cost-capped-${var.env}"

  definition = jsonencode({
    "spark_version" : { "type" : "fixed", "value" : "15.4.x-scala2.12" },
    "node_type_id" : { "type" : "fixed", "value" : "Standard_DS3_v2" },
    "autotermination_minutes" : { "type" : "range", "minValue" : 10, "maxValue" : 60, "defaultValue" : 20 },
    "num_workers" : { "type" : "range", "minValue" : 1, "maxValue" : 4, "defaultValue" : 2 },
    "custom_tags.cost_center" : { "type" : "fixed", "value" : "portfolio" },
  })
}

# end of databricks module
