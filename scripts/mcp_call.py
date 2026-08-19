#!/usr/bin/env python3
"""Drive mcp-atlassian over stdio: dump schemas for key tools + one live read call
to confirm credentials authenticate. Prints no secrets."""
import json, subprocess, sys, threading, time

ENV_FILE = sys.argv[1]
cmd = ["uvx", "mcp-atlassian", "--transport", "stdio", "-v", "--env-file", ENV_FILE]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, bufsize=1)
errlog = []
threading.Thread(target=lambda: [errlog.append(l.rstrip()) for l in proc.stderr], daemon=True).start()

def send(o): proc.stdin.write(json.dumps(o)+"\n"); proc.stdin.flush()
def wait(_id, timeout=45):
    end=time.time()+timeout
    while time.time()<end:
        line=proc.stdout.readline()
        if not line: return None
        line=line.strip()
        if not line: continue
        try: m=json.loads(line)
        except json.JSONDecodeError: continue
        if m.get("id")==_id: return m
    return None

send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"0.0"}}})
wait(1)
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
res=wait(2)
tools={t["name"]:t for t in res["result"]["tools"]} if res and "result" in res else {}

def schema_of(name):
    t=tools.get(name)
    if not t: return f"(tool {name} not found)"
    props=(t.get("inputSchema",{}) or {}).get("properties",{})
    req=set((t.get("inputSchema",{}) or {}).get("required",[]))
    out=[]
    for k,v in props.items():
        d=(v.get("description","") or "").replace("\n"," ")
        if len(d)>90: d=d[:87]+"..."
        star="*" if k in req else " "
        enum=f" enum={v['enum']}" if "enum" in v else ""
        out.append(f"    {star}{k} ({v.get('type','?')}){enum}: {d}")
    return "\n".join(out) or "    (no params)"

print("=== jira search tool names present ===")
print([n for n in tools if "search" in n and n.startswith("jira")])
for name in ["jira_search","confluence_search","confluence_get_page","confluence_create_page"]:
    print(f"\n### {name}\n"+schema_of(name))

# Live auth check: list Jira projects (read-only)
print("\n=== LIVE READ: jira_get_all_projects ===")
send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jira_get_all_projects","arguments":{}}})
r=wait(3)
if r and "result" in r:
    content=r["result"].get("content",[])
    txt=""
    for c in content:
        if c.get("type")=="text": txt+=c["text"]
    try:
        data=json.loads(txt)
        if isinstance(data,list):
            print(f"AUTH OK — {len(data)} project(s):")
            for p in data[:10]:
                print(f"  - {p.get('key')}: {p.get('name')}")
        else:
            print("AUTH OK — response:", txt[:300])
    except Exception:
        print("AUTH OK — raw:", txt[:400])
elif r and "error" in r:
    print("AUTH/CALL ERROR:", json.dumps(r["error"])[:400])
else:
    print("No response.")

print("\n=== connection log (first 12 stderr lines) ===")
for l in errlog[:12]:
    print(l)
try: proc.terminate()
except Exception: pass
