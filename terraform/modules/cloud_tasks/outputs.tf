# Cloud Tasks Module Outputs

output "queue_name" {
  description = "Name of the Cloud Tasks queue"
  value       = google_cloud_tasks_queue.tournament_scrape.name
}

output "queue_id" {
  description = "Full ID of the Cloud Tasks queue"
  value       = google_cloud_tasks_queue.tournament_scrape.id
}

output "queue_path" {
  description = "Full resource path for enqueuing tasks"
  value       = "projects/${var.project_id}/locations/${var.region}/queues/${google_cloud_tasks_queue.tournament_scrape.name}"
}
