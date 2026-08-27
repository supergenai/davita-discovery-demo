"""Central, swappable configuration for the whole factory.

Every environment-specific value (project, region, service account, feature flags)
is read HERE and nowhere else, so moving from the demo project to the enterprise
project later is a one-line change in `.env` (or the deploy env) - no code edits.

Precedence: process env vars > factory/.env file > built-in defaults.
Nothing project-specific is baked into the code.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Load factory/.env if present (does not override already-set process env vars).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseModel):
    project: str | None          # GOOGLE_CLOUD_PROJECT (None -> offline)
    region: str                  # GOOGLE_CLOUD_REGION
    dataset_prefix: str          # optional prefix for BigQuery datasets (multi-tenant)
    offline: bool                # force local seed/stub mode
    agent_service_account: str | None
    use_dlp: bool                # real Cloud DLP vs regex de-id
    cloud_logging: bool          # attach Cloud Logging
    time_zone: str               # scheduler tz
    elie_default_recipient: str  # fallback email target for the ELie stub
    staging_bucket: str | None   # GCS bucket for Agent Engine deploy uploads


def get_settings() -> Settings:
    """Build settings fresh from the environment (cheap; picks up test overrides)."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT") or None
    return Settings(
        project=project,
        region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
        dataset_prefix=os.getenv("FACTORY_DATASET_PREFIX", ""),
        offline=(project is None) or os.getenv("FACTORY_OFFLINE") == "1",
        agent_service_account=os.getenv("AGENT_SERVICE_ACCOUNT") or None,
        use_dlp=os.getenv("FACTORY_USE_DLP") == "1",
        cloud_logging=os.getenv("FACTORY_CLOUD_LOGGING") == "1",
        time_zone=os.getenv("FACTORY_TIME_ZONE", "America/Denver"),
        elie_default_recipient=os.getenv("ELIE_DEFAULT_RECIPIENT", "ops-owner@davita.example"),
        staging_bucket=(
            os.getenv("FACTORY_STAGING_BUCKET")
            or (f"gs://{project}-agent-staging" if project else None)
        ),
    )
