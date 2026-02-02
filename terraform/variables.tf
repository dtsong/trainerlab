# TrainerLab Terraform Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "trainerlab-prod"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-west1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# =============================================================================
# Cloud Run
# =============================================================================

variable "api_image" {
  description = "Docker image for the API. Defaults to 'latest' tag. CI/CD overrides this with commit SHA or digest."
  type        = string
  default     = "" # Will be computed from project_id and region if not provided
}

variable "custom_domain" {
  description = "Custom domain for the API (optional)"
  type        = string
  default     = ""
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "https://trainerlab.app,https://www.trainerlab.app"
}

# =============================================================================
# Cloud SQL
# =============================================================================

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 10
}

# =============================================================================
# External Services
# =============================================================================

variable "redis_url" {
  description = "Redis connection URL (Memorystore or external)"
  type        = string
  default     = ""
}

variable "tcgdex_url" {
  description = "TCGdex API URL (v2 endpoint)"
  type        = string
  default     = "https://api.tcgdex.net/v2"
}

# =============================================================================
# Cloud Scheduler
# =============================================================================

variable "timezone" {
  description = "Timezone for scheduler jobs (IANA format)"
  type        = string
  default     = "America/New_York"
}

variable "scheduler_paused" {
  description = "Whether scheduler jobs should be paused"
  type        = bool
  default     = false
}

# =============================================================================
# GitHub Actions
# =============================================================================

variable "github_repo" {
  description = "GitHub repository in format owner/repo for OIDC authentication"
  type        = string
  default     = "danielsongdev/trainerlab"
}

# =============================================================================
# Operations
# =============================================================================

variable "operations_admins" {
  description = "List of user emails allowed to impersonate the operations service account for manual testing"
  type        = list(string)
  default     = []

  # Usage: Set in terraform.tfvars or via -var flag
  # Example: operations_admins = ["user@example.com", "admin@example.com"]
}
