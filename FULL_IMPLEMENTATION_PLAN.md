# Full Implementation Plan (Core YAML → ADK Library)

## 1) Objectives
- Build a Python library that constructs, validates, and runs agent systems from YAML using Google ADK and adk-extra-services.
- Optimize for fast iteration: define agents/services/workflows/tools via config; spin up systems quickly and consistently.
- Provide portable persistence (filesystem registry) to save/load versioned “systems”.
- Offer optional observability hooks (OpenInference) for Arize AX or Phoenix.
- Exclude CLI/TUI from this repo; keep programmatic API only.


## 2) Non‑Goals
- Shipping a CLI/TUI in this repository (external consumers can provide those).
- Deep deployment tooling (Cloud Run/GKE/Agent Engine samples can live in separate repos).
- Agentic authoring UI (future consumer projects can build atop this core).


## 3) Architecture Overview
- Config layer: Pydantic models + env interpolation; JSON Schema export; optional overlays.
- Builders: factories to map YAML → ADK services, tools, agents, and workflows.
- Runtime: `Runner` construction, `RunConfig` mapping, and session lifecycle helpers.
- Registry: simple filesystem storage for versioned systems (configs + metadata).
- Observability: optional instrumentation helpers for Arize AX / Phoenix via OpenInference.


## 4) Configuration Schema (YAML)
Top‑level keys (all optional unless noted):
- `services`:
  - `session_service` (required): `{type: in_memory|redis|mongo|database|vertex_ai|db, ...params}`
  - `artifact_service` (required): `{type: in_memory|local_folder|s3|gcs, ...params}`
  - `memory_service` (optional): `{type: in_memory|vertex_ai, params: {project, location, agent_engine_id}}`
- `model_providers`: provider defaults for LiteLLM (e.g., `openai`, `ollama_chat`, `anthropic`, `extra_headers`).
- `agents[]` (required ≥1):
  - `name` (string, required)
  - `model` (string id like `gemini-2.0-flash` OR `{type: litellm, model: provider/id, api_base?, api_key?, extra_headers?}`)
  - `instruction` (string | callable ref in future)
  - `tools[]` (see Tools schema)
  - `sub_agents[]` (names of other agents)
- `tools[]` (inline definitions consumed by agents):
  - function tool: `{type: function, ref: "module:callable", name?}`
  - MCP toolset: `{type: mcp, mode: stdio|sse|http, command/args|url|headers, tool_filter?[]}`
  - OpenAPI toolset: `{type: openapi, spec: {path|url|inline}, auth? {scheme, credential|env}, filter?[]}`
- `workflow`: `{type: sequential|parallel|loop, nodes: [agent names]}`
- `groups[]`: named convenience groups mapping to agent names.
- `runtime`: `{streaming_mode: NONE|SSE|BIDI, max_llm_calls: int, save_input_blobs_as_artifacts: bool, speech?: {...}}`
- `registry`: `{root: ./registry, naming?: {strategy: "semver|timestamp|manual"}}`


## 5) Builders & Factories
Services
- SessionService:
  - `in_memory` → `InMemorySessionService`
  - `redis` → `RedisSessionService` (adk-extra-services)
  - `mongo` → `MongoSessionService` (adk-extra-services)
  - `database`|`db` → `DatabaseSessionService` (ADK)
  - `vertex_ai` → `VertexAiSessionService` (ADK)
  - Validate required params (e.g., `redis_url`, `mongo_url`, `db_url`, `project/location`).
- ArtifactService:
  - `in_memory` → `InMemoryArtifactService`
  - `local_folder` → `LocalFolderArtifactService` (adk-extra-services)
  - `s3` → `S3ArtifactService` (adk-extra-services)
  - `gcs` → `GcsArtifactService`
- MemoryService:
  - `in_memory` → `InMemoryMemoryService`
  - `vertex_ai` → `VertexAiMemoryBankService` (params: `project, location, agent_engine_id`)

