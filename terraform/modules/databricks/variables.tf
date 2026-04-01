variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "env" { type = string }
variable "suffix" { type = string }
variable "public_subnet_id" { type = string }
variable "private_subnet_id" { type = string }
variable "log_analytics_workspace_id" { type = string }
variable "storage_account_id" { type = string }
variable "storage_container_name" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
