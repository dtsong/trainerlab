# TrainerLab Infrastructure
# Cloud Run API, Cloud SQL PostgreSQL, and Cloud Scheduler pipelines

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "gcs" {
    bucket = "trainerlab-tfstate-1d22e2f5"
    prefix = "trainerlab-prod/app"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Get project details (for project number)
data "google_project" "current" {
  project_id = var.project_id
}

# =============================================================================
# Remote State - Network Resources from Foundation
# =============================================================================

data "terraform_remote_state" "foundation" {
  backend = "gcs"
  config = {
    bucket = "trainerlab-tfstate-1d22e2f5"
    prefix = "environments/trainerlab-prod"
  }
}

locals {
  # Network resources from foundation state
  network_id         = data.terraform_remote_state.foundation.outputs.network_id
  network_self_link  = data.terraform_remote_state.foundation.outputs.network_self_link
  network_name       = data.terraform_remote_state.foundation.outputs.network_name
  cloudrun_subnet_id = data.terraform_remote_state.foundation.outputs.cloudrun_subnet_id

  # Compute API image URI with fallback to latest tag
  api_image_uri = var.api_image != "" ? var.api_image : "${var.region}-docker.pkg.dev/${var.project_id}/trainerlab-api/api:latest"
}

# =============================================================================
# Enable Required APIs
# =============================================================================

resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iamcredentials.googleapis.com", # Required for Workload Identity Federation
    "cloudtasks.googleapis.com",     # Cloud Tasks for tournament scrape pipeline
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# =============================================================================
# Artifact Registry for Container Images
# =============================================================================

resource "google_artifact_registry_repository" "api" {
  project       = var.project_id
  location      = var.region
  repository_id = "trainerlab-api"
  description   = "Docker repository for TrainerLab API images"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}

# =============================================================================
# Service Accounts
# =============================================================================

# Cloud Run service account
resource "google_service_account" "api" {
  account_id   = "trainerlab-api"
  display_name = "TrainerLab API"
  description  = "Service account for TrainerLab Cloud Run API"
}

# Grant API SA access to Cloud SQL
resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Grant API SA access to Secret Manager
resource "google_project_iam_member" "api_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Cloud Scheduler service account
resource "google_service_account" "scheduler" {
  account_id   = "trainerlab-scheduler"
  display_name = "TrainerLab Cloud Scheduler"
  description  = "Service account for Cloud Scheduler to invoke pipeline endpoints"
}

# Operations service account (for manual testing)
resource "google_service_account" "operations" {
  account_id   = "trainerlab-ops"
  display_name = "TrainerLab Operations"
  description  = "Service account for manual operations and testing in production"
}

# Allow specific users to impersonate the operations service account
resource "google_service_account_iam_member" "operations_impersonation" {
  for_each = toset(var.operations_admins)

  service_account_id = google_service_account.operations.id
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "user:${each.value}"
}

# Grant operations SA ability to view logs (for debugging)
resource "google_project_iam_member" "operations_log_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.operations.email}"
}

# =============================================================================
# Secrets
# =============================================================================

