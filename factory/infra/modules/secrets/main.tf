variable "project_id" { type = string }

# Placeholder secret containers (values added out-of-band, never in Terraform).
# e.g. the real ELie API key when the stub is swapped for the real integration.
locals {
  secret_ids = ["elie-api-key"]
}

resource "google_secret_manager_secret" "s" {
  for_each  = toset(local.secret_ids)
  project   = var.project_id
  secret_id = each.value
  replication {
    auto {}
  }
}

output "secret_ids" { value = [for s in google_secret_manager_secret.s : s.secret_id] }
