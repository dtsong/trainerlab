# Cloud Tasks Queue for Tournament Scraping
#
# Provides rate-limited, deduplicated task dispatch for processing
# individual tournaments discovered by the discovery endpoints.

resource "google_cloud_tasks_queue" "tournament_scrape" {
  name     = var.queue_name
  location = var.region
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = 0.5
    max_concurrent_dispatches = 2
  }

  retry_config {
    max_attempts       = 5
    min_backoff        = "30s"
    max_backoff        = "600s"
    max_doublings      = 3
    max_retry_duration = "3600s"
  }
}
