#!/usr/bin/env python3
"""Refresh the auto-generated inventory in AGENTS.md by enumerating every connected source.

Deterministic — no model calls, no running OpenWorker server, no MCP. It reads creds from the
workspace .env, lists each source directly (GCS JSON API, Jira/Confluence REST), and rewrites the
block between the AUTO-INVENTORY markers in AGENTS.md. It also updates a single workspace memory
entry with a one-line summary + timestamp so a session sees "last refreshed" even before AGENTS.md.

Per-source failures are isolated: if one source errors, its section says so and the others still
refresh. Run via scripts/refresh_source_map.sh (sets PATH + venv) from cron/launchd or by hand.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = ROOT / "AGENTS.md"
BEGIN = "<!-- BEGIN AUTO-INVENTORY -->"
END = "<!-- END AUTO-INVENTORY -->"

GCP_PROJECT = "davita-agent-demo-2023"
GCS_BUCKET = "davita-agent-demo-2023-agent-staging"
JIRA_PROJECT = "BP2"


def _load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'").strip('"')
    return env


ENV = {**_load_env(ROOT / ".env"), **os.environ}


def _gcloud_token() -> str:
    return subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def gcs_section() -> str:
    try:
        token = _gcloud_token()
        if not token:
            return "- ⚠️ GCS: could not obtain a gcloud access token.\n"
        items: list[dict] = []
        page = ""
        with httpx.Client(timeout=30) as c:
            while True:  # paginate — buckets can hold more than one page
                params = {"fields": "items(name,size,updated),nextPageToken", "maxResults": 1000}
                if page:
                    params["pageToken"] = page
                r = c.get(
                    f"https://storage.googleapis.com/storage/v1/b/{GCS_BUCKET}/o",
                    headers={"Authorization": f"Bearer {token}"}, params=params,
                )
                r.raise_for_status()
                data = r.json()
                items.extend(data.get("items", []))
                page = data.get("nextPageToken", "")
                if not page:
                    break
        if not items:
            return f"- Bucket `{GCS_BUCKET}` is empty.\n"
        lines = [f"**Bucket `{GCS_BUCKET}`** ({len(items)} objects):\n"]
        for it in sorted(items, key=lambda x: x["name"]):
            size = int(it.get("size", 0))
            lines.append(f"- `{it['name']}` — {size:,} bytes (updated {it.get('updated','?')[:10]})")
        return "\n".join(lines) + "\n"
    except Exception as exc:
        return f"- ⚠️ GCS enumeration failed: {exc}\n"


def jira_section() -> str:
    try:
        auth = (ENV.get("JIRA_USERNAME", ""), ENV.get("JIRA_API_TOKEN", ""))
        base = ENV.get("JIRA_URL", "").rstrip("/")
        with httpx.Client(timeout=30) as c:
            r = c.get(
                f"{base}/rest/api/3/search/jql",
                params={"jql": f"project={JIRA_PROJECT} ORDER BY key",
                        "fields": "summary,status,issuetype", "maxResults": 100},
                auth=auth, headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            issues = r.json().get("issues", [])
        if not issues:
            return f"- Project `{JIRA_PROJECT}` has no issues.\n"
        lines = [f"**Jira project `{JIRA_PROJECT}`** ({len(issues)} issues):\n"]
        for i in issues:
            f = i["fields"]
            lines.append(
                f"- `{i['key']}` ({f['issuetype']['name']}, **{f['status']['name']}**) — {f['summary']}"
            )
        return "\n".join(lines) + "\n"
    except Exception as exc:
        return f"- ⚠️ Jira enumeration failed: {exc}\n"


def confluence_section() -> str:
    try:
        auth = (ENV.get("CONFLUENCE_USERNAME", ""), ENV.get("CONFLUENCE_API_TOKEN", ""))
        base = ENV.get("CONFLUENCE_URL", "").rstrip("/")
        space = ENV.get("SANDBOX_SPACE_KEY", "")
        with httpx.Client(timeout=30) as c:
            r = c.get(
                f"{base}/rest/api/content",
                params={"spaceKey": space, "type": "page", "limit": 200, "expand": "version"},
                auth=auth, headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            pages = r.json().get("results", [])
        if not pages:
            return f"- Space `{space}` has no pages.\n"
        lines = [f"**Confluence space `{space}`** ({len(pages)} pages):\n"]
        for p in sorted(pages, key=lambda x: x["title"].lower()):
            lines.append(f"- `{p['id']}` — {p['title']}")
        return "\n".join(lines) + "\n"
    except Exception as exc:
        return f"- ⚠️ Confluence enumeration failed: {exc}\n"


def build_block() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"{BEGIN}\n"
        f"## Current inventory (auto-generated — do not edit by hand)\n\n"
        f"_Last refreshed: {now} by scripts/refresh_source_map.py. "
        f"Regenerated on schedule; edits here are overwritten._\n\n"
        f"### Google Cloud Storage\n\n{gcs_section()}\n"
        f"### Jira\n\n{jira_section()}\n"
        f"### Confluence\n\n{confluence_section()}\n"
        f"{END}"
    )


def update_memory(summary: str) -> None:
    """Best-effort: pin a one-line 'last refreshed' fact in OpenWorker memory."""
    try:
        from coworker.memory import SQLiteMemoryStore, Scope
        from coworker.secrets import state_dir
        store = SQLiteMemoryStore(state_dir() / "coworker.db")
        ws = str(ROOT)
        existing = {m.key: m for m in store.list(scope=Scope.WORKSPACE, workspace=ws) if m.key}
        key = "davita-inventory-refresh"
        if key in existing:
            store.update(existing[key].id, summary)
        else:
            store.add(summary, scope=Scope.WORKSPACE, key=key, workspace=ws)
    except Exception as exc:  # memory is a bonus; never fail the refresh over it
        print(f"(memory update skipped: {exc})", file=sys.stderr)


def main() -> int:
    if not AGENTS_MD.is_file():
        print(f"AGENTS.md not found at {AGENTS_MD}", file=sys.stderr)
        return 1
    text = AGENTS_MD.read_text()
    if BEGIN not in text or END not in text:
        print("AUTO-INVENTORY markers not found in AGENTS.md", file=sys.stderr)
        return 1
    block = build_block()
    pre = text.split(BEGIN)[0]
    post = text.split(END, 1)[1]
    AGENTS_MD.write_text(pre + block + post)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    update_memory(
        f"Source-map inventory last auto-refreshed {now}. Live counts and object/ticket/page "
        f"lists are in AGENTS.md under 'Current inventory'. Trust that block over any figures "
        f"hardcoded elsewhere."
    )
    print(f"AGENTS.md inventory refreshed at {now}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
