---
title: Configuration
---

# Configuration Schema

Top-level is `AppConfig` (Pydantic v2). Use `compose.export_app_config_schema()` to generate a JSON Schema for editors.

Key fields:
- `schema_version: string` — semver, e.g., `0.1.0`
- `metadata: { name, description?, labels?: map }`
- `defaults?: { model_alias?: string, runner_policy?: 'sandbox'|'burst', egress_policy?: string[] }`
- `model_aliases?: { aliases: ModelAliasEntry[] }`
- `registries?: { mcp?: RefOrInline[], openapi?: RefOrInline[], agents?: RefOrInline[], functions?: RefOrInline[] }`
- `agents: Agent[]`
- `backends?: { sessions?, memory?, artifacts? }` (declared only; not executed)

Ref types:
- `RegistryRef`: `registry://{kind}/{key}@{version|range|latest}` with kind ∈ {mcp, openapi, agent, function}
- `ModelAliasRef`: `alias://{name}`
- `RefOrInline<T>`: `{ ref: RegistryRef } | { inline: T }`

Model aliases (declarative):
- `ModelAliasEntry`:
  - `id`: alias name used by `alias://id`
  - `resolver`: `direct | litellm | class`
  - `model`: string (model id or endpoint; for litellm use provider-prefixed ids)
  - `class_ref?`: dotted `module:Class` (when `resolver: class`)
  - `params?`: runtime args (e.g., `api_base`, `extra_headers`)
  - `auth_ref?`: reference to secret/profile (e.g., `env:OPENAI_API_KEY`)
  - `provider?`, `labels?`, `description?`

Agents:
- `type: 'llm' | 'workflow.sequential' | 'workflow.parallel' | 'workflow.loop' | 'custom'`
- `llm` agents support: `model` (string or `ModelAliasRef`), `instruction` (required), `tools` (see Tools), `sub_agents`, `include_contents`, `input_schema`, `output_schema`, `output_key`, delegation booleans, `generate_content_config`, `planner`, `code_executor`, and callback lists.
- `workflow.*` agents orchestrate `sub_agents`; `loop` can limit iterations.
- `custom` declares a class path and params (visualization-only here).

Validation highlights:
- strict agent name pattern; duplicate agent names rejected
- dotted ref checks for schemas and class refs
- rich JSON Schema `markdownDescription` and error messages for editors

