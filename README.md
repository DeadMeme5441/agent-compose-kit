Template Agent Builder (Core)
================================

Core Python library for YAML-driven construction of agent workflows using Google ADK. This package provides configuration models, service factories, agent builders, and runtime utilities to compose and run multi-agent flows programmatically. No CLI or TUI is included.

Features
- Config schema (Pydantic) with environment interpolation and provider defaults.
- Services (conservative defaults):
  - Sessions: in-memory (default), Redis, Mongo, Database (SQLAlchemy URL).
  - Artifacts: in-memory (default), Local folder, S3, GCS.
  - Memory: in-memory (default), Vertex AI (falls back to in-memory if missing params).
- Agents: direct model IDs (Gemini/Vertex) or LiteLLM models (OpenAI, Anthropic, Ollama, vLLM), function tools, sub-agent wiring.
- Workflows: sequential, parallel, loop composition.
- Runtime: map YAML runtime to ADK RunConfig; build ADK Runner instances.

Design notes
- Conservative by default: when required service parameters are not provided, factories fall back to in-memory implementations (never attempt network/local resources silently).
- Provider defaults: `model_providers` merge into LiteLLM configs (e.g., OpenAI keys, API base) without overwriting explicit values.

Tools
- Function tools: `{type: function, ref: "module:callable", name?}`. The callable must be Python; for cross-language tools use MCP/OpenAPI below.
- MCP toolsets: connect to MCP servers via stdio/SSE/HTTP and expose their tools to agents.
- OpenAPI toolsets: generate `RestApiTool`s from an OpenAPI spec (inline/path); agents can call REST APIs directly.
- Shared toolsets: define once under `toolsets:` and reference from agents with `{use: name}`.

YAML Examples (Tools)
```yaml
toolsets:
  # Reusable MCP toolset via stdio (requires `mcp` package installed)
  fs_tools:
    type: mcp
    mode: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./sandbox"]
    tool_filter: [list_directory, read_file]

agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: Use tools when appropriate.
    tools:
      # Function tool (Python callable)
      - {type: function, ref: tests.helpers:sample_tool, name: add}
      # Reuse shared toolset
      - {use: fs_tools}

  - name: api_caller
    model: gemini-2.0-flash
    instruction: Use REST API tools.
    tools:
      - type: openapi
        spec:
          path: ./specs/petstore.yaml  # or inline: "{...}" (json/yaml)
        spec_type: yaml  # json|yaml; inferred from path extension when omitted
        tool_filter: []
```

Requirements
- Python 3.12+
- Optional extras at runtime depending on backends:
  - google-adk, adk-extra-services, litellm
  - For MCP stdio mode: `mcp` package (and any server requirements)

Install (dev)
- uv sync

Quickstart (Programmatic)
```python
from pathlib import Path
from src.config.models import load_config_file
from src.services.factory import build_session_service, build_artifact_service, build_memory_service
from src.agents.builder import build_agents
from src.runtime.supervisor import build_plan, build_run_config

cfg = load_config_file(Path("configs/app.yaml"))
print(build_plan(cfg))

artifact_svc = build_artifact_service(cfg.artifact_service)
session_svc = build_session_service(cfg.session_service)
memory_svc = build_memory_service(cfg.memory_service)

agents = build_agents(cfg.agents, provider_defaults=cfg.model_providers)
root = agents[cfg.workflow.nodes[0]] if (cfg.workflow and cfg.workflow.nodes) else agents[cfg.agents[0].name]

from google.adk.runners import Runner
runner = Runner(app_name="template-agent-builder", agent=root, artifact_service=artifact_svc, session_service=session_svc, memory_service=memory_svc)
rc = build_run_config(cfg)
# Use runner in your application according to ADK docs
```

YAML Example
```yaml
services:
  session_service: {type: in_memory}
  artifact_service: {type: local_folder, base_path: ./artifacts_storage}

agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: You are a helpful planner.
    tools: []

workflow:
  type: sequential
  nodes: [planner]

runtime:
  streaming_mode: NONE
  max_llm_calls: 200
```

Testing
- Run all tests: `uv run --with pytest pytest -q`
- Current coverage includes config/env interpolation, service factories (with in-memory fallbacks), function tool loading, workflow composition, and RunConfig mapping.
- Cloud-backed integrations (e.g., GCS) are skipped unless credentials are configured.

Development
- Lint: `uv run --with ruff ruff check .`
- Format: `uv run --with ruff ruff format .`
- Tests: `uv run --with pytest pytest -q`

Project Structure
- `src/config/models.py` — Pydantic models, env interpolation, example writer.
- `src/services/factory.py` — session/artifact/memory service builders.
- `src/agents/builder.py` — model resolution (string/LiteLLM), function tools, sub-agent wiring.
- `src/tools/loader.py` — unified loader for function/MCP/OpenAPI tools and shared toolsets.
- `src/runtime/supervisor.py` — plan summary, Runner construction, RunConfig mapping.
- `templates/app.yaml` — example config template.

Roadmap
- See `FULL_IMPLEMENTATION_PLAN.md` for detailed milestones (MCP/OpenAPI toolsets, JSON Schema export, registry helpers, observability hooks).

License
Apache-2.0
