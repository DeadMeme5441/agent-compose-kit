# Full Implementation Plan

## 1) Problem Statement & Goals
You want a terminal‑first tool that lets humans and agents collaboratively design, run, and manage agentic flows built on Google ADK. The system should:
- Generate/edit YAML flow specs that define agents, tools, services, runtime, and multi‑agent workflows.
- Validate and visualize flows, then execute them with ADK Runners and shared services.
- Support both manual and “agentic” authoring: an assistant agent can propose, scaffold, and evolve flows with human approval.
- Provide flexible model choice (Gemini, Vertex endpoints, plus any provider via LiteLLM including OpenAI, Anthropic, Ollama, vLLM).
- Offer production‑ready service backends (sessions, artifacts, memory) including adk-extra-services (Redis, Mongo, S3, local).
- Manage flows as a registry with versions/tags, sessions, artifacts, and run history.

Key non-goals (for now): GUI; deep cloud deployment tooling (we will integrate later via ADK patterns once CLI stabilizes).


## 2) Requirements (Consolidated)
- Terminal-first CLI (uv-run friendly): init, validate, plan, graph, run, list/show, edit, spawn, export/import, eval (later).
- YAML flow spec:
  - Agents: name, model (string or LiteLLM object), instruction, tools (function/MCP/OpenAPI), sub_agents, policies.
  - Workflow: sequential/parallel/loop or coordinator-child topology; declarative and composable.
  - Services: session, artifact, memory; in_memory, Redis, Mongo, DB, Vertex AI; artifacts in_memory, LocalFolder, S3, GCS.
  - Model providers: `model_providers` to set defaults per provider (api_base, api_key, headers) merged into agents’ LiteLLM configs.
  - Runtime: RunConfig (streaming mode, max_llm_calls, artifact capture, speech/audio config).
  - MCP: outbound server connections and tool allowlists; optional exposure of our tools as MCP servers later.
- Agentic authoring: an in-CLI “designer”/“ops” agent that can propose YAML edits and controlled file changes with approval.
- Runner lifecycle: build services → compose agents/flows → build Runner → run stream (interactive or scripted); resume sessions; save artifacts.
- Flow registry: versioned specs, tagging, run history, sessions, and artifact indices. Export/import of flow bundles.
- Security: env-first secrets, no plaintext in YAML; approval gates for agent-initiated writes; scope file ops; redact logs.
- Testing & CI: unit tests for schema/factories/tool adapters; integration tests for in-memory backends; optional examples for Redis/Mongo/S3.
- Docs: developer and operator guides, templates, and examples.


## 3) Proposed Solution (High-Level)
Architecture layers:
- CLI (Click): `flows`/`agents`/`tools`/`providers`/`registry` command groups.
- Config: Pydantic models, ENV interpolation, overlays, JSON Schema export; `configs/` with templates.
- Services: factories mapping YAML → ADK/adk-extra-services; shareable across flows.
- Tools: adapters for Python function tools (dotted imports), MCP tools, and OpenAPI tools.
- Agents: builders for `LlmAgent` leaves and ADK workflow agents (`SequentialAgent`/`ParallelAgent`/`LoopAgent`), or coordinator with `sub_agents`.
- Runtime: Runner manager (one per flow), streaming loop, session control, and run history plumbing.
- Registry: file-based registry (YAML + metadata) with optional artifact-backed storage (S3/LocalFolder) for sharing.
- Copilot: “designer” agent available via CLI subcommand to propose scaffold/edits/plans; changes applied via gated write-tools.
- Terminal UI (Textual): rich TUI with widgets (DataTable, Tree, TextArea, Inputs, Log, Command Palette) to design, visualize, and operate flows; optional `textual serve` to run in a browser.

Implementation principles:
- YAML-first, code-second; everything composable and testable.
- Provider-agnostic model layer via LiteLLM wrapper and direct ADK string registry.
- Minimal primitives first, grow capabilities behind stable CLI.
- Safety-first agentic edits: explicit user approvals.

