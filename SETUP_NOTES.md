# SETUP_NOTES — OpenWorker discovery demo

Fill this in AS YOU GO during real execution. Redact every secret. This file is the
step-6 deliverable and doubles as the runbook for the next person.

## Versions and pinned tag
- python3: `Python 3.14.5`
- node: `v24.10.0`
- uv/uvx: `uv 0.9.5`
- git: `git 2.51.1`
- rustup: NOT installed — optional, only needed to build the Tauri desktop shell from source. GUI runs via `npm run dev` (vite), so not required for this demo.
- OpenWorker release tag pinned: `v0.1.7` (latest tag; main not used)

## Config used (secrets redacted)
- Atlassian site: `https://davita-demo.atlassian.net` (Confluence: `/wiki`)
- Sandbox space key: `Davitademo` | Jira project: `BP2` (Brooksource Pod 2)
- API token: `REDACTED` (in .env only)
- Confluence write target: a DEDICATED SANDBOX space (user decision). Key from `.env` `SANDBOX_SPACE_KEY`.
  GUARDRAIL: writes go ONLY to this key, never any other space; Step 5 requires explicit go-ahead.
- MCP launch: `uvx mcp-atlassian`, env from `.env` (tokens: `REDACTED`)
- OpenWorker server: `.venv/bin/openworker-server --cwd ~/davita-discovery-demo --port 8765`
  - Flags available: `--cwd --model --mode {discuss,plan,interactive,auto} --host --port`
- GUI: `surfaces/gui`, `npm run dev` (vite)
- Server URL: `http://127.0.0.1:8765`  — UP (uvicorn); `GET /` returns 401 (alive, auth-gated)
- GUI URL: `http://localhost:1420`  — UP, HTTP 200, `<title>OpenWorker</title>` (vite v5.4.21)
- Running PIDs (this session): server 29461, GUI 30256 — stop with `scripts/teardown.sh`

## MCP tool inventory (from standalone stdio probe, before wiring into OpenWorker)
Server: `sooperset/mcp-atlassian` via `uvx mcp-atlassian`. Auth: username + API token (Cloud).
Standalone launch verified: `python3 scripts/mcp_probe.py .env` (full list) and
`python3 scripts/mcp_call.py .env` (schemas + live read). Live read returned 3 Jira projects
(BP2, KAN, SUP) → credentials authenticate.

Key tools (server exposes ~80 total across Jira + Confluence; full dump via mcp_probe.py):

| Tool | Purpose | Read/Write |
|---|---|---|
| `confluence_search` | search by text or CQL, `spaces_filter` | R |
| `confluence_get_page` | FULL page body by page_id OR title+space_key; `convert_to_markdown` | R |
| `confluence_get_space_page_tree` | page hierarchy for a space | R |
| `confluence_create_page` | create page (space_key*, title*, content, content_format) | W |
| `confluence_update_page` / `confluence_delete_page` | edit / remove page | W |
| `jira_search` | JQL search (`jql`*, fields, limit 1–50, projects_filter) | R |
| `jira_get_issue` (+ get_all_projects, search_projects) | fetch issue / list projects | R |
| `jira_create_issue` / `jira_update_issue` | create / edit issue | W |

## The four determinations (Part 2, Step 3) — VERIFIED
1. **Confluence SEARCH vs FULL PAGE FETCH:**
   - SEARCH = `confluence_search` (simple text or CQL; `spaces_filter` to scope to a space).
   - FULL PAGE FETCH = `confluence_get_page` (by `page_id`, or `title`+`space_key`). Returns full
     body; pass `convert_to_markdown=true` for markdown. Distinct tools — search returns hits, get_page returns the body.
2. **Page-create + draft support:** `confluence_create_page` EXISTS but has **NO draft/status param**.
   It publishes a live page immediately. (There is a `subtype='live'` for Confluence Live Docs — NOT a draft.)
   → Demo step 5 / prompt #3 say "draft"; the tool cannot. The write test page publishes on approval.
   Governance = the approval GATE, not a draft state. Title the test page "delete me" and remove it after.
3. **Jira closed/resolved issues:** `jira_search` is pure JQL — there is NO implicit open-only filter.
   Omitting a status clause returns ALL statuses incl. Closed/Done/Resolved. To be explicit in the demo:
   `project = BP2 AND status in (Done, Closed, Resolved) ORDER BY updated DESC`. Closed issues DO surface.
