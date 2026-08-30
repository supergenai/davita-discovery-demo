# ADK Agent Best Practices

Standards this org enforces when building ADK agents. Each rule has an id used in reviews.

## BP-DETERMINISM: keep the decision deterministic
The match, classification, or determination must be code (rules/SQL), not the LLM. The model
explains and prioritizes; it never decides. This keeps outcomes auditable and reproducible.
Signal of violation: an LLM prompt that asks the model to "decide", "determine", or "match".

## BP-CONFIG: config-driven spokes on a shared chassis
A new agent is a config (AgentSpec / config.yaml), not a new codebase. Business context, sources,
skills, and action are the only per-agent inputs. Do not fork the chassis per use case.

## BP-NOHARDCODE: no hardcoded environment
No project id, region, dataset, bucket, or endpoint literals in code. Read them from settings/env
so the same code runs in demo and enterprise projects unchanged.

## BP-GROUNDING: ground on real schema
Ground queries on the live schema (BigQuery skill / Dataplex / MCP), never on assumed columns.
Generation is not verification: validate generated SQL against the schema before running it.

## BP-GUARDRAILS: guardrails as callbacks
Every agent enforces a tool allow-list, a cost cap, and PII de-identification (DLP) before the
model sees data. Guardrails live in the chassis, not per agent.

## BP-EVAL: ground-truth eval before trust
An agent must have a labeled ground-truth set and a way to measure correctness before its autonomy
is raised. Without continuous eval, agents degrade silently.

## BP-AUTONOMY: autonomy is earned
Start at L0/L1. PHI or irreversible actions never run above L2 (act-with-approval) without
governance sign-off. A human owns the decision.

## BP-HITL: explicit human gate for L2+
Actions that change systems or notify people run behind a review queue with a resume-on-confirm gate.

## BP-IAM: least-privilege per-agent service account
One service account per agent, scoped only to the datasets and services it needs. Blast-radius control.

## BP-OBSERVABILITY: trace everything with agent_id
Every run, tool call, and action is logged with an agent_id label so cost and behavior are
attributable per agent. Teams with good tracing debug far faster.

## BP-METRICS: measure what the business cares about
Judge the agent on business metrics (processing time, error rate per thousand, cost per unit, hours
freed), not model benchmarks.
