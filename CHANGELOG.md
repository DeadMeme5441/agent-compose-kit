Changelog
=========

All notable changes to this project will be documented in this file.

0.5.0 - ADK-parity config, graph, quick-fixes, lock plan, docs
----------------------------------------------------------------
- S3: Schema polish (JSON Schema error messages), quick-fix catalog (missing model alias, sequential output_key, thinking_config move to planner, plan_react conflict, unknown operationId suggestions, declare missing aliases).
- S4: Lock plan with registryPins and aliasPins (resolver + params_fingerprint), utilities (fingerprint, lint, list_dependencies) via unified facade.
- S5: Tool fidelity with ADK: long_running function flag; ToolAuthConfig.auth_credential; OpenAPI/MCP/APIHub toolsets; built-in tools; graph nodes for new kinds.
- S6: Model Alias Registry (direct|litellm|class) + validate_aliases helper; quick-fix support; plan_lock alias pin enhancements.
- Unified facade compose.py exporting core API (schema, graph, quickfix, lock, utils).
- Declarative registries for tools and agents; tests.
- Retire runtime adapters into _retired/ namespace (no runtime side-effects in core).
- Regenerate docs to match runtime-free surface.

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
