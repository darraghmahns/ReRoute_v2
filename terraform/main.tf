terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "reroute-training"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "reroute-app"
}

# Enable required APIs
resource "google_project_service" "cloud_run_api" {
  service = "run.googleapis.com"
}

resource "google_project_service" "cloud_build_api" {
  service = "cloudbuild.googleapis.com"
}

resource "google_project_service" "secret_manager_api" {
  service = "secretmanager.googleapis.com"
}

# Cloud SQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "reroute-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        value = "0.0.0.0/0"
        name  = "all"
      }
    }
    
    backup_configuration {
      enabled = true
    }
  }
}

# Database
resource "google_sql_database" "database" {
  name     = "reroute_db"
  instance = google_sql_database_instance.postgres.name
}

# Database User
resource "google_sql_user" "user" {
  name     = "reroute_user"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Redis Instance
resource "google_redis_instance" "cache" {
  name           = "reroute-cache"
  memory_size_gb = 1
  region         = var.region
}

# Use existing secrets (data sources instead of resources)
data "google_secret_manager_secret" "openai_api_key" {
  secret_id = "OPENAI_API_KEY"
}

data "google_secret_manager_secret" "strava_client_secret" {
  secret_id = "STRAVA_CLIENT_SECRET"
}

data "google_secret_manager_secret" "secret_key" {
  secret_id = "SECRET_KEY"
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "reroute-cloud-run"
  display_name = "Reroute Cloud Run Service Account"
}

# IAM bindings for service account
resource "google_project_iam_member" "cloud_run_sa_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "reroute_app" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.cloud_run_sa.email
    
    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest"
      
      ports {
        container_port = 8000
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      
      env {
        name  = "POSTGRES_HOST"
        value = google_sql_database_instance.postgres.private_ip_address
      }
      
      env {
        name  = "POSTGRES_DB"
        value = google_sql_database.database.name
      }
      
      env {
        name  = "POSTGRES_USER"
        value = google_sql_user.user.name
      }
      
      env {
        name  = "POSTGRES_PASSWORD"
        value = var.db_password
      }
      
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
      }
      
      env {
        name  = "STRAVA_CLIENT_ID"
        value = "162622"
      }
      
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "STRAVA_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.strava_client_secret.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_sql_database_instance.postgres,
    google_redis_instance.cache
  ]
}

# Allow unauthenticated invocations
resource "google_cloud_run_service_iam_binding" "default" {
  location = google_cloud_run_v2_service.reroute_app.location
  service  = google_cloud_run_v2_service.reroute_app.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

output "service_url" {
  value = google_cloud_run_v2_service.reroute_app.uri
}

output "database_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}

output "redis_host" {
  value = google_redis_instance.cache.host
}