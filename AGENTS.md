# Repository Guidelines

## Scope & Purpose
Core Python library to compose and run Google ADK agent systems from YAML. No CLI/TUI. Programmatic API only.

## Structure
- Source: `src/` (library modules), entry placeholder at `src/main.py`.
- Config: `pyproject.toml` (Python 3.12+, pytest + ruff).
- Tests: `tests/` (unit/integration, guarded for external deps).
- Configs: `configs/` and `templates/` for examples.

## Development
- Lint: `uv run --with ruff ruff check .`
- Format: `uv run --with ruff ruff format .`
- Tests: `uv run --with pytest pytest -q`

## Coding Style
- PEP 8, 4‑space indent, 100 char line length.
- Imports grouped stdlib → third‑party → local.
- Type hints on public functions; Pydantic models for config.

## Current Capabilities
- Config (Pydantic) with env interpolation and provider defaults (`model_providers`).
- Services:
  - Sessions: `InMemorySessionService` (default), `RedisSessionService`, `MongoSessionService`, `DatabaseSessionService`.
  - Artifacts: `InMemoryArtifactService` (default), `LocalFolderArtifactService`, `S3ArtifactService`, `GcsArtifactService`.
  - Memory: `InMemoryMemoryService` (default), `VertexAiMemoryBankService` (falls back to in‑memory if params missing).
- Agents: direct model IDs or LiteLLM models; function tools; sub‑agent wiring.
- Workflows: `sequential|parallel|loop` composition.
- Runtime: YAML → `RunConfig`; helper to construct `Runner`.

## Design Principles
- Conservative defaults: missing required params → fall back to in‑memory services (no surprise external calls).
- Provider‑agnostic models: LiteLLM wrapper with provider defaults, explicit values win.
- Separation of concerns: config → factories → runtime, testable at each layer.

## YAML Config Model
- `agents[]`: name, model, instruction, tools, optional `sub_agents`.
- `services`:
  - `session_service`: `in_memory | redis | mongo | database` (+ params)
  - `artifact_service`: `in_memory | local_folder | s3 | gcs` (+ params)
  - `memory_service`: `in_memory | vertex_ai` (+ params; falls back if missing)
- `model_providers`: defaults per LiteLLM provider (e.g., `openai`, `ollama_chat`, `anthropic`).
- `workflow`: `{type: sequential|parallel|loop, nodes: [agent names]}`
- `runtime`: `streaming_mode, max_llm_calls, save_input_blobs_as_artifacts, speech?`
- `tools[]` (function now; MCP/OpenAPI planned):
  - Function: `{type: function, ref: module:callable, name?}`

## Service Wiring
- Sessions: YAML → InMemory/Redis/Mongo/Database.
- Artifacts: YAML → InMemory/Local/S3/GCS.
- Memory: YAML → InMemory/Vertex AI (guarded fallback).
- Runner: `Runner(agent=..., artifact_service=..., session_service=..., memory_service=optional)`.

## Tools
- Function tools: dotted imports wrapped as `FunctionTool` with optional name override.
- Planned: MCP toolset (stdio or HTTP/SSE) and OpenAPI toolset (spec→tools) with allowlists.

## Testing
- Unit tests: config/env, factories (with fallbacks), model resolution, function tools, workflows, run config.
- Integration: in‑memory runs; skip cloud-backed paths without creds.
- Commands:
  - `uv run --with pytest pytest -q`

## Roadmap (M1 → M3)
- M1: Add Database session mapping (DONE); conservative fallbacks (DONE); MCP/OpenAPI toolset loaders; JSON Schema export; filesystem registry helpers; expanded tests; docs.
- M2: YAML overlays/partials; instruction templating helpers; examples gallery.
- M3: Observability helpers (Arize/Phoenix); evaluation hooks; isolation options; deployment samples (external repos).

## PR Guidelines
- Conventional Commits.
- PRs should include: summary, example YAML, test updates, and passing CI (ruff + pytest).

## References
- ADK docs topics: Sessions/State/Memory, Artifacts, RunConfig, Agents, Tools (function/MCP/OpenAPI).
