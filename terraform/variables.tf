# TrainerLab Terraform Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "cloud_run_url" {
  description = "Cloud Run service URL for API (e.g., https://api-xyz.run.app)"
  type        = string
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name (for IAM binding)"
  type        = string
  default     = ""
}

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
