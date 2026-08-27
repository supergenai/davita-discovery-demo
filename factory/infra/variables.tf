variable "project_id" {
  type        = string
  description = "Existing GCP project id to deploy the factory into."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Region with Vertex AI / Agent Engine available."
}

variable "agent_id" {
  type        = string
  default     = "admin-turnover-dq"
  description = "Per-agent identifier (service account + scheduler naming + labels)."
}

variable "schedule" {
  type        = string
  default     = "0 6 * * 1"
  description = "Cron for the agent's Cloud Scheduler trigger (weekly Mon 06:00)."
}

variable "agent_target_uri" {
  type        = string
  default     = ""
  description = "HTTPS endpoint of the deployed agent (Agent Engine / Cloud Run) the scheduler calls. Set after deploy."
}
