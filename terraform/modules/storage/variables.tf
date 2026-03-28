variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "env" { type = string }
variable "suffix" { type = string }
variable "subnet_id" {
  description = "Subnet ID for private endpoint and network ACL."
  type        = string
}
variable "tags" {
  type    = map(string)
  default = {}
}
