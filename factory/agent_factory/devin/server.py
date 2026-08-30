"""MCP server that publishes the Devin skills as tools.

Devin acts as an MCP client and calls these at runtime (verified against Devin's MCP support), so
it builds code aware of business context, recorded decisions, ADK standards, and infra conventions.
Same skill code also backs a CI/CD reviewer.

Run locally over stdio:            uv run python -m agent_factory.devin.server
Run as a hosted HTTP server:       uv run python -m agent_factory.devin.server --http   (Cloud Run)

Tools (all read-only, advisory L1):
  get_business_context, flag_conflicts, adk_best_practices, review_code, check_infra, suggest_tests
"""

from __future__ import annotations

import sys

from mcp.server.mcpserver import MCPServer

from . import skills

mcp = MCPServer("davita-devin-plugin")


@mcp.tool()
def get_business_context(topic: str) -> dict:
    """Retrieve the documented business rules and definitions relevant to a topic
    (from Confluence/knowledge). Call this before implementing anything with business meaning."""
    return skills.get_business_context(topic)


@mcp.tool()
def flag_conflicts(proposal: str) -> dict:
    """Check a proposed change or decision against the recorded-decision registry and flag any
    contradiction with a decision that is already made. Call this before committing to an approach."""
    return skills.flag_conflicts(proposal)


@mcp.tool()
def adk_best_practices(topic: str = "", code: str = "") -> dict:
    """Return this org's ADK agent-building standards for a topic, and review agent code against
    them (determinism, no hardcoded env, guardrails, eval)."""
    return skills.adk_best_practices(topic=topic, code=code)


@mcp.tool()
def review_code(code: str, path: str = "") -> dict:
    """Deterministic code review: secrets, hardcoded environment, debugging leftovers, unsafe patterns."""
    return skills.review_code(code, path=path)


@mcp.tool()
def check_infra(content: str, filename: str = "") -> dict:
    """Review Terraform and CI/CD files against conventions (no hardcoded project, required_version,
    labels, a test/lint step in the pipeline)."""
    return skills.check_infra(content, filename=filename)


@mcp.tool()
def suggest_tests(code: str) -> dict:
    """Suggest the tests a change needs: per-function cases, edge cases, and known-good/known-bad
    fixtures for decision logic."""
    return skills.suggest_tests(code)


def main(argv: list[str]) -> int:
    transport = "streamable-http" if "--http" in argv else "stdio"
    mcp.run(transport=transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
