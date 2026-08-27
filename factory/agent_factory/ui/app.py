"""HITL review UI (the 'ui' surface). FastAPI app on Cloud Run.

Serves the review queue so a human can confirm/dismiss flagged mismatches; confirm
fires the ELie email. Works offline against the local queue too:

  uv run uvicorn agent_factory.ui.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import hitl

app = FastAPI(title="Davita DQ - HITL Review")

_PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>DQ Review Queue</title><style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem;color:#1a2430;background:#f4f6f9}}
h1{{color:#1F3A5F}} .item{{background:#fff;border:1px solid #e2e7ee;border-radius:8px;padding:14px 18px;margin:10px 0}}
.sev-HIGH{{border-left:5px solid #b3261e}} .sev-MEDIUM{{border-left:5px solid #C8892A}} .sev-LOW{{border-left:5px solid #0B7A75}}
.k{{font-weight:600;color:#1F3A5F}} button{{border:0;border-radius:6px;padding:7px 14px;cursor:pointer;color:#fff}}
.c{{background:#0B7A75}} .d{{background:#7a8794}} form{{display:inline;margin-left:8px}}
.empty{{color:#55606b}}</style></head><body>
<h1>Data Quality - Review Queue</h1>{body}</body></html>"""


def _render(items: list[dict]) -> str:
    if not items:
        return _PAGE.format(body='<p class="empty">No pending items. All clear.</p>')
    rows = []
    for it in items:
        rows.append(
            f'<div class="item sev-{it["severity"]}">'
            f'<div class="k">{it["kind"]} &middot; {it["severity"]} &middot; employee {it.get("employee_id")}</div>'
            f'<div>{it["detail"]}</div>'
            f'<form method="post" action="/resolve"><input type=hidden name=review_id value="{it["review_id"]}">'
            f'<input type=hidden name=decision value="confirm">'
            f'<button class="c">Confirm &rarr; email</button></form>'
            f'<form method="post" action="/resolve"><input type=hidden name=review_id value="{it["review_id"]}">'
            f'<input type=hidden name=decision value="dismiss"><button class="d">Dismiss</button></form>'
            f"</div>"
        )
    return _PAGE.format(body="".join(rows))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _render(hitl.list_pending())


@app.post("/resolve")
def resolve(review_id: str = Form(...), decision: str = Form(...)) -> RedirectResponse:
    hitl.resolve(review_id, decision, reviewer="ui-user")
    return RedirectResponse("/", status_code=303)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