# Database password
resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "google_secret_manager_secret" "db_password" {
  project   = var.project_id
  secret_id = "trainerlab-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# NextAuth.js shared secret (JWT signing key shared with frontend)
resource "random_password" "nextauth_secret" {
  length  = 32
  special = false
}

resource "google_secret_manager_secret" "nextauth_secret" {
  project   = var.project_id
  secret_id = "trainerlab-nextauth-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "nextauth_secret" {
  secret      = google_secret_manager_secret.nextauth_secret.id
  secret_data = random_password.nextauth_secret.result
}

# Anthropic API key (Claude AI features)
resource "google_secret_manager_secret" "anthropic_api_key" {
  project   = var.project_id
  secret_id = "trainerlab-anthropic-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Cloud SQL PostgreSQL (Private)
# =============================================================================

module "database" {
  source = "./modules/cloud_sql"

  project_id    = var.project_id
  region        = var.region
  instance_name = "trainerlab-db"

  database_version  = "POSTGRES_16"
  tier              = var.db_tier
  availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
  disk_size         = var.db_disk_size

  vpc_id = local.network_self_link

  database_name     = "trainerlab"
  app_user_name     = "trainerlab_app"
  app_user_password = random_password.db_password.result

  deletion_protection    = var.environment == "prod"
  point_in_time_recovery = var.environment == "prod"
  backup_retention_days  = var.environment == "prod" ? 14 : 7

  labels = {
    environment = var.environment
    app         = "trainerlab"
  }
}

# =============================================================================
# Cloud Run API
# =============================================================================

module "api" {
  source = "./modules/cloud_run"

  project_id   = var.project_id
  region       = var.region
  service_name = "trainerlab-api"

  image = local.api_image_uri

  min_instances = var.environment == "prod" ? 1 : 0
  max_instances = var.environment == "prod" ? 10 : 3
  cpu           = "1"
  memory        = "1Gi"

  service_account_email = google_service_account.api.email
  subnet_id             = local.cloudrun_subnet_id

  env_vars = {
    ENVIRONMENT                 = var.environment
    DATABASE_URL                = "postgresql+asyncpg://trainerlab_app@${module.database.private_ip_address}:5432/trainerlab"
    REDIS_URL                   = var.redis_url
    TCGDEX_URL                  = var.tcgdex_url
    CORS_ORIGINS                = var.cors_origins
    CLOUD_RUN_URL               = "https://trainerlab-api-${data.google_project.current.number}.${var.region}.run.app"
    SCHEDULER_SERVICE_ACCOUNT   = google_service_account.scheduler.email
    OPERATIONS_SERVICE_ACCOUNT  = google_service_account.operations.email
    CLOUD_TASKS_QUEUE_PATH      = module.cloud_tasks.queue_path
    CLOUD_TASKS_LOCATION        = var.region
    API_SERVICE_ACCOUNT         = google_service_account.api.email
  }

  secret_env_vars = {
    DATABASE_PASSWORD = {
      secret_id = google_secret_manager_secret.db_password.secret_id
      version   = "latest"
    }
    NEXTAUTH_SECRET = {
      secret_id = google_secret_manager_secret.nextauth_secret.secret_id
      version   = "latest"
    }
    ANTHROPIC_API_KEY = {
      secret_id = google_secret_manager_secret.anthropic_api_key.secret_id
      version   = "latest"
    }
  }

  allow_unauthenticated = true
  custom_domain         = var.custom_domain

  depends_on_resources = [module.database]
}

# Grant scheduler SA permission to invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.api.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# Grant operations SA permission to invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "operations_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.api.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.operations.email}"
}

# =============================================================================
# Cloud Scheduler Jobs
# =============================================================================

module "scheduler" {
  source = "./modules/scheduler"

  project_id = var.project_id
  region     = var.region
  # Use constructed Cloud Run URL that matches API's CLOUD_RUN_URL setting
  cloud_run_url             = "https://trainerlab-api-${data.google_project.current.number}.${var.region}.run.app"
  scheduler_service_account = google_service_account.scheduler.email
  timezone                  = var.timezone
  paused                    = var.scheduler_paused
}

# =============================================================================
# Cloud Tasks Queue (tournament scrape pipeline)
# =============================================================================

module "cloud_tasks" {
  source = "./modules/cloud_tasks"

  project_id = var.project_id
  region     = var.region

  depends_on = [google_project_service.apis]
}

# Grant API SA permission to enqueue Cloud Tasks
resource "google_project_iam_member" "api_cloud_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

# Grant API SA permission to act as itself (required to create Cloud Tasks with its own OIDC token)
resource "google_service_account_iam_member" "api_act_as_self" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.api.email}"
}

# Grant API SA permission to invoke Cloud Run (for Cloud Tasks OIDC auth)
# Cloud Tasks will use the API SA's OIDC token to call the process endpoint
resource "google_cloud_run_v2_service_iam_member" "api_self_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.api.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api.email}"
}
