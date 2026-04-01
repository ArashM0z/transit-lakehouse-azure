output "workspace_id" {
  description = "Databricks workspace resource ID."
  value       = azurerm_databricks_workspace.main.id
}

output "workspace_url" {
  description = "Databricks workspace URL."
  value       = azurerm_databricks_workspace.main.workspace_url
}

output "cluster_policy_id" {
  description = "Cost-capped cluster policy ID."
  value       = databricks_cluster_policy.cost_capped.id
}
