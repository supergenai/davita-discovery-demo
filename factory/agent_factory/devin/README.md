# Devin plugin (MCP surface)

A context-aware review/build assistant for Devin, published as an MCP server. Devin acts as an MCP
client and calls these tools at runtime, so it builds code aware of business context, recorded
decisions, ADK standards, and infra conventions. The same skills back a CI/CD reviewer on merge
requests. All tools are read-only and advisory (L1): they review, flag, and suggest, never merge.

## Tools

| Tool | Purpose |
|------|---------|
| `get_business_context(topic)` | Retrieve documented rules/definitions (Confluence/knowledge) |
| `flag_conflicts(proposal)` | Flag a change/decision that contradicts a recorded decision |
| `adk_best_practices(topic, code)` | Return ADK standards + review agent code against them |
| `review_code(code, path)` | Secrets, hardcoded env, debugging leftovers, unsafe patterns |
| `check_infra(content, filename)` | Terraform + CI/CD conventions |
| `suggest_tests(code)` | Per-function + edge-case + decision-fixture test suggestions |

## Run

```bash
# local, over stdio (for an MCP client on the same machine)
uv run python -m agent_factory.devin.server

# hosted HTTP (Cloud Run), the endpoint Devin connects to
uv run python -m agent_factory.devin.server --http
```

## Connect Devin

Devin supports external MCP servers. Point Devin's MCP client at the hosted `--http` endpoint, then
add a Playbook: "before implementing, call `get_business_context` and `flag_conflicts`; after
implementing, call `review_code`, `check_infra`, and `adk_best_practices`."

## Knowledge sources (the context layer)

Retrieval runs over `factory/knowledge/` today (a deterministic keyword retriever, offline). This is
the seam: swap `retriever.LocalRetriever` for a Vertex AI Search retriever indexed over your GitLab
repos + Confluence spaces + tool docs. Every tool keeps working unchanged. The recorded-decision
registry is `knowledge/decisions/registry.yaml`; conflict detection is only as good as what is
curated there.

## What is real vs stub

- Real: the six skills, the deterministic checks, the MCP server (stdio + streamable-http), the
  conflict registry, the knowledge retriever.
- Seam/stub: retrieval is local-corpus (swap for Vertex AI Search over real GitLab/Confluence);
  the LLM synthesis layer is intentionally out of the deterministic core.
