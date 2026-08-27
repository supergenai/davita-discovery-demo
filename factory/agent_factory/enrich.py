"""LLM enrichment: Gemini explains and prioritizes the deterministic mismatches.

The LLM never decides a mismatch - it receives the rule-derived list and adds a
plain-language explanation + a suggested priority. Offline (no project) it uses a
deterministic template so the pipeline stays testable; online it calls Gemini.
"""

from __future__ import annotations

import logging
from typing import Any

from .business_logic import Mismatch
from .config import AgentSpec, offline
from .guardrails import deidentify

log = logging.getLogger("factory.enrich")


def explain(mismatches: list[Mismatch], spec: AgentSpec) -> list[dict[str, Any]]:
    """Return enriched result rows (mismatch + explanation + priority).

    Enrichment is best-effort: if Gemini is unavailable it falls back to the
    deterministic template so an LLM hiccup never blocks the DQ report.
    """
    if offline():
        return [_template_row(m) for m in mismatches]
    try:
        return _gemini_rows(mismatches, spec)
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemini enrichment failed (%s); using deterministic template", exc)
        return [_template_row(m) for m in mismatches]


_PRIORITY = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _row(m: Mismatch, explanation: str) -> dict[str, Any]:
    """Shape a result row to exactly the dq_results columns (drops the audit
    `sources` blob and coerces the enum), so it is BigQuery-insertable and
    consistent across the offline and online paths."""
    return {
        "kind": m.kind,
        "severity": m.severity.value,
        "employee_id": m.employee_id,
        "facility_id": m.facility_id,
        "detail": m.detail,
        "explanation": explanation,
        "priority": _PRIORITY[m.severity.value],
    }


def _template_row(m: Mismatch) -> dict[str, Any]:
    return _row(m, deidentify(f"{m.kind.replace('_', ' ').title()}: {m.detail}"))


def _gemini_rows(mismatches: list[Mismatch], spec: AgentSpec) -> list[dict[str, Any]]:  # pragma: no cover
    from google import genai
    from google.genai import types

    from .settings import get_settings

    s = get_settings()
    client = genai.Client(vertexai=True, project=s.project, location=s.region)
    context = spec.business_context.get("turnover_definition", "")
    rows: list[dict[str, Any]] = []
    for m in mismatches:
        prompt = (
            f"You are a data-quality analyst. Business context: {context}\n"
            f"A deterministic rule flagged this mismatch (do NOT re-decide it, only explain "
            f"and assign a priority 1-3):\n{deidentify(m.model_dump_json())}\n"
            f"Return one sentence explanation and a priority integer."
        )
        resp = client.models.generate_content(
            model=spec.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0),
        )
        rows.append(_row(m, resp.text.strip()))
    return rows
