# TrainerLab Terraform Outputs

output "api_url" {
  description = "Cloud Run API service URL"
  value       = module.api.service_url
}

output "api_service_name" {
  description = "Cloud Run API service name"
  value       = module.api.service_name
}

output "api_image" {
  description = "Docker image used for the API"
  value       = local.api_image_uri
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.database.instance_name
}

output "database_connection_name" {
  description = "Cloud SQL connection name for Cloud Run"
  value       = module.database.instance_connection_name
}

output "artifact_registry_url" {
  description = "Artifact Registry URL for Docker images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.api.repository_id}"
}

output "scheduler_service_account_email" {
  description = "Email of the scheduler service account"
  value       = google_service_account.scheduler.email
}

output "operations_service_account_email" {
  description = "Email of the operations service account (for manual testing)"
  value       = google_service_account.operations.email
}

output "scheduler_jobs" {
  description = "Created Cloud Scheduler jobs"
  value       = module.scheduler.job_names
}

output "project_number" {
  description = "GCP project number (needed for GitHub Actions OIDC)"
  value       = data.google_project.current.number
}
