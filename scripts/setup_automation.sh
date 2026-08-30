#!/usr/bin/env bash
# Register the "Refresh source-map inventory" automation in a running OpenWorker server, and
# auto-allow the deterministic refresh command so scheduled runs don't park an approval.
#
# The automation lives in OpenWorker's automation.db (machine-local, not in this repo), so this
# script recreates it on a new machine. The server must be running (scripts/start_server.sh).
set -uo pipefail

ROOT="$HOME/davita-discovery-demo"
CONF_DIR="$HOME/.config/coworker"
CMD="bash $ROOT/scripts/refresh_source_map.sh"

TOKEN=$(grep -E '^COWORKER_API_TOKEN=' "$ROOT/.env" | cut -d= -f2-)
[ -z "$TOKEN" ] && { echo "COWORKER_API_TOKEN not in .env"; exit 1; }

# 1) Auto-allow the exact refresh command (global config; prefix/argv match, shell operators rejected).
mkdir -p "$CONF_DIR"
if ! grep -q "refresh_source_map.sh" "$CONF_DIR/config.toml" 2>/dev/null; then
  {
    echo '# Auto-allow the deterministic source-map refresh for unattended automation runs.'
    echo "allowed_commands = [\"$CMD\"]"
  } >> "$CONF_DIR/config.toml"
  echo "added allowed_commands to $CONF_DIR/config.toml"
else
  echo "allowed_commands already present"
fi

# 2) Create the automation (every 30 min). Skip if a task with this title already exists.
EXISTS=$(curl -s -H "x-openworker-token: $TOKEN" http://127.0.0.1:8765/v1/automations \
  | python3 -c "import sys,json;d=json.load(sys.stdin);t=d if isinstance(d,list) else d.get('tasks',[]);print(any(x.get('title')=='Refresh source-map inventory' for x in t))" 2>/dev/null)

if [ "$EXISTS" = "True" ]; then
  echo "automation already exists — skipping create"
else
  curl -s -X POST -H "x-openworker-token: $TOKEN" -H "content-type: application/json" \
    http://127.0.0.1:8765/v1/automations \
    -d '{
      "title": "Refresh source-map inventory",
      "instructions": "Run this exact shell command, verbatim, with no additions, no redirection, and no chaining operators:\n\nbash '"$ROOT"'/scripts/refresh_source_map.sh\n\nThis regenerates the auto-inventory in AGENTS.md by enumerating the connected sources. After it exits, briefly report the exit status and the last line of its output. Do not edit any files yourself.",
      "cron": "*/30 * * * *",
      "timezone": "local"
    }' | python3 -c "import sys,json;d=json.load(sys.stdin);print('created:', d.get('ok'), (d.get('task') or {}).get('id',''))"
fi