### 3.1) Terminal UI with Textual (Key Decisions)
- Framework: Textual (App/Screens/Widgets with CSS-like styling, async-friendly). Install with `textual textual-dev`.
- Structure: one App with Screens: Dashboard, Flow Editor, Run Monitor, Logs/Artifacts, Provider/Secrets, Evaluations.
- Widgets: Header/Footer, TabbedContent, Tree/DirectoryTree (flows & sessions), DataTable (runs, artifacts), TextArea (YAML editor with optional syntax), Input/Button, Log for streaming events.
- Devtools: use `textual run --dev` for hot CSS reload; `textual console` for logs and prints; leverage Command Palette (Ctrl+P) for actions (open flow, run, validate, plan, save, export, etc.).
- Web: optional `textual serve "python -m src.tui"` to run TUI in a browser for demos.
- Theming: built-in themes for immediate polish; custom CSS in `tui/` folder.
- Background tasks: Textual workers for long operations (validate/plan/run) to keep UI responsive.
- Keybindings: predictable navigations (j/k, arrows), action names align with CLI verbs.


## 4) Detailed Implementation Plan (Phased)

### Phase M1 — Foundation (we’ve started; finish and harden)
Deliverables:
- CLI basics (DONE/EXTEND): `init`, `validate`, `plan`, `run`.
- Config (DONE/EXTEND): Pydantic schema, ENV interpolation, example writer, `model_providers` merge.
- Services (PARTIAL): session (in_memory, redis, mongo), artifacts (in_memory, local_folder, s3, gcs). Add memory wiring.
- Agents (DONE/EXTEND): string models + LiteLLM models; `sub_agents`. Add workflow agent types.
- Runtime: Map YAML runtime → ADK RunConfig.
- Tests: unit tests for schema, factories, model resolution, and supervisor; simple integration test (in-memory).
- Docs: AGENTS.md (DONE), plus `README` usage; add Models guide snippet.

Tasks:
1) Memory services
   - Add `MemoryServiceConfig` mapping: in_memory → `InMemoryMemoryService`; vertex_ai → `VertexAiMemoryBankService` with `project`, `location`, `agent_engine_id`.
   - Wire into Runner construction and CallbackContext.
2) RunConfig mapping
   - Map `runtime.streaming_mode`, `max_llm_calls`, `save_input_blobs_as_artifacts`, speech/audio configs to ADK `RunConfig` at runner/agent level.
3) Workflow agents
   - YAML support: `workflow.type: sequential|parallel|loop` and `workflow.nodes: [agent names]`.
   - Build `SequentialAgent` / `ParallelAgent` / `LoopAgent` with children from the agent map.
4) Function tools
   - YAML: `tools: [{type: function, ref: "package.module:func", name: optional, params: {}}]`.
   - Adapter: import dotted ref, wrap in ADK `FunctionTool` with optional parameter schema.
   - Attach tools to agents in builder.
5) CLI improvements
   - `flows graph`: ASCII/graphviz rendering of the agent/tool graph (inspired by `adk.cli.agent_graph`).
   - Error ergonomics: print validation paths and actionable hints.
6) Tests & docs
   - Unit tests for new factories and workflow compilation.
   - Example configs for: single agent (Gemini), OpenAI via LiteLLM, Ollama, sequential flow.

7) TUI bootstrap (Textual)
   - Minimal App: header/footer, left Tree (flows/sessions), right panel (status/log), command palette actions: validate/plan/run.
   - Wire plan/run commands to background workers; stream Runner events to a Log widget.

Acceptance:
- `uv run` can init → validate → plan → graph → run single and sequential flows for both Gemini and Ollama/OpenAI.
- Memory service selectable and searchable by agents (basic call path).
- `uv run --with textual --with textual-dev python -m src.tui` launches a basic TUI that validates / plans / runs flows.


