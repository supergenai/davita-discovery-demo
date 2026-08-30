"""Recorded-decision registry + conflict detection.

Deterministic: a proposal conflicts with a recorded decision when any of that decision's
conflict_signals (lowercased substrings) appears in the proposal text. This is auditable and
explainable, and it is only as good as the curated registry (knowledge/decisions/registry.yaml) -
a business input, not something the model invents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parents[2] / "knowledge" / "decisions" / "registry.yaml"


@dataclass
class Conflict:
    decision_id: str
    topic: str
    status: str
    ruling: str
    source: str
    matched_signal: str


def load_decisions(path: Path = REGISTRY) -> list[dict]:
    return yaml.safe_load(path.read_text()) or []


def flag_conflicts(proposal: str, decisions: list[dict] | None = None) -> list[Conflict]:
    """Return recorded decisions the proposal appears to contradict."""
    text = proposal.lower()
    decisions = decisions if decisions is not None else load_decisions()
    hits: list[Conflict] = []
    for d in decisions:
        for signal in d.get("conflict_signals", []):
            if signal.lower() in text:
                hits.append(Conflict(
                    decision_id=d["id"], topic=d.get("topic", ""),
                    status=d.get("status", ""), ruling=(d.get("ruling", "") or "").strip(),
                    source=d.get("source", ""), matched_signal=signal,
                ))
                break  # one hit per decision is enough
    return hits
