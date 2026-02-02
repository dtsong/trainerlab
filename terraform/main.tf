# TrainerLab Infrastructure
# Manages Cloud Scheduler jobs for data pipelines

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }

  # Remote state stored in GCS
  # Uncomment and configure when ready for production
  # backend "gcs" {
  #   bucket = "trainerlab-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Scheduler service account
resource "google_service_account" "scheduler" {
  account_id   = "trainerlab-scheduler"
  display_name = "TrainerLab Cloud Scheduler"
  description  = "Service account for Cloud Scheduler to invoke pipeline endpoints"
}

# Grant scheduler SA permission to invoke Cloud Run
resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  count    = var.cloud_run_service_name != "" ? 1 : 0
  project  = var.project_id
  location = var.region
  service  = var.cloud_run_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# Scheduler module
module "scheduler" {
  source = "./modules/scheduler"

  project_id                = var.project_id
  region                    = var.region
  cloud_run_url             = var.cloud_run_url
  scheduler_service_account = google_service_account.scheduler.email
  timezone                  = var.timezone
  paused                    = var.scheduler_paused
}
