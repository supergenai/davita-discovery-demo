"""Davita Agent Factory - reusable ADK agent chassis (hub).

A spoke = an AgentSpec (config.yaml). The factory wires shared sockets (sources,
skills, guardrails, business logic, HITL, actions) into a running agent.
"""

from .config import AgentSpec, Autonomy, Surface
from .factory import build_agent
from .pipeline import run as run_pipeline

__all__ = ["AgentSpec", "Autonomy", "Surface", "build_agent", "run_pipeline"]
