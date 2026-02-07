# Development Environment Configuration
# Usage: terraform workspace select dev && terraform apply -var-file=environments/dev.tfvars
# Estimated cost: ~$10/month (db-f1-micro $9, Cloud Run $0 at min=0)

project_id  = "trainerlab-dev"
region      = "us-west1"
environment = "dev"

# Cloud Run (minimal — scale to zero)
api_image = "" # Uses latest tag default

# Cloud SQL (smallest tier — ~$9/month)
db_tier      = "db-f1-micro"
db_disk_size = 10

# Scheduler (paused by default in dev)
timezone         = "America/New_York"
scheduler_paused = true

# GitHub Actions
github_repo = "dtsong/trainerlab"
