"""Background execution path: the deterministic Retrieve -> Reconcile -> Report run.

This is what the scheduled/Agent-Engine trigger invokes. It is fully deterministic
(no LLM needed for the match), so it is unit-testable offline. The LLM only enriches
the already-decided mismatches. The factory's ADK agent (factory.py) wraps this same
logic for the interactive/UI surface.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Callable

from .business_logic import Mismatch
from .config import AgentSpec
from .enrich import explain
from .hitl import enqueue
from .sinks import refresh_looker, write_results
from .sources import read_source

log = logging.getLogger("factory.pipeline")


def _load_reconcile(dotted: str) -> Callable[[dict[str, list[dict]]], list[Mismatch]]:
    """Import the spoke's reconcile() callable from 'module:function'."""
    mod_name, func_name = dotted.split(":")
    return getattr(importlib.import_module(mod_name), func_name)


def run(spec: AgentSpec) -> dict[str, Any]:
    """Execute the full pipeline for a spec. Returns a run summary."""
    # 1. Retrieve
    sources = {name: read_source(name) for name in spec.sources}
    log.info("retrieved %s", {k: len(v) for k, v in sources.items()})

    # 2. Reconcile (deterministic, auditable)
    if not spec.rules:
        raise ValueError(f"spec '{spec.name}' has no rules: reconcile path")
    reconcile = _load_reconcile(spec.rules)
    mismatches: list[Mismatch] = reconcile(sources)
    log.info("reconcile found %d mismatch(es)", len(mismatches))

    # 3. Enrich (LLM explains/prioritizes; never decides)
    rows = explain(mismatches, spec)

    # 4. Report / act
    summary: dict[str, Any] = {"agent": spec.name, "mismatches": len(mismatches)}
    if spec.action.write_bigquery and rows:
        summary["written"] = write_results(spec.action.write_bigquery, rows)
    if spec.action.refresh_looker:
        summary["looker"] = refresh_looker(f"{spec.name}_dashboard")
    if spec.action.hitl_review:
        queued = enqueue(spec.name, mismatches)
        summary["review_queued"] = len(queued)
    return summary
