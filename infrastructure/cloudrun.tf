resource "google_cloud_run_service" "app_agent_services_cloud_run" {
  name     = "fastapi-service"
  location = var.region

  template {
    spec {
      containers {
        image = var.fastapi_image
        ports {
          container_port = 8080
        }
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1"
          }
        }
      }
      timeout_seconds = 300
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# IAM Policy pour autoriser l'API Gateway à invoquer Cloud Run
resource "google_cloud_run_service_iam_member" "apigateway_invoker" {
  service  = google_cloud_run_service.app_agent_services_cloud_run.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app_agent_services_sa.email}"
}
