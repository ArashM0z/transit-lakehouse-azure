variable "location" {
  description = "Azure region for all resources in this environment."
  type        = string
  default     = "canadacentral"
}

variable "subscription_id" {
  description = "Azure subscription ID. Falls back to ARM_SUBSCRIPTION_ID."
  type        = string
  default     = null
}

# end of dev variables
