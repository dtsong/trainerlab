# Cloud Tasks Module Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud Tasks queue"
  type        = string
}

variable "queue_name" {
  description = "Name of the Cloud Tasks queue"
  type        = string
  default     = "tournament-scrape"
}
