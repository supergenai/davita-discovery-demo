"""Observability wiring: structured logging with a per-agent label so every run,
tool call, and action is filterable by agent_id in Cloud Logging, and cost/usage
rolls up per agent (the discipline that makes shared-runtime cost attributable).

Online this attaches Cloud Logging; offline it is plain structured logging.
"""

from __future__ import annotations

import logging
import os


def configure(agent_id: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(levelname)s agent_id={agent_id} %(name)s: %(message)s",
    )
    if os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("FACTORY_CLOUD_LOGGING") == "1":
        try:  # pragma: no cover - requires GCP
            import google.cloud.logging

            client = google.cloud.logging.Client()
            client.setup_logging(labels={"agent_id": agent_id})
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("factory.obs").warning("cloud logging off: %s", exc)
    return logging.getLogger(f"factory.{agent_id}")
