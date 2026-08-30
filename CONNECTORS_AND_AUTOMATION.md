# Connectors, Source Map & Automation

What this repo adds on top of a stock OpenWorker (`andrewyng/openworker` @ `v0.1.7`), and how to
reproduce it on a new machine. The OpenWorker checkout itself is gitignored (it's a separate repo),
so our engine changes ship as a **patch**; the app-state pieces (memory, automation) ship as
**scripts** because they live in machine-local SQLite, not here.

## What's included

| Piece | File(s) | Lives where at runtime |
|---|---|---|
| **GCS connector** (read-only: list buckets/objects, read object) | `openworker-gcs-connector.patch` | inside the `openworker/` checkout |
| **Source-map router** | `AGENTS.md` | this repo (workspace root — loaded into the agent prompt) |
| **Memory pins** (source routing) | `scripts/seed_memory.py` | OpenWorker `coworker.db` (machine-local) |
| **Inventory refresh** (deterministic) | `scripts/refresh_source_map.py`, `scripts/refresh_source_map.sh` | this repo; rewrites the `AUTO-INVENTORY` block in `AGENTS.md` |
| **Refresh automation** (UI-visible, cron) | `scripts/setup_automation.sh` | OpenWorker `automation.db` + `~/.config/coworker/config.toml` |
| **Prompts** | `prompts/*.md` | this repo |

## Reproduce on a new machine

Prereqs: OpenWorker set up per `SETUP_NOTES.md` (server + venv), `.env` filled, `gcloud` authed
to the GCP project, `scripts/start_server.sh` running.

```bash
cd ~/davita-discovery-demo

# 1. Apply the GCS connector to the OpenWorker checkout, then restart the server.
git -C openworker apply ../openworker-gcs-connector.patch     # run from repo root; path is relative
# (GUI logo change is included; restart vite if the GUI is running)
bash scripts/start_server.sh

# 2. Seed the source-routing memory pins.
openworker/.venv/bin/python scripts/seed_memory.py

# 3. Do a first inventory refresh (fills the AUTO-INVENTORY block in AGENTS.md).
bash scripts/refresh_source_map.sh

# 4. Register the scheduled refresh automation (shows in the GUI Automations panel).
bash scripts/setup_automation.sh
```

Verify: `GET /v1/connectors` shows `gcs` connected; `AGENTS.md` has a populated
`## Current inventory`; the GUI Automations panel lists "Refresh source-map inventory".

## Notes & known gaps
- **Connector auth is an OAuth access token** (`gcloud auth print-access-token`) — expires ~1h.
  Re-connect to refresh. A service-account path (auto-refresh) was the alternative, not built.
- **`gcs_list_objects` returns only the first page** (≤100 objects) in the connector. The refresh
  script paginates correctly; the agent's ad-hoc listing does not — fix pending.
- **BigQuery connector: not included** (deferred).
- The refresh automation is a thin agent turn that shells out to the deterministic script, so the
  numbers are reproducible; only the scheduling/visibility runs through the model.
