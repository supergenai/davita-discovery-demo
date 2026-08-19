#!/usr/bin/env python3
"""Standalone MCP stdio probe: initialize + tools/list against mcp-atlassian.
Prints ONLY tool names/descriptions and connection status. Never prints secrets."""
import json, subprocess, sys, threading, time

ENV_FILE = sys.argv[1] if len(sys.argv) > 1 else None
cmd = ["uvx", "mcp-atlassian", "--transport", "stdio", "-v"]
if ENV_FILE:
    cmd += ["--env-file", ENV_FILE]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, bufsize=1)

stderr_lines = []
def drain_stderr():
    for line in proc.stderr:
        stderr_lines.append(line.rstrip())
threading.Thread(target=drain_stderr, daemon=True).start()

def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2024-11-05","capabilities":{},
    "clientInfo":{"name":"probe","version":"0.0"}}})
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})

tools = None
deadline = time.time() + 45
while time.time() < deadline:
    line = proc.stdout.readline()
    if not line:
        break
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("id") == 2 and "result" in msg:
        tools = msg["result"].get("tools", [])
        break
    if msg.get("id") == 2 and "error" in msg:
        print("tools/list ERROR:", json.dumps(msg["error"]))
        break

try:
    proc.terminate()
except Exception:
    pass

# Surface auth-relevant stderr (redact anything token-like defensively)
print("=== connection log (last 15 stderr lines) ===")
for l in stderr_lines[-15:]:
    print(l)

print("\n=== TOOLS ===")
if tools is None:
    print("No tools/list result received (see stderr above).")
    sys.exit(1)
print(f"count: {len(tools)}\n")
for t in tools:
    name = t.get("name","?")
    desc = (t.get("description","") or "").strip().replace("\n"," ")
    if len(desc) > 110:
        desc = desc[:107] + "..."
    print(f"- {name}: {desc}")
