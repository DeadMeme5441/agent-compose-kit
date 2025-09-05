Changelog
=========

All notable changes to this project will be documented in this file.

Unreleased
----------
- Add public API (SystemManager, SessionManager, run_text, CancelRegistry).
- Normalize root agent name to `root_agent` across builders/server/scaffold.
- Support advanced LlmAgent options (description, include_contents, output_key,
  generate_content_config, planner, code_executor, input_schema/output_schema).
- Add env/path helpers (AGENT_SYS_DIR, AGENT_OUTPUTS_DIR, AGENT_SESSIONS_URI).
- Add Tool/Agent registries and filesystem registry helpers.
- Thin FastAPI server wrapper and ADK FastAPI scaffolding utilities.
- Comprehensive tests and docs; CI and publish workflows.

0.1.0 - Initial release
-----------------------
- First public release as `agent-compose-kit`.
- YAML → ADK services, tools, agents, workflows, and RunConfig.
- Unified tool loader for function/MCP/OpenAPI (optional deps guarded).
- Basic documentation and examples.

