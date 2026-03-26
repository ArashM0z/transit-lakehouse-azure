output "vnet_id" {
  description = "Virtual network ID."
  value       = azurerm_virtual_network.main.id
}

output "databricks_public_subnet_id" {
  description = "Public subnet ID for the Databricks workspace."
  value       = azurerm_subnet.databricks_public.id
}

output "databricks_private_subnet_id" {
  description = "Private subnet ID for the Databricks workspace."
  value       = azurerm_subnet.databricks_private.id
}

output "endpoints_subnet_id" {
  description = "Subnet ID for private endpoints (storage, key vault)."
  value       = azurerm_subnet.endpoints.id
}
