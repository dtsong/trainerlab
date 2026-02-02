# TrainerLab Terraform Outputs

output "scheduler_service_account_email" {
  description = "Email of the scheduler service account"
  value       = google_service_account.scheduler.email
}

output "scheduler_jobs" {
  description = "Created Cloud Scheduler jobs"
  value       = module.scheduler.job_names
}
