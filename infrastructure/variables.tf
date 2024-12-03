variable "fastapi_image" {
  description = "Docker image for FastAPI service"
  type        = string
  default = "gcr.io/steam-outlet-209412/application-agent-services:latest"
}

variable "project_id" {
  type        = string
  description = "Baobabplus GCP"
  default     = "steam-outlet-209412"
}

variable "region" {
  type        = string
  description = "Europe west 1"
  default     = "europe-west1"
}

variable "zone" {
  type        = string
  description = "The default compute zone"
  default     = "europe-west1-b"
}
