# agent-compose-kit — Plan (Updated for ADK Agent Categories)

## Purpose

Be the **single source of truth** for the Agentic Composer **system YAML**—aligned with **Google ADK’s core agent categories**: **LLM Agents**, **Workflow Agents** (Sequential / Parallel / Loop), and **Custom Agents**. Provide strict parsing, deterministic graph building, Monaco-ready JSON Schema, and a practical quick-fix catalog. No I/O, no secrets, no execution—**pure validation & structure**. ([Google GitHub][1])

---

## Deliverables

### 1) Typed config model (Pydantic v2)

**Top-level**

* `schema_version: semver`
* `metadata: { name, description?, labels?: map<string,string> }`
* `defaults?: { model_alias?: string, runner_policy?: 'sandbox'|'burst', egress_policy?: string[] }`
* `registries?: { mcp?: RefOrInline[], openapi?: RefOrInline[], agents?: RefOrInline[], functions?: RefOrInline[] }`
* `agents: Agent[]`  ← **primary composition unit (matches ADK)** ([Google GitHub][1])

**Reference types**

* `RegistryRef` → `registry://{kind}/{key}@{range|version|latest}`
  `kind ∈ {mcp, openapi, agent, function}`
* `ModelAliasRef` → `alias://{alias_name}` (BYOK-friendly; **no provider names**)
* `RefOrInline<T>` → `{ ref: RegistryRef } | { inline: T }`

---

#### 1.1 LLM Agents (ADK: `LlmAgent`)

Flexible, language-centric agents that can decide tool use & delegation. ([Google GitHub][1])

Required
- `type: llm`
- `name: string`
- `instruction: string`

Supported fields (ADK-aligned; all Optional unless noted)
- `description`
- `model: string | alias://name`
- `tools: (McpTool | OpenApiTool | FunctionTool | AgentTool)[]`
- `sub_agents: AgentRef[]`
- `include_contents: 'default' | 'none'`
- `input_schema: 'module:Class' | 'module.Class'` (agent-as-tool input)
- `output_schema: 'module:Class'` (structured replies; disables tools at runtime)
- `output_key: string` (session state key for downstream steps)
- `disallow_transfer_to_parent: boolean`
- `disallow_transfer_to_peers: boolean`
- `generate_content_config: object` (non-thinking tuning)
- `planner: { type: 'built_in', thinking_config: {...} } | { type: 'plan_react' }`
- `code_executor: 'module:Class'`
- Callbacks (lists of dotted refs):
  - `before_model_callbacks`, `after_model_callbacks`, `before_tool_callbacks`, `after_tool_callbacks`
- `global_instruction: string` (root-only advisory)

Notes
- `AgentTool` wraps another agent so an LLM can explicitly invoke it as a tool. ([Google GitHub][2])
- Graph hints: (a) output_schema + tools → tools disabled at runtime; (b) missing `output_key` in sequential pipelines.

#### 1.2 Workflow Agents (deterministic control)

Pure control-flow agents that orchestrate **sub\_agents** without LLM for flow control. ([Google GitHub][3])

* **SequentialAgent** (ADK: sub_agents, optional before/after callbacks)

```yaml
type: workflow.sequential
name: string
description?: string
sub_agents: AgentRef[]
before_agent_callback?: string | string[]
after_agent_callback?: string | string[]
```

(Executes sub-agents one after another; pass state via invocation context.) ([Google GitHub][4])

* **ParallelAgent** (ADK: sub_agents, optional before/after callbacks)

```yaml
type: workflow.parallel
name: string
description?: string
sub_agents: AgentRef[]
before_agent_callback?: string | string[]
after_agent_callback?: string | string[]
```

(Parallel orchestration; synthesis is typically a subsequent step, not a field.) ([Google GitHub][5])

* **LoopAgent** (ADK: iterates sub_agents; stops on escalate or `max_iterations`)

```yaml
type: workflow.loop
name: string
description?: string
sub_agents: AgentRef[]   # run each iteration in order
max_iterations?: int
before_agent_callback?: string | string[]
after_agent_callback?: string | string[]
```

> All **sub\_agents/AgentRef** must resolve to agents defined in the same document (or via `RegistryRef` of kind `agent`). The kit **does not** execute them.

#### 1.3 Custom Agents (ADK: subclasses of `BaseAgent`)

Escape hatch for bespoke control logic. ([Google GitHub][1])

```yaml
type: custom
name: string
class: string            # import path (runtime will import)
params?: object          # JSON-serializable constructor args
```

---

#### 1.4 Tools (attachable to LLM Agents or used inside custom/flow agents)

* **MCP Tool**

```yaml
kind: mcp
server: RefOrInline<McpServer>
tool: string                  # as exposed by list_tools
config?: object
```

* **OpenAPI Tool**

```yaml
kind: openapi
spec: RefOrInline<OpenApiSpec>
operationId: string
parameters?: object
body?: object
headers?: map<string,string>
auth_config?: { auth_scheme: string, params?: object }
```

* **Function Tool** (function-calling)

```yaml
kind: function
function: RefOrInline< { import: "pkg.mod:fn" } | { code: string, deps?: string[] } >
signature?: { input_schema?: JSONSchema, output_schema?: JSONSchema }
policy?: { isolation?: 'sandbox'|'burst', timeout_s?: int, mem_mb?: int }
```

*(Shapes are declarative only; the kit never executes.)* ([Google GitHub][6])

* **Agent Tool** (wrap an agent as a callable tool)

```yaml
kind: agent
agent: AgentRef
```

(Explicit invocation alternative to LLM transfer.) ([Google GitHub][2])

---

#### 1.5 Shared backends (declared only)

