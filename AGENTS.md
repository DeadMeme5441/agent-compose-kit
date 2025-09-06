Agent Instructions
==================

Status
- Core library implemented through Phases 1–5:
  - Phase 1: Schema models + validation helpers
  - Phase 2: McpRegistry + loader integration + tests
  - Phase 3: OpenAPIRegistry + URL allowlist + tests
  - Phase 4: A2A remote agent support + tests
  - Phase 5: Server QoL — /schema, /lint, /graph, SSE keepalive, /runs/{id}/cancel + tests

What’s next (high level)
- Wire registries more deeply in server startup (optional): construct MCP/OpenAPI registries and pass into tool loading when applicable; ensure close_all on shutdown
- Expand README examples/templates (MCP/OpenAPI/A2A)
- Optional strict lint pass for E501 long lines
- Optionally prepare a tagged release

Env
- Python 3.12; uv for deps; loguru for logging; pytest (unit+integration); FastAPI optional.

Flow
1) Read IMPLEMENTATION_PLAN.md + README/tests (llms_docs if needed).
2) Environment: uv sync --all-extras --dev.
3) Implement per plan; add Google-style docstrings; guard optional deps (fastapi, mcp, requests, adk).
4) Tests: uv run pytest -q (unit first, then guarded integration/skipped tests).
5) Lint/format: uv run ruff check . && uv run ruff format . (E501 non-blocking by default).
6) Docs: update README and markdowns with new endpoints and examples.
7) GitHub: open PRs and ensure CI green, or commit directly to master when requested.

Use Conventional Commits.
