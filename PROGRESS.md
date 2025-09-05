# Project Progress

## Summary
This repository now scaffolds a YAML‑driven wrapper around Google ADK with provider‑agnostic model support (Gemini + LiteLLM), service factories (sessions/artifacts/memory), basic workflow composition, function tools, and a graph utility. TUI and CLI have been removed to keep this project core‑only. A test suite covers core library behaviors.

## Implemented
- Config
  - Pydantic YAML schema with env interpolation and provider defaults (`model_providers`).
  - Example writer (`init`) and back‑compat for `services:` root.
- Services
  - Sessions: in_memory, Redis (`RedisSessionService`), Mongo (`MongoSessionService`).
  - Artifacts: in_memory, LocalFolder, S3, GCS.
  - Memory: in_memory, Vertex AI Memory Bank.
- Models
  - Direct strings (Gemini / Vertex endpoint).
  - LiteLLM models with provider defaults (OpenAI, Anthropic, Ollama, vLLM).
- Agents & Workflows
  - `LlmAgent` leaves; `workflow` YAML composes Sequential/Parallel/Loop agents.
  - Function tools via `{type:function, ref: module:function, name?}`.
- Runtime
  - YAML `runtime` → ADK `RunConfig` (streaming mode, max calls, artifact capture).
- CLI
  - Removed. Use programmatic API.
- TUI
  - Removed. Focus is core library only.
- Tests (pytest)
  - Unit tests: config/env, run config, function tools, workflow composition.

## How to Use
- Setup: `uv sync`
- Tests: `uv run --with pytest pytest -q`

## Next Milestones
- M1 finish
  - Expand tests: workflow edge cases, graph output, error paths.
- M2
  - MCP client tools (attach allowlisted tools from servers) and OpenAPI tools.
  - Registry: list/show/tag/export/import; run history & sessions.
- M3
  - Dynamic spawn mechanics with policy & quotas; optional process isolation.
  - Evaluation hooks and CI workflows.

## Dev Notes
- Add dependencies: `uv add <package>` (use `--dev` for dev tools).
- Lint/format: `uv run --with ruff ruff check .` / `ruff format .`.
- Keep changes minimal and focused; update docs/tests alongside features.