```yaml
sessions?: { kind: 'sql'|'redis'|'memory', label?: string }
memory?:   { kind: 'sql'|'redis'|'none' }
artifacts?:{ kind: 's3'|'fs'|'none', label?: string }
```

---

### 2) JSON Schema exporter

`export_app_config_schema() -> dict`

* `$defs` for agent **variants** (`llm`, `workflow.sequential`, `workflow.parallel`, `workflow.loop`, `custom`), tools, refs, backends.
* Rich `markdownDescription`, `examples`, and `errorMessage` for Monaco code actions.

### 3) Strict parser with rich errors

`load_config(yaml_or_dict) -> AppConfig`

* Enforces variant discriminators (`type`) and required fields per ADK category.
* Normalizes defaults; reports path-aware, suggestion-rich errors.

### 4) Deterministic graph builder (S2 done)

`build_system_graph(cfg) -> { nodes: Node[], edges: Edge[] }`

* **Nodes**: `agent.llm`, `agent.workflow.sequential`, `agent.workflow.parallel`, `agent.workflow.loop`, `agent.custom`, `tool.mcp`, `tool.openapi`, `tool.function`, `tool.agent`.
* **Edges**:

  * `agent.llm → tool.*` (attached tools)
  * `agent.llm → agent.*` (sub\_agents; transfer/coordination)
  * `workflow.sequential → agent.*` (ordered)
  * `workflow.parallel → agent.*` (fan-out)
  * `workflow.loop → agent.*` (iterates sub_agents)
* Emits `hints[]` for: missing model alias on LLMAgent, empty sub\_agents in workflow, loop without `until`, unresolved AgentRef, tool op not found.
* S2 Hints implemented:
  * LLM missing model and no defaults.model_alias
  * LLM with output_schema + tools (tools disabled at runtime)
  * Sequential: upstream LLM with no output_key (downstream may lack inputs)
  * PlanReAct with output_schema (conflict)
  * BuiltInPlanner + thinking_config under generate_content_config (suggest move to planner)

### 5) Quick-fix catalog (S3 target)

`get_quick_fixes(validation_errors, cfg, indexes?) -> Fix[]`

* **LLM agent missing model** → add `model: alias://chat-default` (if default exists).
* **Sequential/Parallel agent with no sub\_agents** → insert placeholder sub\_agent stub.
* (Removed) Loop `until` — align with ADK: use `max_iterations` and escalate semantics only.
* **Unknown AgentRef** → create stub agent or fix to closest name.
* **Unknown operationId/tool** → suggest from provided `SpecIndex` / `ToolIndex`.
* **No egress/runner defaults** → add to `defaults`.
  *(Indexes are optional, injected by the backend; kit stays offline.)*

### 6) Lock-plan helper (pure)

`plan_lock(cfg, registry_resolves, alias_resolves) -> LockfilePlan`

* **Inputs** (provided by backend, no network):

  * `registry_resolves: (kind,key,range) -> {version, etag?, uri?}`
  * `alias_resolves: alias -> {provider, model, secret_ref}` (ref only)
* **Output**: `{ registryPins, aliasPins }` deterministic structure for later persistence.

### 7) Utilities

* `fingerprint(cfg) -> sha256`
* `list_dependencies(cfg) -> { registryRefs:[], modelAliases:[], agentRefs:[] }`
* `lint(cfg) -> { warnings:[], infos:[] }`

---

## Tests

* **Schema round-trip** (Pydantic ↔ YAML), variant discriminators honored.
* **Graph determinism** across all ADK categories (S2 covered).
* **Ref/alias validation** (strict `registry://` & `alias://`).
* **Quick-fix** idempotency; suggestions from injected indexes.
* **Lock-plan determinism** given fixed resolves.
* **Perf**: `load_config()` P95 < **150ms**, `build_system_graph()` P95 < **100ms** for medium configs.

---

## Stages

**S1 — Types & Schema (ADK-aligned)**
Agent variants (`llm`, `workflow.*`, `custom`), tools, refs, backends; discriminators & validators.

**S2 — Graph Builder**
Node taxonomy + stable IDs; edges per ADK semantics; hints for missing model, output_schema/tools, missing output_key, planner conflicts, unresolved refs.

**S3 — JSON Schema & Quick-fixes**
Export schema with docs; build quick-fix catalog keyed to common authoring mistakes.

**S4 — Lock-plan & Utilities**
Pure lock planner; fingerprints; dependency lister; comprehensive fixtures.

---

## Acceptance

* ADK-aligned **agent categories** parse & validate cleanly (LLM / Sequential / Parallel / Loop / Custom). ([Google GitHub][1])
* Graph renders deterministically with correct control-flow edges and helpful hints (S2 implemented).
* Monaco JSON Schema produces precise markers & actionable quick-fixes.
* Lock-plan is deterministic given pre-resolved registry & alias inputs (no network/secrets in kit).

[1]: https://google.github.io/adk-docs/agents/?utm_source=chatgpt.com "Agents - Agent Development Kit"
[2]: https://google.github.io/adk-docs/agents/multi-agents/?utm_source=chatgpt.com "Multi-agent systems - Agent Development Kit"
[3]: https://google.github.io/adk-docs/agents/workflow-agents/?utm_source=chatgpt.com "Workflow Agents - Agent Development Kit"
[4]: https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/?utm_source=chatgpt.com "Sequential agents - Agent Development Kit"
[5]: https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/?utm_source=chatgpt.com "Parallel agents - Agent Development Kit"
[6]: https://google.github.io/adk-docs/tools/function-tools/?utm_source=chatgpt.com "Overview - Agent Development Kit"
