output "datasets" {
  value       = module.bigquery.dataset_ids
  description = "BigQuery datasets created for the factory."
}

output "agent_service_account" {
  value       = module.agent_sa.email
  description = "Per-agent least-privilege service account."
}

output "scheduler_job" {
  value       = module.agent_trigger.job_name
  description = "Cloud Scheduler job that triggers the agent."
}
