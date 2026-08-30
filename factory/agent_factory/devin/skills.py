"""The Devin-facing skills. Plain functions with deterministic cores so they are testable and
auditable; Devin (as an MCP client) calls the tool wrappers in server.py. The hard checks are
regex/rule based; retrieval adds the relevant standards and context. Autonomy L1: these review,
flag, and suggest. They never modify or merge code.
"""

from __future__ import annotations

import re
from typing import Any

from .decisions import flag_conflicts as _flag_conflicts
from .retriever import LocalRetriever

_retriever = LocalRetriever()

# --- shared deterministic detectors -------------------------------------------------

_SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9]{16,}", "hardcoded API key"),
    (r"AKIA[0-9A-Z]{16}", "hardcoded AWS access key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "embedded private key"),
    (r"(?i)(password|api_key|secret|token)\s*[:=]\s*[\"'][^\"']{6,}[\"']", "hardcoded credential"),
]
# a project-id-like literal, e.g. "davita-agent-demo-2023"
_HARDCODED_PROJECT = re.compile(r"[\"'][a-z][a-z0-9-]{4,}-\d{2,}[\"']")


def _lines(text: str) -> list[str]:
    return text.splitlines()


def _scan(text: str, pattern: re.Pattern | str, rule: str, severity: str, message: str) -> list[dict]:
    rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    out = []
    for i, line in enumerate(_lines(text), 1):
        if rx.search(line):
            out.append({"rule": rule, "severity": severity, "line": i, "message": message,
                        "snippet": line.strip()[:120]})
    return out


# --- skills -------------------------------------------------------------------------

def get_business_context(topic: str, k: int = 4) -> dict[str, Any]:
    """Retrieve the documented business rules/definitions relevant to a topic."""
    passages = _retriever.retrieve(topic, k=k)
    return {"topic": topic, "passages": [
        {"source": p.source, "heading": p.heading, "text": p.text, "score": p.score}
        for p in passages
    ]}


def flag_conflicts(proposal: str) -> dict[str, Any]:
    """Flag where a proposed change/decision contradicts a recorded decision."""
    conflicts = _flag_conflicts(proposal)
    return {"has_conflicts": bool(conflicts), "conflicts": [
        {"decision_id": c.decision_id, "topic": c.topic, "status": c.status,
         "ruling": c.ruling, "source": c.source, "matched_signal": c.matched_signal}
        for c in conflicts
    ]}


def adk_best_practices(topic: str = "", code: str = "") -> dict[str, Any]:
    """Return the ADK standards relevant to a topic, and review agent code against them."""
    guidance = [
        {"heading": p.heading, "text": p.text, "source": p.source}
        for p in _retriever.retrieve((topic or "adk agent best practices") + " adk", k=5)
        if p.source == "adk_best_practices.md"
    ]
    findings: list[dict] = []
    if code:
        findings += _scan(code, _HARDCODED_PROJECT, "BP-NOHARDCODE", "high",
                          "hardcoded project/env literal; read it from settings/env")
        if re.search(r"(?i)(generate_content|\.run\()", code) and \
           re.search(r"(?i)(decide|determine|which is correct|do the match)", code):
            findings.append({"rule": "BP-DETERMINISM", "severity": "high", "line": 0,
                             "message": "LLM appears to make the determination; the match must be "
                                        "deterministic code, the model only explains", "snippet": ""})
        if re.search(r"(?i)llmagent\(", code) and "before_tool_callback" not in code:
            findings.append({"rule": "BP-GUARDRAILS", "severity": "medium", "line": 0,
                             "message": "LlmAgent built without a guardrail before_tool_callback",
                             "snippet": ""})
        if re.search(r"(?i)(def run|pipeline|agent)", code) and not re.search(r"(?i)eval|ground.?truth", code):
            findings.append({"rule": "BP-EVAL", "severity": "low", "line": 0,
                             "message": "no reference to an eval / ground-truth set", "snippet": ""})
    return {"guidance": guidance, "findings": findings}


def review_code(code: str, path: str = "") -> dict[str, Any]:
    """Deterministic code review: secrets, hardcoded env, debugging, unsafe patterns."""
    findings: list[dict] = []
    for pat, msg in _SECRET_PATTERNS:
        findings += _scan(code, pat, "SEC-SECRET", "high", f"possible {msg}")
    findings += _scan(code, _HARDCODED_PROJECT, "ENV-HARDCODE", "medium",
                      "hardcoded project/env literal")
    findings += _scan(code, r"(?i)#\s*(todo|fixme|xxx)", "MAINT-TODO", "low", "unresolved TODO/FIXME")
    findings += _scan(code, r"^\s*except\s*:", "PY-BAREEXCEPT", "medium", "bare except hides errors")
    findings += _scan(code, r"(?<![A-Za-z_])(eval|exec)\s*\(", "PY-EVAL", "high", "eval/exec is unsafe")
    if path.endswith(".py"):
        findings += _scan(code, r"^\s*print\(", "PY-PRINT", "low", "print() left in non-test code")
    findings.sort(key=lambda f: {"high": 0, "medium": 1, "low": 2}[f["severity"]])
    return {"path": path, "finding_count": len(findings), "findings": findings}


def check_infra(content: str, filename: str = "") -> dict[str, Any]:
    """Terraform + CI/CD conventions check."""
    findings: list[dict] = []
    if filename.endswith(".tf") or "resource \"" in content or "terraform {" in content:
        findings += _scan(content, r"project_id\s*=\s*\"[^\"$]+\"", "TF-HARDCODE", "high",
                          "project_id is a literal; use a variable")
        if "terraform {" in content and "required_version" not in content:
            findings.append({"rule": "TF-VERSION", "severity": "medium", "line": 0,
                             "message": "terraform block missing required_version", "snippet": ""})
        if re.search(r'resource\s+"google_', content) and "labels" not in content:
            findings.append({"rule": "TF-LABELS", "severity": "low", "line": 0,
                             "message": "google_* resource without labels (cost attribution)", "snippet": ""})
    if re.search(r"(?i)(gitlab-ci|cloudbuild|\.ya?ml$)", filename) or "stages:" in content:
        if not re.search(r"(?i)(pytest|test|lint)", content):
            findings.append({"rule": "CI-NOTEST", "severity": "medium", "line": 0,
                             "message": "pipeline has no visible test/lint step", "snippet": ""})
    return {"filename": filename, "finding_count": len(findings), "findings": findings}


def suggest_tests(code: str) -> dict[str, Any]:
    """Suggest tests for a change: one per function plus edge cases and, for decision logic,
    known-good / known-bad fixtures."""
    funcs = re.findall(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code, flags=re.MULTILINE)
    suggestions = [f"test {fn}: happy path + empty/None input + boundary" for fn in funcs]
    if re.search(r"(?i)(reconcile|classify|determine|match|rule)", code):
        suggestions.append("decision logic present: add a labeled known-good and known-bad fixture "
                           "and assert exact classifications")
    if not suggestions:
        suggestions.append("no functions detected; add at least one behavior test for the change")
    return {"function_count": len(funcs), "suggestions": suggestions}
