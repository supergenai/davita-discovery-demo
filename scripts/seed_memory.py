#!/usr/bin/env python3
"""Seed OpenWorker memory with the Davita source-routing pins.

Memory lives in OpenWorker's own SQLite store (state-dir/coworker.db), which is machine-local and
NOT in this repo — so this script recreates the workspace-scoped memory entries on a new machine.
Run with the OpenWorker venv python:  openworker/.venv/bin/python scripts/seed_memory.py

Idempotent: entries are keyed, so re-running updates in place rather than duplicating.
"""

from __future__ import annotations

from pathlib import Path

WORKSPACE = str(Path(__file__).resolve().parent.parent)  # ~/davita-discovery-demo

ENTRIES = {
    "davita-src-routing":
        "Source routing (see AGENTS.md): quantitative/row-level NUMBERS -> GCS first; "
        "metric DEFINITIONS/policy/narrative -> Confluence; ticket STATUS/decisions/scope -> Jira BP2. "
        "Local *.md memos are compiled summaries only — never cite them for raw figures. "
        "If a memo and GCS disagree, GCS wins.",
    "davita-src-gcs":
        "Raw data lake = Google Cloud Storage (connector gcs). GCP project `davita-agent-demo-2023`, "
        "bucket `davita-agent-demo-2023-agent-staging`, prefix `demo/`. Authoritative for numbers. "
        "gcs_list_buckets needs project=davita-agent-demo-2023; then gcs_list_objects -> gcs_read_object.",
    "davita-src-confluence":
        "Confluence wiki (MCP atlassian-read): site davita-demo.atlassian.net/wiki, space "
        "`~71202087d07093cbdf419895df9183abeeea5f`. KNOWN metric conflict — always surface BOTH, never "
        "silently pick one: Glossary defines no_show_rate = no_shows/scheduled_trips; Ops Dashboard spec "
        "defines no_show_rate = no_shows/(completed_trips+no_shows). Writes are gated (approval) and sandbox-only.",
    "davita-src-jira":
        "Jira (MCP atlassian-read): site davita-demo.atlassian.net, project BP2 (Brooksource Pod 2). "
        "Active epic BP2-1 (Automated SMS Reminder Rollout) is CONTRADICTED by closed spike BP2-2 "
        "(Done/Won't Do — do NOT pursue SMS-only); surface the conflict. "
        "jira_search is pure JQL with NO implicit open-only filter (add a status clause to scope).",
}


def main() -> int:
    from coworker.memory import SQLiteMemoryStore, Scope
    from coworker.secrets import state_dir

    store = SQLiteMemoryStore(state_dir() / "coworker.db")
    existing = {m.key: m for m in store.list(scope=Scope.WORKSPACE, workspace=WORKSPACE) if m.key}
    added = updated = 0
    for key, content in ENTRIES.items():
        if key in existing:
            store.update(existing[key].id, content); updated += 1
        else:
            store.add(content, scope=Scope.WORKSPACE, key=key, workspace=WORKSPACE); added += 1
    print(f"memory seeded: added={added} updated={updated} (workspace={WORKSPACE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
