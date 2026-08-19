#!/usr/bin/env bash
# Part 2, Step 6 — teardown. Stops the demo, leaves credentials and notes in place.
set -uo pipefail

echo "Stopping OpenWorker server (port 8765) and GUI dev server..."
lsof -ti tcp:8765 2>/dev/null | xargs -r kill 2>/dev/null   # agent server
lsof -ti tcp:1420 2>/dev/null | xargs -r kill 2>/dev/null   # GUI (vite, Tauri default port)

echo "Killing any stray uvx mcp-atlassian processes..."
pkill -f "mcp-atlassian" 2>/dev/null

cat <<'EOF'

Teardown done. Not removed (do these by hand if you want a clean slate):
  - ~/davita-discovery-demo/openworker         (cloned source)
  - ~/davita-discovery-demo/briefs             (generated briefs)
  - the "MCP write test — delete me" page in the sandbox space, if step 5 ran
  - your Atlassian API token — revoke at id.atlassian.com if this was a one-off
EOF
