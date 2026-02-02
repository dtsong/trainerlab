# Production Environment Configuration
# Usage: terraform apply -var-file=environments/prod.tfvars

project_id  = "trainerlab-prod"
region      = "us-west1"
environment = "prod"

# Cloud Run
api_image     = "us-west1-docker.pkg.dev/trainerlab-prod/trainerlab-api/api:latest"
custom_domain = ""  # Domain mapping requires ownership verification
cors_origins  = "https://trainerlab.io,https://www.trainerlab.io"

# Cloud SQL
db_tier      = "db-f1-micro"
db_disk_size = 10

# Scheduler
timezone         = "America/New_York"
scheduler_paused = false

# GitHub Actions
github_repo = "danielsongdev/trainerlab"
