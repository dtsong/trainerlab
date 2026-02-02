# =============================================================================
# GitHub Actions OIDC Authentication
# Enables keyless authentication from GitHub Actions to GCP
# =============================================================================

# Workload Identity Pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-actions"
  display_name              = "GitHub Actions"
  description               = "Workload Identity Pool for GitHub Actions OIDC"

  depends_on = [google_project_service.apis]
}

# Workload Identity Pool Provider for GitHub
resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub"
  description                        = "GitHub OIDC provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions"
  description  = "Service account for GitHub Actions CI/CD"
}

# Allow GitHub Actions to impersonate the service account
resource "google_service_account_iam_member" "github_actions_wif" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# Grant permissions to GitHub Actions service account

# Push to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "github_actions_push" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.api.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.github_actions.email}"
}

# Deploy to Cloud Run
resource "google_project_iam_member" "github_actions_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Execute Cloud Run Jobs (for migrations)
resource "google_project_iam_member" "github_actions_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Act as the API service account (for Cloud Run deployments)
resource "google_service_account_iam_member" "github_actions_act_as_api" {
  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# =============================================================================
# Outputs
# =============================================================================

output "github_workload_identity_provider" {
  description = "Workload Identity Provider for GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "github_service_account_email" {
  description = "GitHub Actions service account email"
  value       = google_service_account.github_actions.email
}
