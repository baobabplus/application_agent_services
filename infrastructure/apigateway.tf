resource "google_service_account" "app_agent_services_sa" {
  account_id   = "api-gateway-app-agent-services"
  display_name = "API Gateway Service Account"
}

resource "google_api_gateway_api" "app_agent_services_api" {
  provider     = google-beta
  api_id       = "app-agent-services-api"
  display_name = "Application Agent Services API Gateway"
}

# Génération du fichier openapi.yaml
resource "local_file" "openapi_yaml" {
  filename = "${path.module}/openapi.yaml"

  content = templatefile("${path.module}/openapi_template.yaml", {
    cloud_run_url   = google_cloud_run_service.app_agent_services_cloud_run.status[0].url
  })

  depends_on = [
    google_cloud_run_service.app_agent_services_cloud_run
  ]
}

# Configuration de l'API Gateway avec le fichier généré
resource "google_api_gateway_api_config" "app_agent_services_api_config" {
  provider      = google-beta
  api           = google_api_gateway_api.app_agent_services_api.id
  api_config_id = "app-agent-services-config"

  openapi_documents {
    document {
      path = local_file.openapi_yaml.filename
      contents = local_file.openapi_yaml.content
    }
  }

  depends_on = [
    local_file.openapi_yaml
  ]
}

resource "google_api_gateway_gateway" "app_agent_services_gateway" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.app_agent_services_api_config.id
  gateway_id = "app-agent-services-gateway"
}

resource "google_apikeys_key" "app_agent_services_api_key" {
  name         = "app-agent-services-api-key"
  display_name = "Application Agent Services API Key"
}
