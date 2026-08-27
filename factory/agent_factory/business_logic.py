"""Business-logic socket: deterministic reconciliation primitives.

The MATCH is code, never the LLM. A spoke supplies a `reconcile(sources)` function
(see agents/*/rules.py) that returns a list of Mismatch records. Gemini later only
explains and prioritizes these - it does not decide them. This keeps HR-adjacent
determinations auditable.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from typing import Any

from pydantic import BaseModel


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Mismatch(BaseModel):
    kind: str                       # e.g. "terminated_but_active"
    severity: Severity
    employee_id: str | None = None
    facility_id: str | None = None
    detail: str                     # human-readable, rule-derived (not LLM)
    sources: dict[str, Any] = {}    # the raw values that triggered it, for audit


def index_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Index rows by a key column (last wins on dupes)."""
    return {str(r[key]): r for r in rows if r.get(key) not in (None, "")}


def group_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(str(r.get(key, "")), []).append(r)
    return out
