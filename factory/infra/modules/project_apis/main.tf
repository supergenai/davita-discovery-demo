variable "project_id" { type = string }

locals {
  services = [
    "aiplatform.googleapis.com",      # Vertex AI / Agent Engine
    "bigquery.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "dlp.googleapis.com",             # Sensitive Data Protection
    "run.googleapis.com",             # UI surface + trigger shim
    "iam.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
  ]
}

resource "google_project_service" "svc" {
  for_each                   = toset(local.services)
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}
