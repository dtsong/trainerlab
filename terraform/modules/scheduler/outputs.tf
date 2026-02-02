# Scheduler Module Outputs

output "job_names" {
  description = "Names of created scheduler jobs"
  value       = [for job in google_cloud_scheduler_job.pipeline : job.name]
}

output "job_schedules" {
  description = "Schedule expressions for each job"
  value = {
    for key, job in google_cloud_scheduler_job.pipeline : key => job.schedule
  }
}
