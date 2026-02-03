# Cloud Scheduler Jobs for TrainerLab Pipelines
#
# Schedule Reference:
# - scrape-en: 6 AM daily (after tournaments complete)
# - scrape-jp: 7 AM daily (after JP tournaments)
# - compute-meta: 8 AM daily (after scraping)
# - sync-cards: 3 AM Sunday weekly (low traffic)

locals {
  jobs = {
    scrape-en = {
      description = "Scrape English (international) tournaments from Limitless"
      schedule    = "0 6 * * *" # Daily at 6 AM
      uri         = "${var.cloud_run_url}/api/v1/pipeline/scrape-en"
      body        = jsonencode({ dry_run = false, lookback_days = 90 })
    }
    scrape-jp = {
      description = "Scrape Japanese tournaments from Limitless"
      schedule    = "0 7 * * *" # Daily at 7 AM
      uri         = "${var.cloud_run_url}/api/v1/pipeline/scrape-jp"
      body        = jsonencode({ dry_run = false, lookback_days = 90 })
    }
    compute-meta = {
      description = "Compute daily meta snapshots"
      schedule    = "0 8 * * *" # Daily at 8 AM
      uri         = "${var.cloud_run_url}/api/v1/pipeline/compute-meta"
      body        = jsonencode({ dry_run = false, lookback_days = 90 })
    }
    sync-cards = {
      description = "Sync card data from TCGdex"
      schedule    = "0 3 * * 0" # Weekly on Sunday at 3 AM
      uri         = "${var.cloud_run_url}/api/v1/pipeline/sync-cards"
      body        = jsonencode({ dry_run = false })
    }
  }
}

resource "google_cloud_scheduler_job" "pipeline" {
  for_each = local.jobs

  name        = "trainerlab-${each.key}"
  description = each.value.description
  project     = var.project_id
  region      = var.region
  schedule    = each.value.schedule
  time_zone   = var.timezone
  paused      = var.paused

  retry_config {
    retry_count          = 1
    min_backoff_duration = "30s"
    max_backoff_duration = "300s"
    max_retry_duration   = "600s"
    max_doublings        = 1
  }

  http_target {
    http_method = "POST"
    uri         = each.value.uri
    body        = base64encode(each.value.body)

    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = var.scheduler_service_account
      audience              = var.cloud_run_url
    }
  }

  # Give scrape jobs enough time to complete instead of retrying
  attempt_deadline = "600s"
}
