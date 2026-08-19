# Demo prompts + run checklist

Rehearse all three at least twice. Have a recording as backup.

## Sharp queries that hit the seeded tensions (for Step 4b / recovery)
- **"no-show rate"** → surfaces the Glossary vs Ops Dashboard contradiction (two incompatible definitions).
- **"SMS reminder"** → surfaces the active SMS-only Epic vs the CLOSED spike (BP2, Won't Do) that argues against it.
- **Jira closed incl. spike:** JQL `project = BP2 AND status in (Done, Closed, Resolved)`.
- Confluence write target for demo #3: space **Davitademo**.

## 1. Framing (planning before action)
```
I'm a product owner scoping patient transport no-show reduction for regional clinics.
Before you search anything, tell me: what would you look for, in which systems, and
in what order? List the specific Confluence spaces and Jira projects you'd hit.
```
Pause: it hasn't touched a system yet — it's showing its plan.

## 2. Discovery run (the substance, 3–5 min)
```
Go. Search Confluence and Jira. Read the most relevant sources in full rather than
working from search snippets. Then give me three sections:

WHAT WE ALREADY KNOW — prior findings, pilots, research. Link every claim to its source.
WHAT'S ALREADY BUILT — existing services, closed spikes, prior decisions.
WHAT'S CONTESTED — contradictions between sources, competing definitions, assumptions in
current epics that conflict with earlier findings.

Flag anything you could not verify. Do not fill gaps with inference.
```
Narrate the tool calls while it works — the connector activity IS the demo.
Cap full-page reads (10–15, not 30) if context overflows.

## 3. Deliverable (the approval gate)
```
Draft this as a Confluence page in the <SANDBOX> space. Structure it with the three
sections above plus a gap table: open question, why it matters, suggested owner.
Also save a one-page executive brief as a file in my working directory.
Show me both for approval before you write anything.
```
When the approval gate appears, stop and point at it. That's the governance story.

## End-to-end checklist (run before the demo, not during)
- [ ] Server and GUI start clean from a cold boot
- [ ] Confluence search returns relevant results
- [ ] Full page fetch returns complete body, not snippets
- [ ] Jira search surfaces closed issues
- [ ] Agent produces at least one genuine contradiction / surprising finding
- [ ] Every claim carries a working source link
- [ ] Approval gate fires before the Confluence write
- [ ] Created page renders correctly — tables intact, no raw markup
- [ ] Brief file lands in working dir and opens
- [ ] Full run completes under 8 minutes
- [ ] A recorded backup of a successful run exists
