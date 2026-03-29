terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.14" }
  }
}

locals {
  name_prefix = "transit-lakehouse-${var.env}"
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.name_prefix}-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${local.name_prefix}-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  application_type    = "other"
  workspace_id        = azurerm_log_analytics_workspace.main.id
  tags                = var.tags
}

resource "azurerm_monitor_action_group" "ops" {
  name                = "ag-${local.name_prefix}-ops"
  resource_group_name = var.resource_group_name
  short_name          = substr("ops${var.env}", 0, 12)
  tags                = var.tags

  email_receiver {
    name          = "primary-oncall"
    email_address = "ArashM0z@users.noreply.github.com"
  }
}

# Alert: bronze ingestion lag > 10 minutes
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "bronze_lag" {
  name                 = "alert-bronze-freshness-${var.env}"
  resource_group_name  = var.resource_group_name
  location             = var.location
  evaluation_frequency = "PT5M"
  window_duration      = "PT15M"
  scopes               = [azurerm_log_analytics_workspace.main.id]
  severity             = 2
  tags                 = var.tags

  criteria {
    query                   = <<-KQL
      AppMetrics
      | where Name == "lakehouse_bronze_freshness_seconds"
      | summarize p95 = percentile(Sum / Count, 95) by bin(TimeGenerated, 5m)
      | where p95 > 600
    KQL
    operator                = "GreaterThan"
    threshold               = 0
    time_aggregation_method = "Count"
  }

  action {
    action_groups = [azurerm_monitor_action_group.ops.id]
  }
}
