Changelog
=========

All notable changes to this project will be documented in this file.

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
