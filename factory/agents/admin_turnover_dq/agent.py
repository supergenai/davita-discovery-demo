"""Entrypoint for the Admin Turnover DQ spoke.

  python agents/admin_turnover_dq/agent.py --local   # run the deterministic pipeline
  (deploy path: python -m agent_factory.runtime deploy agents/admin_turnover_dq/config.yaml)

`root_agent` is the ADK agent object Agent Engine / `adk` CLI discover for the
interactive/UI surface.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python agents/admin_turnover_dq/agent.py` by putting the factory root on the path.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent_factory import AgentSpec, build_agent, run_pipeline

CONFIG = Path(__file__).with_name("config.yaml")

spec = AgentSpec.load(CONFIG)
root_agent = build_agent(spec)  # ADK agent for interactive / Agent-Engine surface


def main(argv: list[str]) -> int:
    summary = run_pipeline(spec)
    print("Run summary:", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
