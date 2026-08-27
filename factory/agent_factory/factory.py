"""The factory: assemble a running ADK agent from an AgentSpec.

build_agent() returns an ADK LlmAgent for the interactive / UI / Agent-Engine
surface, with the spec's granted skills as tools and guardrail callbacks attached.
The scheduled/background surface calls pipeline.run(spec) directly (deterministic).
Both share the same skills, guardrails, HITL, and actions - only the spec changes.
"""

from __future__ import annotations

import logging

from .config import AgentSpec
from .guardrails import make_tool_guard
from .skills import resolve_skills

log = logging.getLogger("factory.factory")


def _instruction(spec: AgentSpec) -> str:
    ctx = spec.business_context
    lines = [
        f"You are '{spec.name}', a Davita data-quality agent. {spec.description}",
        "The deterministic reconciliation is done in code and given to you as results.",
        "Your job is ONLY to explain mismatches in plain language and prioritize them.",
        "Never invent or re-decide a mismatch. Never expose PII.",
    ]
    if "turnover_definition" in ctx:
        lines.append(f"Turnover definition: {ctx['turnover_definition']}")
    if "instructions" in ctx:
        lines.append(str(ctx["instructions"]))
    return "\n".join(lines)


def build_agent(spec: AgentSpec):
    """Construct the ADK LlmAgent for this spec (interactive/UI/Agent-Engine surface)."""
    from google.adk.agents import LlmAgent

    granted = list(dict.fromkeys(spec.sources + spec.skills))  # dedupe, keep order
    tools = resolve_skills(granted)
    guard = make_tool_guard(allowed=set(granted))

    agent = LlmAgent(
        name=spec.name,
        model=spec.model,
        description=spec.description or f"Davita DQ agent: {spec.name}",
        instruction=_instruction(spec),
        tools=tools,
        before_tool_callback=guard,
    )
    log.info("built agent '%s' (model=%s, tools=%s)", spec.name, spec.model, granted)
    return agent
