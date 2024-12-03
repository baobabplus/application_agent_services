output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.app_agent_services_cloud_run.status[0].url
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = google_api_gateway_gateway.app_agent_services_gateway.default_hostname
}

output "api_key" {
  description = "API Key for accessing the API Gateway"
  value       = google_apikeys_key.app_agent_services_api_key.key_string
  sensitive = true
}
