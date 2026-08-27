"""Factory + pipeline wiring, offline."""

from __future__ import annotations

import json
from pathlib import Path

from agent_factory import AgentSpec, run_pipeline
from agent_factory.config import Autonomy, Surface

CONFIG = Path(__file__).resolve().parent.parent / "agents" / "admin_turnover_dq" / "config.yaml"


def test_spec_loads_and_parses():
    spec = AgentSpec.load(CONFIG)
    assert spec.name == "admin_turnover_dq"
    assert spec.surface == Surface.BACKGROUND
    assert spec.autonomy == Autonomy.L2
    assert set(spec.sources) == {"mdm", "workday", "cwow"}
    assert spec.action.hitl_review is True


def test_pipeline_runs_and_writes_results(tmp_path, monkeypatch):
    # isolate local outputs to a temp dir
    import agent_factory.sinks as sinks
    import agent_factory.hitl as hitl
    monkeypatch.setattr(sinks, "LOCAL_OUT", tmp_path)
    monkeypatch.setattr(hitl, "LOCAL_OUT", tmp_path)
    monkeypatch.setattr(hitl, "QUEUE_FILE", tmp_path / "ops_review_queue.json")

    spec = AgentSpec.load(CONFIG)
    summary = run_pipeline(spec)

    assert summary["mismatches"] == 4
    assert summary["review_queued"] == 1  # only the HIGH one
    results = json.loads((tmp_path / "dq_results_admin_turnover.json").read_text())
    assert len(results) == 4
    assert all("explanation" in r and "priority" in r for r in results)


def test_build_agent_requires_adk():
    # build_agent constructs a real ADK agent; just assert it wires without a live model call.
    from agent_factory import build_agent
    spec = AgentSpec.load(CONFIG)
    agent = build_agent(spec)
    assert agent.name == "admin_turnover_dq"
    assert len(agent.tools) == 6  # 3 sources + bigquery_write + looker + elie
