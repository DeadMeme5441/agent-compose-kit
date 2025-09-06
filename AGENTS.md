Agent Instructions
==================

Status
- Core lib ready; see IMPLEMENTATION_PLAN.md for A2A + MCP/OpenAPI registry work.

Env
- Python 3.12; uv for deps; loguru for logging; pytest (unit+integration); FastAPI optional.

Flow
1) Read IMPLEMENTATION_PLAN.md + README/tests using llms_docs.
2) Create worktree: git worktree add ../wt-<slug> -b feat/<slug> && cd ../wt-<slug>.
3) uv sync --all-extras --dev.
4) Implement per plan; add docstrings; guard optional deps.
5) Tests: uv run pytest -q (unit first, then guarded integration).
6) Lint/format: uv run ruff check . && uv run ruff format .
7) Update docs/examples minimally.
8) PR: push; gh pr create -f; ensure CI green; gh pr merge --squash.

Use Conventional Commits.
