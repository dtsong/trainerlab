# Development Environment Configuration
# Usage: terraform apply -var-file=environments/dev.tfvars

project_id             = "trainerlab-dev"
region                 = "us-central1"
cloud_run_url          = "https://api-dev.trainerlab.app"
cloud_run_service_name = "trainerlab-api-dev"
timezone               = "America/New_York"
scheduler_paused       = true # Jobs paused in dev by default
