# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/main.py` (no root `main.py`).
- Config: `pyproject.toml` (Python 3.12; Ruff + pytest configured).
- Tests: `tests/` (e.g., `tests/test_main.py`).
- Configs: `configs/` (YAML describing agents, groups, services, MCP, runtime).
- Purpose: YAML-driven wrapper around `google-adk` to build agents and agent groups, wiring MCP connections, `SessionService`, and `ArtifactService` (adk-extra-services).

## Build, Test, and Development
- Lint: `uv run --with ruff ruff check .`  •  Format: `uv run --with ruff ruff format .`
- Test: `uv run --with pytest pytest -q`

## Terminal UI
Not included. This repository is core-only and exposes a programmatic API for YAML-driven agent/workflow construction.

## Project Settings
Not included. This repository focuses strictly on the core config-driven library.

## Coding Style & Naming Conventions
- PEP 8, 4 spaces, max line length 100.
- Names: `snake_case` (functions/vars), `PascalCase` (classes), lower_case modules.
- Imports: stdlib → third‑party → local; keep sorted; blank lines between groups.
- Type hints required on public functions; prefer dataclasses/pydantic models for config.

## YAML Config Model (Planned)
- `agents[]`: name, model, instruction, tools, optional `sub_agents` (for groups).
- `services`: `session_service` (in_memory | redis | mongo | vertex_ai | db), `artifact_service` (in_memory | gcs | s3 | local_folder) with backend params.
- `mcp`: outbound MCP servers to consume as tools (host/port/auth/allowlist).
- `runtime`: `RunConfig` options (streaming_mode, max_llm_calls, save_input_blobs_as_artifacts, speech).
- `model_providers`: defaults per LiteLLM provider (e.g., `openai`, `ollama_chat`) merged into agent models.
 - `workflow`: `{type: sequential|parallel|loop, nodes: [agent names]}` to compose multi-agent flows.
- Example:
  ```yaml
  services:
    session_service: {type: redis, redis_url: redis://localhost:6379}
    artifact_service: {type: s3, bucket_name: my-bucket, endpoint_url: https://s3.amazonaws.com}
  agents:
    - name: planner
      model: gemini-2.0-flash  # or LiteLLM wrapper below
      tools: [load_memory]
    - name: openai_agent
      model:
        type: litellm
        model: openai/gpt-4o-mini
        # api_base: http://localhost:11434/v1   # for Ollama via OpenAI shim
        # api_key: ${OPENAI_API_KEY}
  model_providers:
    openai:
      api_key: ${OPENAI_API_KEY}
    ollama_chat:
      api_base: ${OLLAMA_API_BASE}
  groups:
    - name: build_pipeline
      members: [planner]
  runtime: {streaming_mode: SSE, max_llm_calls: 200}
  mcp:
    - name: db_toolbox
      host: localhost
      port: 8000
  ```

## Service Wiring (Implementation Plan)
- Sessions: map YAML → `InMemorySessionService` | `RedisSessionService` | `MongoSessionService` | `VertexAiSessionService`.
- Artifacts: map YAML → `InMemoryArtifactService` | `GcsArtifactService` | `S3ArtifactService` | `LocalFolderArtifactService`.
- Runner: `Runner(agent=..., session_service=..., artifact_service=..., memory_service=optional)`; compose groups via `sub_agents`.

## Testing Guidelines
- Pytest; tests in `tests/test_*.py`; mock external services (Redis/Mongo/S3/MCP).
- Aim ≥90% coverage for new code; validate YAML schema + error paths.

## Commit & PR Guidelines
- Conventional Commits (e.g., `feat: load services from yaml`).
- PRs must include: summary, linked issues, example YAML, and local run steps; ensure `ruff` + tests pass.

## Using llms_docs MCP for google-adk
- Steps: list sources → open “Google ADK” → fetch pages.
- Useful pages: MCP (`docs/mcp/index.md`), Sessions/Memory (`docs/sessions/*.md`), Artifacts (`docs/artifacts/index.md`), Runtime (`docs/runtime/runconfig.md`).
- Use this to align YAML → ADK services/tools precisely before implementation.

## LiteLLM Models (Any Provider)
- Enable with YAML `model: {type: litellm, model: provider/model-id, api_base?, api_key?}`.
- Examples:
  - OpenAI: set `OPENAI_API_KEY`; model `openai/gpt-4o-mini`.
  - Ollama (local): set `OPENAI_API_BASE=http://localhost:11434/v1` and `OPENAI_API_KEY=anything`; model `openai/mistral-small3.1`.
  - Anthropic direct: set `ANTHROPIC_API_KEY`; model `anthropic/claude-3-5-sonnet-latest`.

## Dev Workflow (Fresh Start)
- `uv sync` to install deps; add new ones with `uv add <pkg>` (use `--dev` for dev tools).
- Run tests: `uv run --with pytest pytest -q` (should pass out-of-the-box).
- Extend features:
  - Services: `src/services/factory.py`
  - Config models: `src/config/models.py`
  - Agents/tools: `src/agents/builder.py`
  - Runner logic: `src/runtime/supervisor.py`
