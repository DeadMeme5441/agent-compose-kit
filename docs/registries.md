---
title: Registries
---

# Registries

This package includes pure declarative registries that validate and organize specs. They do not execute or import runtime dependencies.

## Model Alias Registry
AppConfig: `model_aliases: { aliases: ModelAliasEntry[] }`

Alias entry fields:
- `id`: alias name (used as `alias://id`)
- `resolver`: `direct | litellm | class`
- `model`: model id or endpoint (for `direct`/`class`), provider-prefixed for `litellm`
- `class_ref?`: dotted `module:Class` (when `resolver: class`)
- `params?`: runtime parameters (no secrets) — e.g., `api_base`, `extra_headers`
- `auth_ref?`: a reference to a secret/profile (e.g., `env:OPENAI_API_KEY`)
- `provider?`, `labels?`, `description?`

Validation helper:
`compose.validate_aliases(cfg.model_dump()) -> { unknown_aliases: [...] }`

## Agents Registry (declarative)
`DeclarativeAgentRegistry(spec)` with shape:
```yaml
agents:
  - { id: planner, type: llm, name: planner, instruction: plan }
groups:
  - { id: core, include: [planner] }
```
APIs: `get(id)`, `get_group(id)`, `list_ids()`, `list_groups()`

## Tools Registry (declarative)
`DeclarativeToolRegistry(spec)` with shape:
```yaml
tools:
  - { id: sum, kind: function, function: { import: tests.helpers:sample_tool } }
groups:
  - { id: default, include: [sum] }
```
APIs: `get(id)`, `get_group(id)`, `list_ids()`, `list_groups()`