### Phase M2 — Tools, MCP, and Copilot
Deliverables:
- MCP client tools: read `mcp[]`, connect to servers, add allowlisted tools to agents.
- OpenAPI tools: load specs and attach generated tool adapters.
- Copilot agent: `flows copilot` opens chat where the agent proposes edits to YAML, plans, and run changes; writes gated by approval.
- Registry operations: list/show/tag/version flows, run history, session list; export/import flow bundles.
- Profiles/overlays: dev/prod profiles with overrides and `.env` interpolation policies.

Tasks:
1) MCP integration
   - YAML: `mcp: [{name, host, port, token_env?, tool_allowlist: []}]`.
   - Adapter: connect MCP client per server; discover tools; filter by allowlist; expose to selected agents.
   - Optional: expose our tools via MCP server later (deferred unless needed).
2) OpenAPI tools
   - YAML: `tools: [{type: openapi, spec: path_or_url, select: [opIds], auth_env?: ...}]`.
   - Generate function tools using ADK OpenAPI integration; attach to agents.
3) Copilot agent
   - System prompt scoped to flow authoring semantics; tool access: read templates, propose YAML patches, validate/plan, request approval to apply.
   - CLI: `flows copilot` to converse; show diffs; `--auto-approve` optional.
4) Registry & runs
   - Flow store: `flows/` directory with versioned YAML and metadata; commands: `list`, `show`, `tag`, `rm`, `export`, `import`.
   - Run history: maintain index (flow id/version, session ids, timestamps, user id). CLI: `runs list/show/logs`.
5) Profiles/overlays
   - Simple overlay merge: `--profile dev|prod` to merge `configs/app.dev.yaml` onto base; or `--set key=val` inline.
6) TUI v2 (Textual)
   - Screens: Flow Editor with TextArea YAML + validation markers; Runs Monitor (DataTable); Artifacts browser; Providers/Secrets form.
   - Command Palette integration for common actions; persist window state; `textual console` logging enabled.

Acceptance:
- Can attach MCP tools from a running server; can import a small OpenAPI spec and call tools.
- Copilot can propose and apply changes to YAML with user approval.
- Flows are versioned, listable, and exportable; run history visible.
- TUI supports editing YAML, validating in-place, and running flows with live logs and artifact listing.


### Phase M3 — Dynamic Spawn, Policies, and Hardening
Deliverables:
- Dynamic spawn API: agents can propose new agents/flows during runtime; supervisor validates policy and registers them.
- Policies & quotas: limits on spawn depth, tool sets, resources; require approvals.
- Supervisor isolation options: per-flow Runner isolation (process), and pluggable backends.
- Evaluation hooks and CI sample pipelines.

Tasks:
1) Spawn mechanics
   - Add supervisor tool: `spawn_agent(spec)` / `spawn_flow(spec)` that writes a candidate spec file; requires human approval to register.
   - Registry updates: new version created with metadata for provenance (which agent/tool proposed it).
2) Policies & safety
   - Configurable policy module: allowed providers/backends/tools; max agents; max llm calls; rate limits.
   - Logging redaction; structured logs; audit trail of edits and runs.
3) Isolation
   - Optional process isolation for risky tools; configurable via YAML (exec runner vs in-process).
4) Eval & CI
   - Integrate with ADK eval flows and add sample GitHub Actions / make targets for lint, tests, and simple e2e job.

Acceptance:
- Agents can draft new agents/flows; registration requires approval; runs show provenance.
- Policy violations are prevented with clear errors; logs are sanitized.
- TUI adds spawn flows UI with policy prompts and approvals, plus evaluation views.


## 5) CLI Surface (Initial & Target)
Current:
- `init` (writes templates/app.yaml to configs/app.yaml)
- `validate`, `plan`, `run` (interactive)

Target (non-exhaustive):
- `flows init|new [--template T]` — scaffold a flow; wizard or template.
- `flows validate|plan|graph` — schema check/dry-run/visualize.
- `flows run [--flow F.yaml] [--user U] [--session S]` — run/resume.
- `flows list|show|tag|export|import` — registry management.
- `agents add|edit|rm` — agent operations inside a flow.
- `tools add function|mcp|openapi` — attach tools.
- `providers set <name> [kv...]` — update `model_providers` defaults.
- `runs list|show|logs` — run history.
- `copilot` — agent-assisted design with approvals.


