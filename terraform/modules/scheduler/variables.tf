# Scheduler Module Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for scheduler jobs"
  type        = string
}

variable "cloud_run_url" {
  description = "Cloud Run service URL"
  type        = string
}

variable "scheduler_service_account" {
  description = "Service account email for OIDC authentication"
  type        = string
}

variable "timezone" {
  description = "Timezone for scheduler jobs"
  type        = string
  default     = "America/New_York"
}

variable "paused" {
  description = "Whether jobs should be created in paused state"
  type        = bool
  default     = false
}
