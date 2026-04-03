output "resource_group_name" {
  description = "Resource group containing all environment resources."
  value       = azurerm_resource_group.main.name
}

output "databricks_workspace_url" {
  description = "URL of the Azure Databricks workspace."
  value       = module.databricks.workspace_url
}

output "storage_account_name" {
  description = "Primary ADLS Gen2 storage account."
  value       = module.storage.storage_account_name
}

output "key_vault_uri" {
  description = "Key Vault URI for secret retrieval."
  value       = module.storage.key_vault_uri
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for observability."
  value       = module.monitoring.log_analytics_workspace_id
}
