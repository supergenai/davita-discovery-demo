"""Human-in-the-loop socket.

Flagged mismatches are written to a review queue (ops.review_queue online, local
JSON offline). A human confirms/dismisses via the UI surface; on confirm the ELie
action fires. This is the L2 gate: the agent prepares, a human authorizes the email.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from .business_logic import Mismatch, Severity
from .config import offline
from .settings import get_settings
from .sinks import LOCAL_OUT, send_elie

log = logging.getLogger("factory.hitl")
QUEUE_FILE = LOCAL_OUT / "ops_review_queue.json"


def enqueue(agent: str, mismatches: list[Mismatch], min_severity: Severity = Severity.HIGH) -> list[dict[str, Any]]:
    """Push mismatches at/above min_severity onto the review queue."""
    order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}
    items = [
        {
            "review_id": str(uuid.uuid4()),
            "agent": agent,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **m.model_dump(),
        }
        for m in mismatches
        if order[m.severity] >= order[min_severity]
    ]
    if not items:
        return []
    if offline():
        LOCAL_OUT.mkdir(exist_ok=True)
        existing = json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else []
        existing.extend(items)
        QUEUE_FILE.write_text(json.dumps(existing, indent=2, default=str))
    else:
        from google.cloud import bigquery

        client = bigquery.Client(project=get_settings().project)
        client.insert_rows_json(f"{client.project}.ops.review_queue", items)
    log.info("hitl.enqueue: %d item(s) for %s", len(items), agent)
    return items


def list_pending() -> list[dict[str, Any]]:
    if offline():
        return [i for i in _load_local() if i.get("status") == "pending"]
    from google.cloud import bigquery

    client = bigquery.Client(project=get_settings().project)
    rows = client.query(
        f"SELECT * FROM `{client.project}`.ops.review_queue WHERE status='pending'"
    ).result()
    return [dict(r) for r in rows]


def resolve(review_id: str, decision: str, reviewer: str = "unknown") -> dict[str, Any]:
    """Confirm or dismiss a queued item. On 'confirm', fire the ELie email."""
    if decision not in {"confirm", "dismiss"}:
        raise ValueError("decision must be 'confirm' or 'dismiss'")
    item = _update_status(review_id, "confirmed" if decision == "confirm" else "dismissed", reviewer)
    if decision == "confirm" and item:
        send_elie(
            to=item.get("owner_email") or get_settings().elie_default_recipient,
            subject=f"[Data Quality] {item.get('kind')} needs correction",
            body=f"Reviewer {reviewer} confirmed: {item.get('detail')}",
        )
    return item or {}


def _load_local() -> list[dict[str, Any]]:
    return json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else []


def _update_status(review_id: str, status: str, reviewer: str) -> dict[str, Any] | None:
    if offline():
        items = _load_local()
        found = None
        for it in items:
            if it["review_id"] == review_id:
                it.update(status=status, reviewer=reviewer,
                          resolved_at=datetime.now(timezone.utc).isoformat())
                found = it
        QUEUE_FILE.write_text(json.dumps(items, indent=2, default=str))
        return found
    from google.cloud import bigquery

    client = bigquery.Client(project=get_settings().project)
    client.query(
        f"UPDATE `{client.project}`.ops.review_queue SET status=@s, reviewer=@r "
        f"WHERE review_id=@id",
        job_config=bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("s", "STRING", status),
            bigquery.ScalarQueryParameter("r", "STRING", reviewer),
            bigquery.ScalarQueryParameter("id", "STRING", review_id),
        ]),
    ).result()
    return {"review_id": review_id, "status": status, "reviewer": reviewer}
