# Davita Discovery Demo — Source Map & Routing

This workspace pulls from several connected sources. **Before answering any question, route to
the right source below, then DISCOVER live** (list/search) rather than relying on any hardcoded
list. A tool being available does not mean it is the right place to look — pick the authoritative
source for the *kind* of question, then enumerate it.

## Where each kind of information lives

| Question is about… | Go to | How to discover |
|---|---|---|
| **Raw / row-level numbers** (counts, per-clinic, per-week) | **GCS** | `gcs_list_objects` under the bucket, then `gcs_read_object` |
| **Metric definitions, policy, narrative, program docs** | **Confluence** | `confluence_search` / `confluence_get_space_page_tree`, then `confluence_get_page` |
| **Work status, tickets, decisions, scope** | **Jira (BP2)** | `jira_search` (JQL), then `jira_get_issue` |
| **Public web pages** | **Browser** | `browser_read_url` — external only, not internal data |
| Quick recap of prior findings | Local `*.md` memos | **Summaries only — never cite for raw figures** |

**Default rules**
- Any *quantitative* question → **GCS first** (authoritative for figures).
- Any *definition / rule / policy* question → **Confluence first** (authoritative for how things are defined).
- Any *status / decision* question → **Jira BP2**.
- **Always list/search the source live.** Do not assume the set of files, tickets, or pages from
  memory or from the inventory below — the inventory is a snapshot; the tools are the truth.
- Local `*.md` memos are compiled summaries. If a memo figure and the live source disagree, **the live source wins.**

## Source coordinates (stable config)

- **GCS** (connector `gcs`): GCP project `davita-agent-demo-2023`, bucket
  `davita-agent-demo-2023-agent-staging`. `gcs_list_buckets` needs `project=davita-agent-demo-2023`.
- **Jira** (MCP `atlassian-read` / `atlassian-write`): site `https://davita-demo.atlassian.net`,
  project `BP2`. `jira_search` is pure JQL with **no implicit open-only filter** — add a status
  clause to scope (e.g. `status in (Done, Closed, Resolved)` to include closed work).
- **Confluence** (MCP `atlassian-read` / `atlassian-write`): site
  `https://davita-demo.atlassian.net/wiki`, space `~71202087d07093cbdf419895df9183abeeea5f`.
  Writes (`confluence_create_page/update/delete`) are **gated (require approval)**, publish
  immediately (no draft), and target the sandbox space only.
- **Browser** (connector `browser`): public web fetch/automation; not a source of internal data.

## Curated consistency watch (domain knowledge — persists across refreshes)

These are known, deliberate conflicts in the demo data. Surface them; never silently pick a side.
1. **No-show-rate definition conflict** between Confluence's Glossary and the Ops Dashboard spec —
   one divides by *scheduled trips*, the other by *completed + no-shows*. Any no-show-rate answer
   must state which definition it used and flag that a conflicting one exists.
2. **SMS approach conflict** in Jira: an active epic assumes SMS-only reminders while a closed
   spike argues against SMS-only. Check ticket status before treating the epic as settled.
3. **Raw vs. narrative**: GCS holds the actual counts; the local `*.md` memos paraphrase them. On
   any disagreement, GCS wins.

---

<!-- BEGIN AUTO-INVENTORY -->
## Current inventory (auto-generated — do not edit by hand)

_Last refreshed: 2026-08-30 01:08 UTC by scripts/refresh_source_map.py. Regenerated on schedule; edits here are overwritten._

### Google Cloud Storage

**Bucket `davita-agent-demo-2023-agent-staging`** (6 objects):

- `agent_engine/agent_engine.pkl` — 3,733 bytes (updated 2026-08-27)
- `agent_engine/dependencies.tar.gz` — 42,516 bytes (updated 2026-08-27)
- `agent_engine/requirements.txt` — 109 bytes (updated 2026-08-27)
- `demo/transport/rideshare_fallback_aug.csv` — 83 bytes (updated 2026-08-30)
- `demo/transport/sms_reminder_optout_rates.csv` — 173 bytes (updated 2026-08-30)
- `demo/transport/transport_no_show_weekly.csv` — 555 bytes (updated 2026-08-30)

### Jira

**Jira project `BP2`** (5 issues):

- `BP2-1` (Epic, **To Do**) — Automated SMS Reminder Rollout for regional clinic transport
- `BP2-2` (Task, **Done**) — SPIKE: Is an SMS-only reminder program sufficient to hit the 30% no-show target?
- `BP2-3` (Story, **To Do**) — Validate mobile phone numbers at transport booking entry
- `BP2-4` (Story, **To Do**) — Design hybrid reminder flow (auto reminder + live confirmation for high-risk trips)
- `BP2-5` (Story, **To Do**) — Reconcile the two no-show-rate definitions (Glossary vs Ops Dashboard)

### Confluence

**Confluence space `~71202087d07093cbdf419895df9183abeeea5f`** (18 pages):

- `688129` — 2024 No-Show Baseline Analysis
- `917505` — Decision Log
- `851969` — EPIC BRIEF — Automated SMS Reminder Rollout (active)
- `163940` — Getting started in Confluence from Jira
- `622593` — Glossary — Transport Metrics (authoritative definitions)
- `819201` — Literature & Prior-Art Scan — No-Show Drivers
- `163938` — Overview
- `131074` — Patient Segments & Access Barriers
- `1048578` — Patient Transport No-Show Reduction — Discovery Memo
- `589825` — Patient Transport No-Show Reduction — Program Charter
- `720897` — Pilot A — Automated SMS Reminders (results)
- `753665` — Pilot B — Live Caller Confirmation (results)
- `2490370` — Product Spec: Regional Clinic Patient Transport No-Show Reduction
- `655361` — Regional Ops Dashboard — Spec v2
- `786433` — Rideshare Fallback — Vendor Evaluation
- `622613` — Scheduling System Constraints
- `884737` — Spike Write-up — SMS-Only Reminder Approach (CLOSED, Won't Do)
- `753685` — Stakeholders & Owners

<!-- END AUTO-INVENTORY -->
