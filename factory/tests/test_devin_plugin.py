"""Deterministic tests for the Devin plugin skills + MCP tool registration."""

from __future__ import annotations

import asyncio

from agent_factory.devin import skills
from agent_factory.devin.retriever import LocalRetriever


def test_retriever_finds_relevant_passage():
    hits = LocalRetriever().retrieve("no-show rate definition baseline")
    assert any(h.source.endswith("no_show_rate.md") for h in hits)


def test_business_context_returns_turnover_rule():
    out = skills.get_business_context("admin turnover Workday source of truth")
    assert any("admin_turnover" in p["source"] for p in out["passages"])


def test_flag_conflicts_catches_sms_only():
    out = skills.flag_conflicts("Proposal: roll out an SMS-only reminder for transport no-shows.")
    assert out["has_conflicts"] is True
    assert out["conflicts"][0]["decision_id"] == "BP2-1"
    assert out["conflicts"][0]["matched_signal"] in ("sms-only", "sms only")


def test_flag_conflicts_benign_proposal_is_clean():
    out = skills.flag_conflicts("Proposal: add a nightly export of the roster dimension.")
    assert out["has_conflicts"] is False


def test_adk_best_practices_reviews_code():
    code = (
        'client = bigquery.Client(project="davita-agent-demo-2023")\n'
        'resp = client.models.generate_content(model, "decide which record is correct")\n'
    )
    out = skills.adk_best_practices(topic="determinism", code=code)
    rules = {f["rule"] for f in out["findings"]}
    assert "BP-NOHARDCODE" in rules
    assert "BP-DETERMINISM" in rules
    assert out["guidance"]  # returned relevant standards


def test_review_code_flags_secret_and_bare_except():
    code = 'api_key = "sk-abcd1234efgh5678ijkl"\ntry:\n    x()\nexcept:\n    pass\n'
    out = skills.review_code(code, path="x.py")
    rules = {f["rule"] for f in out["findings"]}
    assert "SEC-SECRET" in rules
    assert "PY-BAREEXCEPT" in rules


def test_check_infra_flags_hardcoded_project_and_version():
    tf = (
        'terraform {\n}\n'
        'resource "google_bigquery_dataset" "x" {\n'
        '  project_id = "davita-agent-demo-2023"\n'
        '}\n'
    )
    out = skills.check_infra(tf, filename="main.tf")
    rules = {f["rule"] for f in out["findings"]}
    assert "TF-HARDCODE" in rules
    assert "TF-VERSION" in rules


def test_suggest_tests_covers_functions_and_decision_logic():
    code = "def reconcile(a, b):\n    return a\n\ndef helper(x):\n    return x\n"
    out = skills.suggest_tests(code)
    assert out["function_count"] == 2
    assert any("known-good" in s for s in out["suggestions"])


def test_mcp_server_registers_all_tools():
    from agent_factory.devin.server import mcp
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {
        "get_business_context", "flag_conflicts", "adk_best_practices",
        "review_code", "check_infra", "suggest_tests",
    }