4. **stdio without a proxy:** YES. The stdio probe drove it directly (log: "Starting server with STDIO
   transport"); no `mcp-remote` needed. OpenWorker's MCP config launches via command/args over stdio,
   which this server supports natively. (Path A. Path B/Rovo OAuth would use mcp-remote.)

## OpenWorker registration + connection (Step 3/4, verified through OpenWorker)
Config file: `~/.config/coworker/mcp.json` (global). Secrets resolve from `~/.config/coworker/.env`
(0600) via `${VAR}` — never inlined. Two entries, split to get reads-ungated / writes-gated
(generic MCP servers gate all-or-nothing at server level; connector-style per-tool gating only
applies to registry-backed connectors — so we split by fail-closed allowlist):
- `atlassian-read`  — `requires_approval: false`, include_tools = 8 read tools
- `atlassian-write` — `requires_approval: true`,  include_tools = [create/update/delete_page]

Connected through OpenWorker API (`POST /v1/mcp/<name>/connect`): both `status=connected`.
SECURITY BOUNDARY VERIFIED via session tool-prep filter (`_filtered`):
- read server resolves to ONLY read tools (no create/update/delete survive) — ungated.
- write server resolves to ONLY the 3 page-write tools — gated.
→ No destructive tool is ever reachable ungated. Matches Step-4 requirement.

## Model provider
DEFAULT = **Kimi `kimi:kimi-k2.6`** (Anthropic key is valid but has NO CREDITS). Both providers
configured via env_key fallback (start_server.sh exports MOONSHOT_API_KEY + ANTHROPIC_API_KEY from
.env). Default set in `~/.config/coworker/prefs.json`; `/v1/health` confirms `model: kimi:kimi-k2.6`.
Live-tested: Kimi key 200 on /models AND a real chat completion (content "OK."). Switch to Claude in
the composer only if credits are added.
CAVEAT: kimi-k2.6 is a REASONING model — it burns ~100+ tokens on reasoning before content (a 10-token
cap returned empty). Expect slower, token-heavier turns; cap full-page reads to 10–15 in demo prompt #2.
NOTE: if `.env` is hand-edited, keep COWORKER_API_TOKEN + MOONSHOT_API_KEY lines — losing COWORKER_API_TOKEN
makes the server mint a random token and the GUI can't auth (a stale editor buffer clobbered these once).

## Sidecar auth (GUI <-> server) — IMPORTANT for cold-boot
`openworker-server` generates a random token per launch and writes `~/.config/coworker/sidecar-8765.token`;
vite bakes that token ONCE at `npm run dev` start. So a server restart alone breaks the GUI's token.
FIX (this setup): a FIXED token in `.env` (`COWORKER_API_TOKEN`) is exported to the server and passed
to vite as `VITE_COWORKER_API_TOKEN` (start_gui.sh) — order- and restart-independent. Local demo only.

## Runbook
- Start server: `scripts/start_server.sh`  (port 8765; injects Atlassian + ANTHROPIC + COWORKER token)
- Start GUI:    `scripts/start_gui.sh`      (http://localhost:1420)
- Verify MCP:   `python3 scripts/mcp_probe.py .env`  (standalone tool dump)
- Teardown:     `scripts/teardown.sh`

## Smoke test results (Step 4)
- Standalone MCP auth: `jira_get_all_projects` → BP2 (Brooksource Pod 2), KAN (Demo-1), SUP (Support).
- Through OpenWorker: both servers connect, 98 raw tools each; session filter narrows to 8 read / 3 write.
- Jira closed issues: use JQL `project = BP2 AND status in (Done, Closed, Resolved)` (no implicit filter).
- REMAINING (agent-driven, run in GUI): the 3-part read run (spaces / search+fetch / Jira incl. closed)
  and confirming the approval gate visually. Content must exist first (see seeding).

## Seeding outcome (executed)
- JIRA (BP2) — CREATED: BP2-1 Epic (Automated SMS Reminder Rollout), BP2-2 SPIKE (now **Done**;
  description records "Won't Do / do NOT pursue SMS-only"), BP2-3/4/5 Stories (To Do).
  The active-epic-vs-closed-spike contradiction is fully present in Jira alone.
  (Resolution "Won't Do" not settable via API — not on this workflow's transition screen; set in UI if wanted.)
- CONFLUENCE — initially BLOCKED (401 at /wiki root): Confluence was not activated on the site. After the
  user added the Confluence product, auth returned 200. Write target switched from the non-existent
  "Davitademo" to the user's PERSONAL space `~71202087d07093cbdf419895df9183abeeea5f` (name "arsalan hafiz",
  id 163842). SANDBOX_SPACE_KEY quoted in .env (the ~ else tilde-expands when scripts source .env).
- CONFLUENCE seed — CREATED: all 14 pages (verified: 16 total in space incl. 2 Confluence defaults).
  Includes the metric contradiction (Glossary `no_shows/scheduled_trips` vs Ops Dashboard
  `no_shows/(completed+no_shows)`) and the closed-spike write-up. `confluence_search 'no-show rate'`
  returns them; `confluence_get_page` returns full bodies → Step 4b read path verified.
- CORRECTION (kept for the record): the Step-4 "AUTH OK" earlier verified JIRA only. Confluence was not
  read-tested until seeding, which is when the 401 surfaced. Now resolved and verified.

## Write-path test (Step 5 — NOT run; needs explicit go-ahead)
- Guardrail: writes ONLY to space `Davitademo`. `confluence_create_page` has NO draft mode → publishes
  on approval. Title test page "MCP write test — delete me" and delete after.
- Page ID: `<fill>`   URL: `<fill>`   Landed as: published (no draft support)

## Failures hit and how resolved
- Prefs written to workspace `.coworker/` first — build_app uses `data_dir=state_dir()`, so prefs must
  live in `~/.config/coworker/prefs.json`. Moved; model then resolved to Claude.
- Server restart after GUI start broke sidecar token (regenerated per launch) → switched to fixed token.
- Python 3.14 install emitted "Cache entry deserialization failed" pip warnings — harmless (stale cache).

## Teardown
Run `scripts/teardown.sh`. Then: delete the "MCP write test" page if created; consider revoking the
API token; remove `openworker/` and `briefs/` for a clean slate. `.env` + `~/.config/coworker/.env`
hold live secrets — rotate the Atlassian token and Anthropic key after the demo (they transited setup).
