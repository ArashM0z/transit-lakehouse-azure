variable "resource_group_name" {
  description = "Resource group to deploy networking into."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "env" {
  description = "Environment short name (e.g. dev, prod)."
  type        = string
}

variable "vnet_cidr" {
  description = "Address space for the virtual network."
  type        = string
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default     = {}
}
