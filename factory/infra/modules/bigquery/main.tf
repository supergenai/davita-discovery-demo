variable "project_id" { type = string }
variable "region" { type = string }

locals {
  # medallion + results + ops (review queue, sent emails)
  datasets = ["bronze", "silver", "gold", "dq_results", "ops"]
}

resource "google_bigquery_dataset" "ds" {
  for_each                   = toset(local.datasets)
  project                    = var.project_id
  dataset_id                 = each.value
  location                   = var.region
  delete_contents_on_destroy = true
  labels                     = { platform = "agent-factory" }
}

# Results and HITL tables the pipeline writes to. Sources (bronze/silver) are
# loaded by seed/load_seed.py (autodetect schema), so only the write-targets are declared.
resource "google_bigquery_table" "admin_turnover" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.ds["dq_results"].dataset_id
  table_id            = "admin_turnover"
  deletion_protection = false
  schema              = jsonencode([
    { name = "kind", type = "STRING" },
    { name = "severity", type = "STRING" },
    { name = "employee_id", type = "STRING" },
    { name = "facility_id", type = "STRING" },
    { name = "detail", type = "STRING" },
    { name = "explanation", type = "STRING" },
    { name = "priority", type = "INTEGER" },
  ])
}

resource "google_bigquery_table" "review_queue" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "review_queue"
  deletion_protection = false
  schema              = jsonencode([
    { name = "review_id", type = "STRING" },
    { name = "agent", type = "STRING" },
    { name = "status", type = "STRING" },
    { name = "created_at", type = "TIMESTAMP" },
    { name = "kind", type = "STRING" },
    { name = "severity", type = "STRING" },
    { name = "employee_id", type = "STRING" },
    { name = "facility_id", type = "STRING" },
    { name = "detail", type = "STRING" },
    { name = "reviewer", type = "STRING" },
  ])
}

resource "google_bigquery_table" "sent_emails" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.ds["ops"].dataset_id
  table_id            = "sent_emails"
  deletion_protection = false
  schema              = jsonencode([
    { name = "to", type = "STRING" },
    { name = "subject", type = "STRING" },
    { name = "body", type = "STRING" },
    { name = "sent_at", type = "TIMESTAMP" },
    { name = "channel", type = "STRING" },
  ])
}

output "dataset_ids" { value = [for d in google_bigquery_dataset.ds : d.dataset_id] }
