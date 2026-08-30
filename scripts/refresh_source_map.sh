#!/usr/bin/env bash
# Wrapper for the source-map refresh so it runs identically by hand, from cron, or from launchd.
# launchd/cron give a minimal PATH, so we set it explicitly (gcloud lives in /opt/homebrew/bin)
# and use the OpenWorker venv python (has httpx + the coworker memory module).
set -uo pipefail

ROOT="$HOME/davita-discovery-demo"
PY="$ROOT/openworker/.venv/bin/python"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$ROOT/logs"
echo "=== refresh $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$ROOT/logs/refresh.log"
"$PY" "$ROOT/scripts/refresh_source_map.py" >> "$ROOT/logs/refresh.log" 2>&1
echo "exit=$?" >> "$ROOT/logs/refresh.log"
