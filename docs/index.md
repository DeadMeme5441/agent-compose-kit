---
title: Agent Compose Kit
---

# Agent Compose Kit

Agent Compose Kit is a pure, declarative configuration and validation layer for Google ADK agent systems. It is designed to be the single source of truth for system YAMLs that a backend service or editor can consume without any runtime side-effects.

- Strict Pydantic v2 schema for agents, tools, registries, and defaults
- Deterministic graph builder with actionable hints
- Monaco-friendly JSON Schema exporter
- Quick-fix catalog that proposes JSON-Pointer patches
- Lock-plan generator for pinning external refs and model aliases (offline)
- Unified Python facade for programmatic use (no server)

Note: This package intentionally performs no network I/O, execution, or secret handling. It validates and structures configs; your runtime maps them to live ADK objects.

## What’s in scope
- Configuration parsing and rich errors
- Tool/Agent variants aligned with ADK (including toolsets and built‑ins)
- Model alias registry with LiteLLM and class-based resolvers
- Graph, quick-fixes, lock planning, utilities (fingerprint, lint, deps)

## What’s not in scope
- Running agents, services, or executing tools
- Secret management and network access
- ADK/extras adapters (kept under `_retired/` for reference)

## Quick links
- Install: [Installation](install.md)
- Schema: [Configuration](config.md)
- Agents: [Agents](agents.md)
- Tools: [Tools](tools.md)
- Registries: [Registries](registries.md)
- Graph: [Graph](graph.md)
- Quick-fixes: [Quick Fixes](quickfixes.md)
- Lock plan: [Plan Lock](plan_lock.md)
- API: [Compose API](api.md)
- Examples: [Examples](examples.md)

