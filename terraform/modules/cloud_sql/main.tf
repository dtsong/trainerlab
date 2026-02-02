# Cloud SQL PostgreSQL Instance for TrainerLab
# Private instance with pgvector extension support

resource "google_sql_database_instance" "this" {
  name             = var.instance_name
  project          = var.project_id
  region           = var.region
  database_version = var.database_version

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_size         = var.disk_size
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    # Private IP only - no public IP
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "cloudsql.enable_pg_cron"
      value = "on"
    }

    database_flags {
      name  = "max_connections"
      value = var.max_connections
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.point_in_time_recovery
      backup_retention_settings {
        retained_backups = var.backup_retention_days
      }
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # 4 AM
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = false
    }

    user_labels = var.labels
  }

  deletion_protection = var.deletion_protection

  lifecycle {
    prevent_destroy = false
  }
}

# Create database
resource "google_sql_database" "this" {
  name     = var.database_name
  instance = google_sql_database_instance.this.name
  project  = var.project_id
}

# Create application user
resource "google_sql_user" "app" {
  name     = var.app_user_name
  instance = google_sql_database_instance.this.name
  project  = var.project_id
  password = var.app_user_password
}

# Enable pgvector extension (via null_resource since GCP doesn't support it natively)
# Note: This requires manual setup or Cloud SQL Admin API
