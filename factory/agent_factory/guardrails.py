"""Guardrails socket, wired as ADK callbacks on the agent.

- tool allow-list: the agent may only call skills its spec granted.
- cost cap: bound the number of tool calls per run.
- DLP de-identify: mask PII before it reaches the model (stub offline; real DLP online).

Callbacks match the ADK 2.x signatures (before_tool_callback / before_model_callback).
They are attached in factory.build_agent(). Returning a value short-circuits the call.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

log = logging.getLogger("factory.guardrails")

_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def make_tool_guard(allowed: set[str], max_calls: int = 25):
    """Enforce the tool allow-list and a per-run call cap."""
    state = {"calls": 0}

    def before_tool_callback(tool: Any, args: dict, tool_context: Any):  # noqa: ANN401
        name = getattr(tool, "name", str(tool))
        state["calls"] += 1
        if name not in allowed:
            log.warning("guardrail: blocked disallowed tool %s", name)
            return {"error": f"tool '{name}' is not in this agent's allow-list"}
        if state["calls"] > max_calls:
            log.warning("guardrail: cost cap hit (%d calls)", state["calls"])
            return {"error": "cost cap reached; aborting further tool calls"}
        return None

    return before_tool_callback


def deidentify(text: str) -> str:
    """Mask obvious PII. Offline uses regex; online swap for Cloud DLP."""
    if os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("FACTORY_USE_DLP") == "1":
        return _dlp_deidentify(text)
    text = _SSN.sub("[SSN]", text)
    text = _EMAIL.sub("[EMAIL]", text)
    return text


def _dlp_deidentify(text: str) -> str:  # pragma: no cover - requires GCP + DLP API
    from google.cloud import dlp_v2

    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}"
    resp = client.deidentify_content(request={
        "parent": parent,
        "item": {"value": text},
        "deidentify_config": {
            "info_type_transformations": {"transformations": [
                {"primitive_transformation": {"replace_with_info_type_config": {}}}
            ]}
        },
        "inspect_config": {"info_types": [
            {"name": "US_SOCIAL_SECURITY_NUMBER"}, {"name": "EMAIL_ADDRESS"},
            {"name": "PERSON_NAME"},
        ]},
    })
    return resp.item.value
