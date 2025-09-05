# Project Progress

## Summary
This repository now scaffolds a YAML‑driven wrapper around Google ADK with a uv‑first CLI, provider‑agnostic model support (Gemini + LiteLLM), service factories (sessions/artifacts/memory), basic workflow composition, function tools, a graph view, and a minimal Textual TUI stub. A test suite covers core behaviors and CLI flows.

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
- CLI (Click)
  - `init`, `validate`, `plan`, `graph` (ASCII/DOT), `run` (interactive stream).
- TUI (Textual)
  - Minimal stub in `src/tui.py` (status log, keybindings), ready to wire actions.
- Tests (pytest)
  - Unit and CLI integration: config/env, run config, function tools, workflow composition, CLI commands. 6 tests passing.

## How to Use
- Setup: `uv sync`
- CLI help: `uv run python -m src.main --help`
- Init/validate/plan:
  - `uv run python -m src.main init`
  - `uv run python -m src.main validate configs/app.yaml`
  - `uv run python -m src.main plan configs/app.yaml`
- Graph:
  - ASCII: `uv run python -m src.main graph configs/app.yaml`
  - DOT: `uv run python -m src.main graph configs/app.yaml --dot`
- Run:
  - Gemini: `export GOOGLE_API_KEY=...`
  - `uv run --with google-adk python -m src.main run configs/app.yaml`
  - LiteLLM (e.g., Ollama): `export OLLAMA_API_BASE=http://127.0.0.1:11434` then `uv run --with google-adk --with litellm python -m src.main run configs/app.yaml`
- TUI (stub): `uv run --with textual --with textual-dev python -m src.tui`
- Tests: `uv run --with pytest pytest -q`

## Next Milestones
- M1 finish
  - Wire TUI actions (validate/plan/run) with background workers.
  - Expand tests: workflow edge cases, graph output, error paths.
- M2
  - MCP client tools (attach allowlisted tools from servers) and OpenAPI tools.
  - Copilot agent (design/ops) with approval‑gated edits.
  - Registry: list/show/tag/export/import; run history & sessions.
  - TUI v2: YAML editor, runs monitor, artifacts browser, providers/secrets forms.
- M3
  - Dynamic spawn mechanics with policy & quotas; optional process isolation.
  - Evaluation hooks and CI workflows.

## Dev Notes
- Add dependencies: `uv add <package>` (use `--dev` for dev tools).
- Lint/format: `uv run --with ruff ruff check .` / `ruff format .`.
- Keep changes minimal and focused; update docs/tests alongside features.
