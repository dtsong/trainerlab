# Production Environment Configuration
# Usage: terraform apply -var-file=environments/prod.tfvars

project_id             = "trainerlab-prod"
region                 = "us-central1"
cloud_run_url          = "https://api.trainerlab.app"
cloud_run_service_name = "trainerlab-api"
timezone               = "America/New_York"
scheduler_paused       = false # Jobs active in production
