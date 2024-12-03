terraform {
  backend "gcs" {
    bucket = "terraform_bbplus_bucket"
    prefix = "state/application_agent_services"
  }
}
