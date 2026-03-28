output "storage_account_id" {
  description = "ADLS Gen2 account resource ID."
  value       = azurerm_storage_account.lake.id
}

output "storage_account_name" {
  description = "ADLS Gen2 account name."
  value       = azurerm_storage_account.lake.name
}

output "containers" {
  description = "Map of zone -> container name."
  value       = { for k, v in azurerm_storage_container.zones : k => v.name }
}

output "key_vault_id" {
  description = "Key Vault resource ID."
  value       = azurerm_key_vault.main.id
}

output "key_vault_uri" {
  description = "Key Vault URI for secret retrieval."
  value       = azurerm_key_vault.main.vault_uri
}
