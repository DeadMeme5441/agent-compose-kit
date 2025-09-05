# Repository Guidelines

## Scope & Purpose
Core Python library to compose and run Google ADK agent systems from YAML. No CLI/TUI. Programmatic API only.

## Structure
- Source: `src/` (library modules), entry placeholder at `src/main.py`.
- Config: `pyproject.toml` (Python 3.12+, pytest + ruff).
- Tests: `tests/` (unit/integration, guarded for external deps).
- Configs: `configs/` and `templates/` for examples.
 - Registries: define under `tools_registry:` and `agents_registry:` in AppConfig, or separate YAML and merge into config.

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

## Unified Tools
- Function tool (Python): `{type: function, ref: module:callable, name?}` wraps a Python callable as a tool. Use MCP/OpenAPI for cross-language.
- MCP toolset: `{type: mcp, mode: stdio|sse|streamable_http, ...}` connects to an MCP server and provides its tools to the agent. Supports `tool_filter` and timeouts.
- OpenAPI toolset: `{type: openapi, spec: {inline|path}, spec_type: json|yaml, tool_filter?}` generates REST API tools from an OpenAPI spec.
- Shared toolsets: top-level `toolsets:` map for reuse, referenced by `{use: name}` in an agent’s `tools` list.

Example
```yaml
toolsets:
  files:
    type: mcp
    mode: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    tool_filter: [list_directory, read_file]

agents:
  - name: worker
    model: gemini-2.0-flash
    instruction: Use tools.
    tools:
      - {type: function, ref: tests.helpers:sample_tool, name: add}
      - {use: files}

  - name: api
    model: gemini-2.0-flash
    tools:
      - type: openapi
        spec:
          path: ./specs/petstore.yaml
        spec_type: yaml
```

Notes
- Paths under `spec.path` resolve relative to the config file directory.
- MCP stdio mode requires the `mcp` package (and any MCP server prerequisites). Remote modes require explicit `url` and optional headers.
- OpenAPI `spec.url` is not fetched by the loader (avoid silent network I/O). Use `path` or `inline` content.

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
  - Cloud-backed tests (e.g., GCS) are skipped unless credentials are present.

## Optional Deps
- MCP toolset (stdio) requires `mcp` package.
- MCP/OpenAPI require appropriate `google-adk` extras (ensure installed).

## Registries
- Tools Registry (global):
  - `tools_registry:` section in AppConfig with `tools` (each has `id`, `type`, and type-specific fields) and `groups` (`id` + `include` tool ids).
  - Build with `build_tool_registry_from_config(cfg)` and reuse across agents.
- Agents Registry (global):
  - `agents_registry:` section in AppConfig with `agents` (`id`, `model`, `instruction?`, `tools?`, `sub_agents?`) and `groups`.
  - Tool references inside agents can use `{use: registry:<tool_id>}` to pull from Tools Registry.
  - Build with `build_agent_registry_from_config(cfg, tool_registry=...)`.
- Lifecycle: call `ToolRegistry.close_all()` when done (e.g., on shutdown) to close toolset connections.

Example snippets
```yaml
tools_registry:
  tools:
    - id: util.add
      type: function
      ref: tests.helpers:sample_tool
      name: add
  groups:
    - id: essentials
      include: [util.add]

agents_registry:
  agents:
    - id: calc
      name: calculator
      model: gemini-2.0-flash
      tools: [{use: registry:util.add}]
  groups:
    - id: core
      include: [calc]
```

## Public API (for external CLI projects)
- `SystemManager(base_dir)`: load config, select `root_agent`, build `Runner`.
- `SessionManager(runner)`: create/get sessions for a user.
- `run_text(...)`: async generator yielding ADK events for a text input.
- `event_to_minimal_json(event)`: lightweight event serialization for terminals/UIs.
- Paths via env:
  - `AGENT_SYS_DIR` (default `./systems`)
  - `AGENT_OUTPUTS_DIR` (default `./outputs`)
  - `AGENT_SESSIONS_URI` (default `sqlite:///./sessions.db`)

## Roadmap (M1 → M3)
- M1: Add Database session mapping (DONE); conservative fallbacks (DONE); MCP/OpenAPI toolset loaders; JSON Schema export; filesystem registry helpers; expanded tests; docs.
- M2: YAML overlays/partials; instruction templating helpers; examples gallery.
- M3: Observability helpers (Arize/Phoenix); evaluation hooks; isolation options; deployment samples (external repos).

## PR Guidelines
- Conventional Commits.
- PRs should include: summary, example YAML, test updates, and passing CI (ruff + pytest).

## References
- ADK docs topics: Sessions/State/Memory, Artifacts, RunConfig, Agents, Tools (function/MCP/OpenAPI).
