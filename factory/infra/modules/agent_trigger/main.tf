variable "project_id" { type = string }
variable "region" { type = string }
variable "agent_id" { type = string }
variable "schedule" { type = string }
variable "target_uri" { type = string }
variable "invoker_sa_email" { type = string }

# Weekly trigger. Calls the deployed agent endpoint with an OIDC token minted for
# the per-agent service account. target_uri is set after the agent is deployed.
resource "google_cloud_scheduler_job" "agent" {
  project   = var.project_id
  region    = var.region
  name      = "trigger-${var.agent_id}"
  schedule  = var.schedule
  time_zone = "America/Denver"

  http_target {
    http_method = "POST"
    uri         = var.target_uri != "" ? var.target_uri : "https://example.invalid/set-after-deploy"
    oidc_token {
      service_account_email = var.invoker_sa_email
    }
  }

  # Avoid failing plan/apply before the agent endpoint exists.
  lifecycle {
    ignore_changes = [http_target[0].uri]
  }
}

output "job_name" { value = google_cloud_scheduler_job.agent.name }
