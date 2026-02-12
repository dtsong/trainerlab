# Cloud Scheduler Jobs for TrainerLab Pipelines
#
# Schedule Reference:
# - discover-en: 6 AM daily (discover new EN tournaments, enqueue via Cloud Tasks)
# - discover-jp: 7 AM daily (discover new JP tournaments, enqueue via Cloud Tasks)
# - compute-meta: 8 AM daily (after scraping)
# - compute-evolution: 9 AM daily (after compute-meta, AI classification + predictions)
# - sync-cards: 3 AM Sunday weekly (low traffic)
# - sync-jp-cards: 3:30 AM Sunday weekly (after sync-cards, JP card sync)
# - sync-card-mappings: 4 AM Sunday weekly (after JP sync, JP-to-EN mappings)
# - sync-events: 11 AM Monday weekly (upcoming event calendar)
# - translate-pokecabook: 9 AM MWF (Japanese content translation)
# - sync-jp-adoption: 10 AM TTS (JP card adoption rates)
# - translate-tier-lists: 10 AM Sunday (weekly tier list consolidation)
# - reprocess-archetypes: 5 AM 1st of month (fix JP archetype data drift)
# - monitor-card-reveals: every 6 hours (JP card reveal tracking)

locals {
  jobs = {
    discover-en = {
      description      = "Discover new EN tournaments and enqueue for processing"
      schedule         = "0 6 * * *" # Daily at 6 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/discover-en"
      body             = jsonencode({ dry_run = false, lookback_days = 90 })
      attempt_deadline = "120s" # Discovery is fast (<30s)
    }
    discover-jp = {
      description      = "Discover new JP tournaments and enqueue for processing"
      schedule         = "0 7 * * *" # Daily at 7 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/discover-jp"
      body             = jsonencode({ dry_run = false, lookback_days = 90, min_date = "2026-01-23" })
      attempt_deadline = "120s" # Discovery is fast (<30s)
    }
    compute-meta = {
      description      = "Compute daily meta snapshots"
      schedule         = "0 8 * * *" # Daily at 8 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/compute-meta"
      body             = jsonencode({ dry_run = false, lookback_days = 90 })
      attempt_deadline = "600s"
    }
    compute-evolution = {
      description      = "Run evolution intelligence (AI classification, predictions, articles)"
      schedule         = "0 9 * * *" # Daily at 9 AM (after compute-meta at 8 AM)
      uri              = "${var.cloud_run_url}/api/v1/pipeline/compute-evolution"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "1200s"
    }
    sync-cards = {
      description      = "Sync card data from TCGdex"
      schedule         = "0 3 * * 0" # Weekly on Sunday at 3 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/sync-cards"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "600s"
    }
    sync-jp-cards = {
      description      = "Sync Japanese card data from TCGdex"
      schedule         = "30 3 * * 0" # Weekly on Sunday at 3:30 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/sync-jp-cards"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "600s"
    }
    sync-card-mappings = {
      description      = "Sync JP-to-EN card ID mappings for archetype detection"
      schedule         = "0 4 * * 0" # Weekly on Sunday at 4 AM (after sync-cards)
      uri              = "${var.cloud_run_url}/api/v1/pipeline/sync-card-mappings"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "300s"
    }
    sync-events = {
      description      = "Sync upcoming events from RK9 and Pokemon Events"
      schedule         = "0 11 * * 1" # Weekly on Monday at 11 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/sync-events"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "300s"
    }
    translate-pokecabook = {
      description      = "Translate Japanese content from Pokecabook"
      schedule         = "0 9 * * 1,3,5" # MWF at 9 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/translate-pokecabook"
      body             = jsonencode({ dry_run = false, lookback_days = 7 })
      attempt_deadline = "600s"
    }
    sync-jp-adoption = {
      description      = "Sync JP card adoption rates from Pokecabook"
      schedule         = "0 10 * * 2,4,6" # TTS at 10 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/sync-jp-adoption"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "300s"
    }
    translate-tier-lists = {
      description      = "Translate JP tier lists from Pokecabook and Pokekameshi"
      schedule         = "0 10 * * 0" # Sunday at 10 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/translate-tier-lists"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "600s"
    }
    monitor-card-reveals = {
      description      = "Monitor JP card reveals for unreleased cards"
      schedule         = "0 */6 * * *" # Every 6 hours
      uri              = "${var.cloud_run_url}/api/v1/pipeline/monitor-card-reveals"
      body             = jsonencode({ dry_run = false })
      attempt_deadline = "300s"
    }
    reprocess-archetypes = {
      description      = "Monthly reprocess of JP archetype labels to fix data drift"
      schedule         = "0 5 1 * *" # 1st of each month at 5 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/reprocess-archetypes"
      body             = jsonencode({ dry_run = false, region = "JP", force = true, batch_size = 500 })
      attempt_deadline = "600s"
    }
    cleanup-exports = {
      description      = "Clean up expired export files from Cloud Storage"
      schedule         = "0 3 * * 0" # Weekly Sunday 3 AM
      uri              = "${var.cloud_run_url}/api/v1/pipeline/cleanup-exports"
      body             = jsonencode({ dry_run = false, max_age_hours = 24 })
      attempt_deadline = "300s"
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

  attempt_deadline = each.value.attempt_deadline
}
