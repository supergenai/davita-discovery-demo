"""Skills registry: GCP capabilities exposed as ADK tools.

Each skill is a plain function with a clear docstring/signature so the ADK LlmAgent
can call it, plus a name the spec's allow-list references. Source skills read
enterprise data (mocked as BQ/CSV); action skills write results, email, dashboard.
"""

from __future__ import annotations

from typing import Any

from ..sinks import refresh_looker, send_elie, write_results
from ..sources import read_source


def read_mdm() -> list[dict[str, Any]]:
    """Read Oracle MDM master records for Facility Admins / Regional Ops Directors."""
    return read_source("mdm")


def read_workday() -> list[dict[str, Any]]:
    """Read Workday employment records (status, termination/transfer dates, role)."""
    return read_source("workday")


def read_cwow() -> list[dict[str, Any]]:
    """Read CWOW role-assignment records (facility to employee role assignments)."""
    return read_source("cwow")


def write_dq_results(table: str, rows: list[dict[str, Any]]) -> str:
    """Persist data-quality mismatch results to the results table."""
    return write_results(table, rows)


def refresh_dashboard(dashboard: str) -> str:
    """Refresh the Looker data-quality dashboard (stub in the prototype)."""
    return refresh_looker(dashboard)


def send_email(to: str, subject: str, body: str) -> str:
    """Send an Outlook email via ELie (stub records the payload for the HITL loop)."""
    return send_elie(to, subject, body)


# name -> callable. The spec's `skills` + `sources` select which are granted.
SKILL_FUNCS: dict[str, Any] = {
    "mdm": read_mdm,
    "workday": read_workday,
    "cwow": read_cwow,
    "bigquery_write": write_dq_results,
    "looker": refresh_dashboard,
    "elie": send_email,
}


def resolve_skills(names: list[str]) -> list[Any]:
    """Return the callables for the given skill/source names (for ADK tools=)."""
    missing = [n for n in names if n not in SKILL_FUNCS]
    if missing:
        raise KeyError(f"unknown skills {missing}; known: {sorted(SKILL_FUNCS)}")
    return [SKILL_FUNCS[n] for n in names]
