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
    """Return enriched result rows (mismatch + explanation + priority)."""
    if offline():
        return [_template_row(m) for m in mismatches]
    return _gemini_rows(mismatches, spec)


def _template_row(m: Mismatch) -> dict[str, Any]:
    priority = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}[m.severity.value]
    return {
        **m.model_dump(),
        "explanation": deidentify(
            f"{m.kind.replace('_', ' ').title()}: {m.detail}"
        ),
        "priority": priority,
    }


def _gemini_rows(mismatches: list[Mismatch], spec: AgentSpec) -> list[dict[str, Any]]:  # pragma: no cover
    from google import genai
    from google.genai import types

    client = genai.Client()  # picks up Vertex/GOOGLE_* env
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
        rows.append({**m.model_dump(), "explanation": resp.text.strip(),
                     "priority": {"HIGH": 1, "MEDIUM": 2, "LOW": 3}[m.severity.value]})
    return rows