Models & Agents
- Model resolution: plain string id (Gemini/Vertex) or LiteLLM wrapper.
  - Merge provider defaults from `model_providers` by provider prefix of `model`.
- Agents: build `LlmAgent` instances; pass `instruction`, `tools`, `model`.
- Sub‑agents: second‑pass wiring by name.

Workflows
- When `workflow` present, construct root workflow agent:
  - `sequential` → `SequentialAgent(name="workflow", sub_agents=[...])`
  - `parallel` → `ParallelAgent(...)`
  - `loop` → `LoopAgent(...)`
- If not present, default root to the first defined agent.

Tools (Unified Loader)
- Function tools: dotted import → `FunctionTool`, optional name override.
- MCP toolsets: YAML → `McpToolset` with stdio/SSE/streamable HTTP connection params; optional `tool_filter`.
- OpenAPI toolsets: YAML spec (inline/path) → `OpenAPIToolset` → generated `RestApiTool`s; optional tool filtering.
- Shared toolsets: top-level `toolsets:` and `{use: name}` references in agents.


## 6) Runtime & Sessions
- `build_run_config(cfg)`: map to ADK `RunConfig`
  - `streaming_mode` → enum `NONE|SSE|BIDI`
  - `max_llm_calls` (default 500)
  - `save_input_blobs_as_artifacts` (bool)
  - `speech` fields (optional) if provided
- `build_runner(services, root_agent)`: return `Runner` configured with shared services.
- Session helpers:
  - `create_or_resume_session(app_name, user_id, session_id?)`
  - Document state semantics: commit after yielded events; allow dirty reads within an invocation.
  - Encourage prefixes: `user:`, `app:`, `temp:` with persistence behavior tied to backend.


## 7) Registry (Filesystem)
Purpose: Store/retrieve versioned “systems” (configs + metadata) for repeatable spin‑ups.
- Layout:
  - `registry/<system_name>/<version>/config.yaml`
  - Optional: `manifest.json` (id, tags, created_at), `notes.md`
- API:
  - `save_system(config: AppConfig, name: str, version: str|tag)`
  - `load_system(name: str, version: str|tag) -> AppConfig`
  - `list_systems() -> list[str]`
  - `list_versions(name: str) -> list[str]`
  - `promote(name, version, tag)` for aliases like `latest`/`prod`


## 8) Observability (Optional)
Provide helpers to enable OpenInference tracing with Arize AX or Phoenix:
- `enable_observability(provider: "arize"|"phoenix", **params)`
- Doc required packages/env and minimal setup snippets.
- Scope: library offers a thin entrypoint; full dashboards live with providers.


## 9) Public API Surface (Initial)
- Config: `load_config_file`, `AppConfig`, `write_example_config`, `export_json_schema`.
- Services: `build_session_service`, `build_artifact_service`, `build_memory_service`.
- Agents/Tools: `build_agents`, toolset loaders for function/MCP/OpenAPI.
- Workflow/Runtime: `build_workflow_root`, `build_run_config`, `build_runner`, `build_plan`.
- Registry: `save_system`, `load_system`, `list_systems`, `list_versions`, `promote`.


## 10) Security & Safety
- Strict env‑first secrets; support `${VAR}` interpolation; redact logs.
- MCP toolsets: require explicit `tool_filter`; document stdio vs remote and security implications.
- OpenAPI toolsets: validate auth config; caution on untrusted specs; optional allowlist.
- Filesystem paths: ensure local folder artifact base path and MCP filesystem scopes are explicit.


## 11) Testing Strategy
Unit Tests
- Config schema: happy/sad paths; env interpolation; provider default merges.
- Factories: services mapping with required/optional params.
- Tools: function loader (dotted import), MCP/OpenAPI toolset wiring (mock connection/specs).
- Agents/workflows: model resolution; sub‑agent wiring; workflow root assembly.
- Runtime: `RunConfig` mapping and defaults.

