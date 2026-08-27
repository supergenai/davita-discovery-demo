# Root module: wires the factory's GCP footprint into an EXISTING project.
# Everything here is shared platform except agent_sa/agent_trigger, which are per-agent.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "apis" {
  source     = "./modules/project_apis"
  project_id = var.project_id
}

module "bigquery" {
  source     = "./modules/bigquery"
  project_id = var.project_id
  region     = var.region
  depends_on = [module.apis]
}

# Per-agent: least-privilege service account.
module "agent_sa" {
  source     = "./modules/agent_sa"
  project_id = var.project_id
  agent_id   = var.agent_id
  depends_on = [module.apis]
}

# Per-agent: weekly Cloud Scheduler trigger that invokes the deployed agent endpoint.
module "agent_trigger" {
  source           = "./modules/agent_trigger"
  project_id       = var.project_id
  region           = var.region
  agent_id         = var.agent_id
  schedule         = var.schedule
  target_uri       = var.agent_target_uri
  invoker_sa_email = module.agent_sa.email
  depends_on       = [module.apis]
}

module "secrets" {
  source     = "./modules/secrets"
  project_id = var.project_id
  depends_on = [module.apis]
}
