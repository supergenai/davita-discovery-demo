"""Action/output sinks. Offline they write to factory/.local_out/*.json + log so the
whole pipeline is verifiable without GCP. With a project they write to BigQuery.
ELie (Outlook email) and Looker are STUBS with a clearly marked integration seam.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import offline

log = logging.getLogger("factory.sinks")
LOCAL_OUT = Path(__file__).resolve().parent.parent / ".local_out"


def _local_append(name: str, rows: list[dict[str, Any]]) -> Path:
    LOCAL_OUT.mkdir(exist_ok=True)
    path = LOCAL_OUT / f"{name}.json"
    existing = json.loads(path.read_text()) if path.exists() else []
    existing.extend(rows)
    path.write_text(json.dumps(existing, indent=2, default=str))
    return path


def _bq_insert(table: str, rows: list[dict[str, Any]]) -> None:
    from google.cloud import bigquery

    from .settings import get_settings

    client = bigquery.Client(project=get_settings().project)
    errors = client.insert_rows_json(table, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors for {table}: {errors}")


def write_results(table: str, rows: list[dict[str, Any]]) -> str:
    """Persist DQ results (BigQuery online, local JSON offline)."""
    if not rows:
        return "no rows"
    if offline():
        p = _local_append(table.replace(".", "_"), rows)
        log.info("write_results offline -> %s (%d rows)", p, len(rows))
        return str(p)
    _bq_insert(table, rows)
    return f"{table} (+{len(rows)} rows)"


def refresh_looker(dashboard: str) -> str:
    """STUB. Real integration seam: call the Looker API to refresh/rebuild.
    For the prototype the results table + review UI ARE the dashboard."""
    log.info("[STUB] refresh_looker(%s)", dashboard)
    return f"looker refresh stubbed for {dashboard}"


def send_elie(to: str, subject: str, body: str) -> str:
    """STUB for ELie (sends an Outlook email). Records the payload to
    ops.sent_emails (or local) so the HITL loop is verifiable end-to-end.
    Real integration seam: POST to the ELie service."""
    payload = {
        "to": to,
        "subject": subject,
        "body": body,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "channel": "ELie(Outlook)[STUB]",
    }
    if offline():
        _local_append("ops_sent_emails", [payload])
    else:
        from .settings import get_settings

        _bq_insert(f"{get_settings().project}.ops.sent_emails", [payload])
    log.info("[STUB] send_elie -> %s | %s", to, subject)
    return f"email queued to {to} (stub)"