Integration Tests (non‑network focus)
- In‑memory services: end‑to‑end single and sequential workflows.
- Function tool execution within agent run; artifact save/load where applicable.

Skip/Mark
- Vertex AI / Database service paths (run only with env/creds present, else skip).


## 12) Documentation
- README: quickstart (programmatic), YAML example, services matrix, usage patterns.
- AGENTS.md: coding and config guidelines for this library; extension points.
- Examples: `templates/app.yaml`; curated examples for function tools, OpenAPI, MCP.
- Observability: short guide for Arize/Phoenix setup.


## 13) Roadmap & Milestones
M1 (Core hardening)
- Add `database` session service mapping (DONE).
- Implement MCP/OpenAPI toolset loaders + YAML wiring (DONE).
- Add JSON Schema export for `AppConfig`.
- Implement filesystem registry helpers.
- Expand tests to cover new factories and toolsets (DONE for loader & services).

M2 (Composition & UX)
- YAML overlays/partials and merge strategy.
- Instruction templating enhancements (state/artifacts) helper.
- Examples gallery; more workflow edge tests.

M3 (Advanced)
- Evaluation hooks; isolation options; richer planners/code execution wiring.
- Deployment samples (external repos): Cloud Run, GKE, Agent Engine.


## 14) Acceptance Criteria
- Given a valid YAML, library constructs services, tools, agents, workflows, and returns a runnable `Runner`.
- LiteLLM models resolve with provider defaults from `model_providers`.
- Function tools load via dotted imports and are callable in runs.
- Optional MCP/OpenAPI toolsets are built from YAML (with filtering) and callable.
- `build_run_config` maps fields correctly; streaming modes work per ADK.
- Registry APIs save/load systems on disk and list versions.
- Tests cover core flows; in‑memory E2E runs succeed.


## 15) Folder Structure (Current/Target)
- `src/config/models.py` — Pydantic models, env interpolation, JSON schema export.
- `src/services/factory.py` — session/artifact/memory service builders.
- `src/agents/builder.py` — model resolution (string/LiteLLM), function tool loader, sub‑agent wiring.
- `src/agents/tools.py` — conservative function tools (read/search/plan/graph).
- `src/runtime/supervisor.py` — plan summary, workflow root build, runner helpers, run config mapping.
- `src/registry/fs.py` — filesystem registry helpers (new).
- `templates/app.yaml`, `configs/app.yaml` — examples/templates.
- Tests under `tests/` for units + basic integration.


## 16) Implementation Tasks (Actionable)
1) Config/Schema
- Add JSON Schema export function for `AppConfig`.
2) Services
- Extend session factory: support `database` and `vertex_ai` with params + validation.
3) Tools
- Add MCP toolset loader: stdio + streamable HTTP/SSE; filtering.
- Add OpenAPI toolset loader: spec (path/url/inline), auth, filtering.
4) Agents/Workflow
- Expose `build_workflow_root(cfg, agent_map)` for reuse.
5) Runtime
- Harden `build_run_config` to include optional speech fields.
6) Registry
- Implement filesystem registry helpers + docs.
7) Tests
- Units for new services/toolsets; integration for in‑memory flows.
8) Docs
- Update README/AGENTS; add examples for MCP/OpenAPI & registry usage.


## 17) Risks & Mitigations
- Provider variability (LiteLLM): document defaults; clear error messages; examples for common providers.
- MCP lifecycle/scale: provide stdio for local; document remote HTTP/SSE for production; timeouts and cleanup.
- Security: default to restrictive tool filtering and explicit scopes; env‑first secrets.
- External creds/services: mark tests as skip when not configured; provide smoke tests for local paths.


## 18) Out‑of‑Scope Notes
- No UI or CLI shipped here; consumers can build atop this library.
- No heavy deployment code; only doc pointers and minimal examples.
