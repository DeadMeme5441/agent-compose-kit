Changelog
=========

All notable changes to this project will be documented in this file.

0.2.1 - A2A agent-card support (docs + compat)
-----------------------------------------------
- Update A2A remote agent wiring to prefer `agent_card` (AgentCard or URL) for `RemoteA2aAgent`.
- Config: add `agent_card_url` to `A2AClientConfig` (keep `url` as backward-compatible alias treated as an agent-card URL).
- Docs: README A2A examples now use `agent_card_url`; added migration note.
- Tests/lint: green.

0.2.0 - Programmatic-only library; registries & URIs
----------------------------------------------------
- BREAKING: remove all FastAPI/server scaffolding; repo is library-only.
- New: `graph.build_system_graph(cfg)` for UI graphs (no HTTP required).
- New: `parse_service_uri` and URI support for session/artifact/memory configs.
- New: registry discovery methods (`list_*`) on Tool/MCP/OpenAPI/Agent registries.
- Public API hardened: `SystemManager`, `SessionManager`, `run_text`, `event_to_minimal_json`.
- Docs: programmatic-only README with service URI examples and graph usage.
- Lint/tests: ruff clean, 70+ tests green.

0.1.0 - Initial release
-----------------------
- First public release as `agent-compose-kit`.
- YAML → ADK services, tools, agents, workflows, and RunConfig.
- Unified tool loader for function/MCP/OpenAPI (optional deps guarded).
- Basic documentation and examples.
