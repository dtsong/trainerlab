variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
}

variable "image" {
  description = "Container image to deploy (e.g., us-central1-docker.pkg.dev/project/repo/image:tag)"
  type        = string
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "cpu" {
  description = "CPU limit (e.g., '1' or '2')"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory limit (e.g., '512Mi' or '1Gi')"
  type        = string
  default     = "512Mi"
}

variable "env_vars" {
  description = "Environment variables (non-secret)"
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Secret environment variables from Secret Manager"
  type = map(object({
    secret_id = string
    version   = string
  }))
  default = {}
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for Direct VPC Egress (e.g., projects/PROJECT/regions/REGION/subnetworks/SUBNET)"
  type        = string
  default     = null
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to the service"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for the service (optional)"
  type        = string
  default     = ""
}

variable "depends_on_resources" {
  description = "Resources that must be created before this service"
  type        = list(any)
  default     = []
}