## 6) Configuration Schema (YAML Sketch)
```yaml
services:
  session_service: {type: redis, redis_url: ${REDIS_URL}}
  artifact_service: {type: s3, bucket_name: my-bucket, endpoint_url: https://s3.amazonaws.com}
  memory_service: {type: in_memory}

model_providers:
  openai: {api_key: ${OPENAI_API_KEY}}
  ollama_chat: {api_base: ${OLLAMA_API_BASE}}

agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: Plan tasks.
    tools:
      - {type: function, ref: mypkg.tools:search_docs}
  - name: worker
    model: {type: litellm, model: openai/gpt-4o-mini}

workflow:
  type: sequential
  nodes: [planner, worker]

mcp:
  - name: db_toolbox
    host: localhost
    port: 8000
    tool_allowlist: [query_sql, list_tables]

runtime:
  streaming_mode: SSE
  max_llm_calls: 200
  save_input_blobs_as_artifacts: true
```


## 7) Security & Configuration Guidelines
- Secrets only via env; YAML interpolation supports `${VAR}`. Do not commit `.env`.
- Gate all agent-initiated writes with explicit user approvals.
- Restrict write tools to safe directories (`configs/`, `flows/`, `templates/`).
- Redact secrets in logs and diagnostics; avoid echoing headers/keys.
- Make isolation configurable (future): process-per-flow, tool sandboxes.


## 8) Testing & Validation Strategy
- Unit: schema validations (happy/sad), service factories, model resolution, workflow compilation, function tool loader.
- Integration: in-memory sessions/artifacts/memory; simple MCP mock; sample OpenAPI spec.
- E2E smoke: `uv run` flows from template (Gemini & Ollama paths).
- CI: ruff lint, pytest, minimal timeout budgets, optional matrix for Python 3.12/3.11.


## 9) Observability & UX
- CLI: clear errors with path hints, suggested fixes; `--verbose`/`--json` output options for scripting.
- Logs: timestamps, flow/run/session IDs; optional file logs per run.
- Graphs: simple ASCII and optional Graphviz DOT export.


## 10) Current Status (Baseline)
- Implemented: CLI (init/validate/plan/run/graph), config schema + env interpolation, provider defaults (`model_providers`), services (in_memory + redis/mongo; in_memory + local/s3/gcs; memory in_memory + vertex_ai), agent builder (string + LiteLLM + function tools), workflow composition (sequential/parallel/loop), supervisor, template, docs, minimal TUI stub.
- Verified runs: Gemini (GOOGLE_API_KEY) and LiteLLM→Ollama (`ollama_chat/gpt-oss:20b`).
- Tests: unit + CLI integration (6 passing).
- To finish M1: wire TUI actions; expand tests and error ergonomics.


## 11) Risks & Mitigations
- Provider variability (LiteLLM): standardize via provider defaults and strong error messages; docs with env tips.
- MCP complexity: start client-only, narrow allowlists; add exposure later.
- Agentic edits safety: strict approval flow with dry-run diffs; scoped write paths.
- Service credentialing: lean on env + cloud-native ADC; document clearly.


## 12) Milestones & Acceptance
- M1: Single/sequential flow, dual provider support (Gemini/LiteLLM), memory + runtime mapping, function tools, graphs, tests.
- M2: MCP/OpenAPI tools, copilot, registry + runs, profiles/overlays.
- M3: Dynamic spawn with policy, isolation, eval hooks, CI samples.


## 13) Next Actions
- Wire Textual TUI actions to validate/plan/run with background workers.
- Add more tests (workflow edges, DOT/ASCII output, invalid config paths).
- Begin MCP client tools adapter and OpenAPI tools schema (M2).
