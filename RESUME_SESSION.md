Resume Session Guide
====================

Snapshot
- Core repo: agent-compose-kit (library-only). IMPLEMENTATION_PLAN.md and AGENTS.md present. Phases 1–5 implemented (schema+validation, MCP/OpenAPI registries, A2A remote, server QoL).
- Decisions: UI = React + Vite SPA with Bun; TUI = Textual; Backend = FastAPI + Postgres + Redis/Arq + S3-compatible. This repo focuses on YAML→ADK, remote consume, registries, validation, and dev server QoL.

Next Builds (this repo)
✓ 1) Schema: AppConfig.a2a_clients, mcp_registry, openapi_registry; AgentConfig.kind (llm|a2a_remote) + client.
✓ 2) MCP Registry (SSE-first; stdio/http optional): tools/mcp_registry.py; loader + agent-registry integration; validate + tests.
✓ 3) OpenAPI Registry (URL/path/inline + allowlist): tools/openapi_registry.py; loader + agent‑registry; validate + tests.
✓ 4) A2A remote agent: builder support for kind=a2a_remote; validate + tests.
✓ 5) Server QoL: /schema, /lint diagnostics, /graph, /runs/{id}/cancel; SSE keepalive; tests (guarded on fastapi/adk).

Up Next
6) Server registry wiring: construct MCP/OpenAPI registries on startup when present and pass into loader calls; ensure close_all on shutdown.
7) Examples/templates: add MCP/OpenAPI/A2A snippets to templates/app.yaml and README quickstarts.
8) Optional: strict lint E501 pass or tune line-length, and prep a tagged release.

Environment & Conventions
- Python 3.12; uv for deps; loguru for logging (optional); pytest (unit+integration; guard optional deps); ruff for lint/format; Conventional Commits.

Fresh Session Checklist
1) Read IMPLEMENTATION_PLAN.md, AGENTS.md, README changes.
2) Ensure GitHub PAT (scopes: repo, project). gh auth status; gh auth refresh -s project.
3) Setup: uv sync --all-extras --dev
4) Implement next items (see Up Next); add Google-style docstrings; guard optional deps.
5) Tests: uv run pytest -q (unit first, then guarded/skipped integration).
6) Lint/format: uv run ruff check . && uv run ruff format .
7) Docs: update README/templates with examples as needed.
8) PR or direct commit (as agreed): push and ensure CI green; merge.

Docs & References
- ADK MCP: google/adk-python mcp_toolset + mcp_session_manager.
- ADK OpenAPI: openapi_toolset (spec_str/spec_type, auth scheme/credential, tool_filter).
- A2A: adk-docs a2a intro/quickstarts (consume via RemoteA2aAgent).

Optional (multi-repo setup)
- scripts/bootstrap_repos.sh, scripts/seed_issues.sh, scripts/setup_project.sh (requires gh project support). Not required for core library work.

Grand Roadmap (multi‑repo)
- Repos
  - agent-compose-kit (this): core YAML→ADK, A2A consume, MCP/OpenAPI registries, validation, dev server.
  - google-adk-extras: extended services (sessions/memory/artifacts/credentials) + custom Runner wrapper.
  - agent-platform-backend: FastAPI, Postgres, Redis/Arq, S3-compatible; APIs for Projects/Systems/Versions/Runs/Tests; SSE/WS; secrets; git.
  - agent-tui: Textual app (tree/editor/graph/run/test panels; Copilot with guarded patch apply).
  - agent-web: React + Vite SPA with Bun (Monaco, React Flow, TanStack Query, Tailwind + shadcn/ui, Zustand if needed).
  - agents-tooling: shared tool adapters, codegen, test DSL, CI actions.
- Architecture
  - Core builds Runner + registries; backend orchestrates runs/tests/deploys; UIs consume backend APIs; Copilot tools operate via backend.
- Phases
  1) Core hardening (this repo) — current focus.
  2) Backend MVP — CRUD + Runs SSE + job queue + secrets/artifacts + git.
  3) TUI MVP — local-first authoring; Copilot.
  4) Web UI MVP — SPA with editor/graph/runs/tests.
  5) Testing/CI — test spec DSL, golden snapshots, GH Actions.
  6) Deployments — container builds, K8s/VM manifests, apply/rollback.
- Chosen stacks
  - Backend: FastAPI + Postgres + Redis/Arq + S3-compatible; SSE with keepalive; cancel tokens.
  - Web: React + Vite + Bun; Monaco + React Flow + TanStack Query + Tailwind/shadcn; auth later.
  - TUI: Textual (Python).
- Bootstrap
  - gh auth login; ./scripts/bootstrap_repos.sh --owner <OWNER> --clone
  - ./scripts/seed_issues.sh --owner <OWNER>
  - ./scripts/setup_project.sh --owner <OWNER>
