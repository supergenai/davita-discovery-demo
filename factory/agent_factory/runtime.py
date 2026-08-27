"""Run + deploy entrypoints.

  python -m agent_factory.runtime run   <path/to/config.yaml>   # background pipeline (local or GCP)
  python -m agent_factory.runtime deploy <path/to/config.yaml>  # deploy to Vertex AI Agent Engine

Deploy requires `google-cloud-aiplatform[agent_engines]` and GOOGLE_CLOUD_PROJECT/REGION.
"""

from __future__ import annotations

import logging
import sys

from .config import AgentSpec, offline
from .factory import build_agent
from .pipeline import run as run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("factory.runtime")


def run(config_path: str) -> dict:
    spec = AgentSpec.load(config_path)
    log.info("running '%s' (offline=%s)", spec.name, offline())
    summary = run_pipeline(spec)
    log.info("run summary: %s", summary)
    return summary


def deploy(config_path: str):  # pragma: no cover - requires GCP
    """Deploy the spoke's ADK agent to Vertex AI Agent Engine.

    Verified against google-cloud-aiplatform 1.165.1: wraps the ADK agent in an
    AdkApp (tracing on), uploads our local packages via extra_packages (without this
    the remote build cannot import agent_factory/agents), runs under the per-agent
    service account, and passes runtime env so cloud mode (not offline) is used.
    """
    import vertexai
    from vertexai import agent_engines
    from vertexai.preview.reasoning_engines import AdkApp

    from .settings import get_settings

    spec = AgentSpec.load(config_path)
    s = get_settings()
    if s.offline or not s.project:
        raise RuntimeError("deploy needs GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_REGION set")
    project, region = s.project, s.region
    vertexai.init(project=project, location=region, staging_bucket=s.staging_bucket)

    app = AdkApp(agent=build_agent(spec), enable_tracing=True)
    remote = agent_engines.create(
        agent_engine=app,
        display_name=spec.name,
        description=spec.description or f"Davita DQ agent: {spec.name}",
        requirements=[
            "google-adk", "google-cloud-aiplatform[agent-engines]",
            "google-cloud-bigquery", "pydantic>=2", "pyyaml",
        ],
        extra_packages=["agent_factory", "agents"],  # our source, uploaded to the build
        service_account=s.agent_service_account,  # per-agent SA (Terraform output)
        # NOTE: GOOGLE_CLOUD_PROJECT/REGION are reserved by Agent Engine and injected
        # automatically, so we only force online mode here.
        env_vars={"FACTORY_OFFLINE": "0"},
    )
    log.info("deployed '%s' -> %s", spec.name, remote.resource_name)
    return remote


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in {"run", "deploy"}:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    (run if cmd == "run" else deploy)(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
