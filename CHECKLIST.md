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

#### 1.1 LLM Agents (ADK: `LlmAgent` / `Agent`)

Flexible, language-centric agents that can decide tool use & delegation. ([Google GitHub][1])

```yaml
type: llm
name: string
description?: string
model?: alias://chat-default
instruction: string            # system prompt
tools?: (McpTool | OpenApiTool | FunctionTool | AgentTool)[]
sub_agents?: AgentRef[]        # for LLM-driven delegation / transfer
transfer?: {                   # optional hints
  allow_to_peers?: boolean
  allow_to_parent?: boolean
}
output_schema?: JSONSchema?    # optional tool-structured guardrails
```

* `AgentTool` wraps another declared agent (by ref) so an LLM agent can **explicitly invoke a sub-agent as a tool** (ADK’s pattern). ([Google GitHub][2])

#### 1.2 Workflow Agents (deterministic control)

Pure control-flow agents that orchestrate **sub\_agents** without LLM for flow control. ([Google GitHub][3])

* **SequentialAgent**

```yaml
type: workflow.sequential
name: string
description?: string
sub_agents: AgentRef[]   # run in order; shared invocation context
```

(Executes sub-agents one after another; pass state via invocation context.) ([Google GitHub][4])

* **ParallelAgent**

```yaml
type: workflow.parallel
name: string
description?: string
sub_agents: AgentRef[]   # run in parallel
merge?: AgentRef?        # optional merger agent to combine results
```

(Parallel orchestration + optional merger/aggregator step.) ([Google GitHub][5])

* **LoopAgent**

```yaml
type: workflow.loop
name: string
description?: string
body: AgentRef           # the agent to repeat
until: string            # termination condition (expression string)
max_iters?: int
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

### 4) Deterministic graph builder

`build_system_graph(cfg) -> { nodes: Node[], edges: Edge[] }`

* **Nodes**: `agent.llm`, `agent.workflow.sequential`, `agent.workflow.parallel`, `agent.workflow.loop`, `agent.custom`, `tool.mcp`, `tool.openapi`, `tool.function`, `tool.agent`.
* **Edges**:

  * `agent.llm → tool.*` (attached tools)
  * `agent.llm → agent.*` (sub\_agents; transfer/coordination)
  * `workflow.sequential → agent.*` (ordered)
  * `workflow.parallel → agent.*` (fan-out) and `→ merger?`
  * `workflow.loop → agent.*` (body)
* Emits `hints[]` for: missing model alias on LLMAgent, empty sub\_agents in workflow, loop without `until`, unresolved AgentRef, tool op not found.

### 5) Quick-fix catalog

`get_quick_fixes(validation_errors, cfg, indexes?) -> Fix[]`

* **LLM agent missing model** → add `model: alias://chat-default` (if default exists).
* **Sequential/Parallel agent with no sub\_agents** → insert placeholder sub\_agent stub.
* **Loop agent missing until** → add `until: "iteration >= 3"` template.
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
* **Graph determinism** across all ADK categories.
* **Ref/alias validation** (strict `registry://` & `alias://`).
* **Quick-fix** idempotency; suggestions from injected indexes.
* **Lock-plan determinism** given fixed resolves.
* **Perf**: `load_config()` P95 < **150ms**, `build_system_graph()` P95 < **100ms** for medium configs.

---

## Stages

**S1 — Types & Schema (ADK-aligned)**
Agent variants (`llm`, `workflow.*`, `custom`), tools, refs, backends; discriminators & validators.

**S2 — Graph Builder**
Node taxonomy + stable IDs; edges per ADK semantics; hints for missing model/sub\_agents/until.

**S3 — JSON Schema & Quick-fixes**
Export schema with docs; build quick-fix catalog keyed to common authoring mistakes.

**S4 — Lock-plan & Utilities**
Pure lock planner; fingerprints; dependency lister; comprehensive fixtures.

---

## Acceptance

* ADK-aligned **agent categories** parse & validate cleanly (LLM / Sequential / Parallel / Loop / Custom). ([Google GitHub][1])
* Graph renders deterministically with correct control-flow edges and helpful hints.
* Monaco JSON Schema produces precise markers & actionable quick-fixes.
* Lock-plan is deterministic given pre-resolved registry & alias inputs (no network/secrets in kit).

[1]: https://google.github.io/adk-docs/agents/?utm_source=chatgpt.com "Agents - Agent Development Kit"
[2]: https://google.github.io/adk-docs/agents/multi-agents/?utm_source=chatgpt.com "Multi-agent systems - Agent Development Kit"
[3]: https://google.github.io/adk-docs/agents/workflow-agents/?utm_source=chatgpt.com "Workflow Agents - Agent Development Kit"
[4]: https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/?utm_source=chatgpt.com "Sequential agents - Agent Development Kit"
[5]: https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/?utm_source=chatgpt.com "Parallel agents - Agent Development Kit"
[6]: https://google.github.io/adk-docs/tools/function-tools/?utm_source=chatgpt.com "Overview - Agent Development Kit"

