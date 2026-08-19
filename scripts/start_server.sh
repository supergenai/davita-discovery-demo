#!/usr/bin/env bash
# Launch the OpenWorker agent server with credentials in its environment.
# - ANTHROPIC_API_KEY comes from MODEL_API_KEY in .env (OpenWorker auto-configures
#   Claude via the provider env_key fallback — no GUI paste needed).
# - Atlassian vars are exported too (belt-and-suspenders; they also resolve from
#   ~/.config/coworker/.env for the MCP servers).
# Secrets are never echoed.
set -uo pipefail

ROOT="$HOME/davita-discovery-demo"
VENV="$ROOT/openworker/.venv"
ENV_FILE="$ROOT/.env"

[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE"; exit 1; }

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export ANTHROPIC_API_KEY="${MODEL_API_KEY:-}"

# Stop any server already on 8765 so we start clean.
lsof -ti tcp:8765 2>/dev/null | xargs -r kill 2>/dev/null

mkdir -p "$ROOT/logs"
nohup "$VENV/bin/openworker-server" --cwd "$ROOT" --port 8765 \
  > "$ROOT/logs/server.log" 2>&1 &
echo "server starting (pid $!) — log: $ROOT/logs/server.log"
