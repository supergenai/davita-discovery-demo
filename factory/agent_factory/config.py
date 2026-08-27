"""AgentSpec: the declarative contract a spoke hands the factory.

A new agent = a new config.yaml that fills these fields. The factory reads the
spec and assembles a running ADK agent from the shared sockets (sources, skills,
guardrails, business logic, HITL, action). Nothing here is agent-specific code.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Autonomy(str, Enum):
    L0 = "L0"  # notify only
    L1 = "L1"  # suggest
    L2 = "L2"  # act with approval (HITL gate)
    L3 = "L3"  # act + audit
    L4 = "L4"  # fully autonomous


class Surface(str, Enum):
    BACKGROUND = "background"  # headless: Scheduler/Eventarc -> Agent Engine
    UI = "ui"                  # FastAPI/Cloud Run, also serves the HITL review queue


class TriggerSpec(BaseModel):
    kind: str = "schedule"          # schedule | event | manual
    schedule: str | None = None     # cron, e.g. "0 6 * * 1" (weekly Mon 6am)


class ActionSpec(BaseModel):
    """What the agent does when it finishes. Any subset."""

    write_bigquery: str | None = None   # fully-qualified results table
    refresh_looker: bool = False        # stub in the prototype
    notify_elie: bool = False           # stub: writes ops.sent_emails
    hitl_review: bool = False           # push flagged items to ops.review_queue


class AgentSpec(BaseModel):
    name: str
    description: str = ""
    model: str = Field(default="gemini-2.5-flash")  # verify availability in your project/region
    surface: Surface = Surface.BACKGROUND
    autonomy: Autonomy = Autonomy.L1

    trigger: TriggerSpec = Field(default_factory=TriggerSpec)

    # Which shared sockets this spoke plugs in:
    sources: list[str] = Field(default_factory=list)   # e.g. ["mdm", "workday", "cwow"]
    skills: list[str] = Field(default_factory=list)     # e.g. ["bigquery", "elie", "looker"]
    rules: str | None = None                            # dotted path to a reconcile() callable
    action: ActionSpec = Field(default_factory=ActionSpec)

    # Free-form business context injected into the instruction + rules:
    business_context: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "AgentSpec":
        data = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(data)


def offline() -> bool:
    """True when no GCP project is configured (or FACTORY_OFFLINE=1); sources read
    local seed CSVs and actions/LLM steps run in stub mode. Delegates to settings
    so all environment config lives in one place."""
    from .settings import get_settings

    return get_settings().offline
