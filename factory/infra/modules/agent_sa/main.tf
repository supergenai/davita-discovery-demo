variable "project_id" { type = string }
variable "agent_id" { type = string }

# Per-agent least-privilege service account. Blast-radius control lives here.
resource "google_service_account" "agent" {
  project      = var.project_id
  account_id   = "agent-${var.agent_id}"
  display_name = "Agent Factory - ${var.agent_id}"
}

locals {
  # Minimum roles for the DQ agent: read data, run queries, write results, call Vertex.
  roles = [
    "roles/bigquery.dataViewer", # read bronze/silver/gold (tighten to authorized views in prod)
    "roles/bigquery.dataEditor", # write dq_results + ops
    "roles/bigquery.jobUser",    # run queries
    "roles/aiplatform.user",     # Gemini / Agent Engine
    "roles/secretmanager.secretAccessor",
  ]
}

resource "google_project_iam_member" "agent_roles" {
  for_each = toset(local.roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.agent.email}"
}

output "email" { value = google_service_account.agent.email }
