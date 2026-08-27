# Davita Agent Factory

A reusable **ADK agent chassis** (hub) that powers many data-quality / determination
agents (spokes) on GCP. A new agent is a `config.yaml`, not new plumbing: the factory
wires shared sockets - data sources, skills, guardrails, business logic, HITL, actions -
from the spec. First spoke: **Admin Turnover Reconciliation** (Oracle MDM vs Workday/CWOW).

Greenfield and standalone. Gemini-only, ADK-only. `openworker/` is inspiration, not a dependency.

## Layout
```
agent_factory/        # THE HUB (reusable)
  config.py           # AgentSpec (the spec a spoke fills)
  sources.py          # source connector interface (mock: CSV offline / BigQuery online)
  skills/             # GCP capabilities as ADK tools (mdm/workday/cwow/bigquery/looker/elie)
  business_logic.py   # deterministic reconciliation primitives (the auditable match)
  enrich.py           # Gemini explains + prioritizes (never decides)
  guardrails.py       # tool allow-list, cost cap, DLP de-identify (ADK callbacks)
  hitl.py             # review queue + confirm -> ELie
  sinks.py            # write BigQuery / Looker / ELie (stubs marked)
  pipeline.py         # background run: Retrieve -> Reconcile -> Enrich -> Report
  factory.py          # build_agent(spec) -> ADK LlmAgent (interactive/UI/Agent-Engine surface)
  runtime.py          # run + deploy CLI
  ui/app.py           # HITL review UI (FastAPI, Cloud Run)
agents/admin_turnover_dq/   # THE SPOKE (thin config)
  config.yaml  rules.py  agent.py
seed/                 # mock enterprise CSVs + BigQuery loader
infra/                # Terraform (project APIs, BigQuery, per-agent SA, scheduler, secrets)
tests/                # deterministic reconciliation + factory wiring
```

## Run locally (offline, no GCP)
```bash
uv sync
FACTORY_OFFLINE=1 uv run pytest -q
FACTORY_OFFLINE=1 uv run python agents/admin_turnover_dq/agent.py --local   # -> .local_out/
FACTORY_OFFLINE=1 uv run uvicorn agent_factory.ui.app:app --reload          # HITL review UI
```
Offline, sources read the seed CSVs and actions/LLM run in stub mode, so the whole
Retrieve -> Reconcile -> HITL -> ELie loop is verifiable with zero cloud credentials.

## Deploy to GCP (existing project)
```bash
export GOOGLE_CLOUD_PROJECT=... GOOGLE_CLOUD_REGION=us-central1
cd infra && terraform init && terraform apply -var-file=envs/dev/terraform.tfvars
uv run python seed/load_seed.py                                   # bronze/silver
uv run python -m agent_factory.runtime deploy agents/admin_turnover_dq/config.yaml
# set agent_target_uri in tfvars to the deployed endpoint, re-apply to point the scheduler
gcloud scheduler jobs run trigger-admin-turnover-dq --location=$GOOGLE_CLOUD_REGION
```

## Prototype boundary (real vs stub)
- **Real:** ADK factory, BigQuery, Gemini, Vertex AI Agent Engine, Cloud Scheduler, IAM, Terraform.
- **Mock:** MDM/Workday/CWOW = seeded BigQuery tables behind the `sources.py` connector interface
  (swap for GCP Integration Connectors later). ELie + Looker = stubs in `sinks.py` with the
  integration seam clearly marked.

## Design rules
- The reconciliation **match is deterministic code** (`rules.py`); Gemini only explains + prioritizes.
- Autonomy **L2**: the ELie email fires only after a human confirms in the HITL queue.
- Per-agent service account = blast-radius control; shared chassis = code reuse, not one process.
