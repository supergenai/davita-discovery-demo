#!/usr/bin/env python3
"""Load seed content into Confluence (Davitademo) and Jira (BP2) via mcp-atlassian over stdio.
Reads creds from ../.env via --env-file. Creates pages + issues; tries to close the spike.
Run ONLY with the user's go-ahead — this writes to live Atlassian (sandbox space/project).

Usage: python3 seed/seed_load.py            # dry-run: prints what it WOULD create
       python3 seed/seed_load.py --apply    # actually create
"""
import json, subprocess, sys, threading, time, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "seed" / "seed_manifest.json").read_text())
ENV_FILE = str(ROOT / ".env")
APPLY = "--apply" in sys.argv

if not APPLY:
    print("DRY RUN (no --apply). Would create:")
    print(f"  {len(MANIFEST['confluence_pages'])} Confluence pages in space {MANIFEST['space_key']}")
    for p in MANIFEST["confluence_pages"]:
        print(f"    - {p['title']}")
    print(f"  {len(MANIFEST['jira_issues'])} Jira issues in project {MANIFEST['jira_project']}")
    for i in MANIFEST["jira_issues"]:
        extra = f" (=> {i.get('target_status')}/{i.get('target_resolution','')})".rstrip("/ ")
        print(f"    - [{i['issuetype']}] {i['summary']}{extra}")
    print("\nRe-run with --apply to create. Requires go-ahead.")
    sys.exit(0)

cmd = ["uvx", "mcp-atlassian", "--transport", "stdio", "--env-file", ENV_FILE]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, bufsize=1)
threading.Thread(target=lambda: [None for _ in proc.stderr], daemon=True).start()
_id = [0]
def send(method, params=None, notify=False):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None: msg["params"] = params
    if not notify:
        _id[0] += 1; msg["id"] = _id[0]
    proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()
    return msg.get("id")
def wait(_want, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        line = proc.stdout.readline()
        if not line: return None
        line = line.strip()
        if not line: continue
        try: m = json.loads(line)
        except json.JSONDecodeError: continue
        if m.get("id") == _want: return m
    return None
def call(tool, args):
    i = send("tools/call", {"name": tool, "arguments": args})
    r = wait(i)
    if not r: return None, "no response"
    if "error" in r: return None, json.dumps(r["error"])[:300]
    txt = "".join(c.get("text", "") for c in r["result"].get("content", []) if c.get("type") == "text")
    try: return json.loads(txt), None
    except Exception: return txt, None

send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "seed", "version": "0.0"}}); wait(1)
send("notifications/initialized", notify=True)

space = MANIFEST["space_key"]
print(f"=== Confluence pages -> {space} ===")
for p in MANIFEST["confluence_pages"]:
    res, err = call("confluence_create_page", {
        "space_key": space, "title": p["title"],
        "content": p["body"], "content_format": "markdown"})
    if err: print(f"  FAIL {p['title']}: {err}")
    elif isinstance(res, dict):
        pid = res.get("page_id") or res.get("id") or "?"
        url = res.get("url") or res.get("_links", {}).get("webui", "")
        print(f"  ok   {p['title']}  id={pid} {url}")
    else:
        print(f"  ok   {p['title']}  -> {str(res)[:160]}")

if "--no-jira" in sys.argv:
    print("\n(skipping Jira — --no-jira)")
    try: proc.terminate()
    except Exception: pass
    sys.exit(0)

proj = MANIFEST["jira_project"]
print(f"\n=== Jira issues -> {proj} ===")
made = {}
for it in MANIFEST["jira_issues"]:
    res, err = call("jira_create_issue", {
        "project_key": proj, "issue_type": it["issuetype"], "summary": it["summary"],
        "description": it["description"]})
    if err: print(f"  FAIL {it['summary']}: {err}"); continue
    if isinstance(res, dict):
        key = res.get("key") or res.get("issue", {}).get("key") or "?"
    else:
        import re as _re
        m = _re.search(rf"{proj}-\d+", str(res)); key = m.group(0) if m else "?"
    made[it["key_hint"]] = key
    print(f"  ok   [{it['issuetype']}] {key}  {it['summary']}")
    # Close the spike if requested
    if it.get("target_status") == "Done":
        tr, terr = call("jira_get_transitions", {"issue_key": key})
        print(f"       transitions: {tr if not terr else terr}")
        print(f"       -> transition {key} to Done manually if not auto-applied "
              f"(resolution {it.get('target_resolution','Done')}).")

print("\nDone. If any Jira transition to Done/Won't-Do didn't apply, set it in the Jira UI.")
try: proc.terminate()
except Exception: pass
