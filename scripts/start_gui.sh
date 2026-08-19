#!/usr/bin/env bash
# Launch the OpenWorker GUI (vite dev) wired to the server's fixed sidecar token.
# VITE_COWORKER_API_TOKEN must equal the server's COWORKER_API_TOKEN (both from .env),
# so the browser GUI authenticates regardless of start order or server restarts.
set -uo pipefail

ROOT="$HOME/davita-discovery-demo"
GUI="$ROOT/openworker/surfaces/gui"
ENV_FILE="$ROOT/.env"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export VITE_COWORKER_API_TOKEN="${COWORKER_API_TOKEN:-}"

# Stop any GUI already on 1420.
lsof -ti tcp:1420 2>/dev/null | xargs -r kill 2>/dev/null

mkdir -p "$ROOT/logs"
cd "$GUI"
nohup npm run dev > "$ROOT/logs/gui.log" 2>&1 &
echo "GUI starting (pid $!) — http://localhost:1420  (log: $ROOT/logs/gui.log)"
