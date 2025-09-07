Agent Compose Kit
=================

![CI](https://github.com/DeadMeme5441/agent-compose-kit/actions/workflows/ci.yml/badge.svg)
![Publish](https://github.com/DeadMeme5441/agent-compose-kit/actions/workflows/publish.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/agent-compose-kit.svg)](https://pypi.org/project/agent-compose-kit/)
[![Python Versions](https://img.shields.io/pypi/pyversions/agent-compose-kit.svg)](https://pypi.org/project/agent-compose-kit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Core Python library for YAML-driven construction of agent systems using Google ADK. This package provides configuration models, service factories, agent and tool builders, registries, runtime utilities, and a programmatic graph builder. It is designed to be consumed by external clients (CLI or web) that handle end-user interaction. No server, CLI, or TUI is included in this repo.

Features
- Config schema (Pydantic) with environment interpolation and provider defaults.
- Services (conservative defaults):
  - Sessions: in-memory (default), Redis (host/port/db/password or URL), Mongo, SQL (database_url), YAML file.
- Artifacts: in-memory (default), Local folder, S3, Mongo, SQL.
- Memory: in-memory (default), Redis, Mongo, SQL, YAML file.
- Agents: direct model IDs (Gemini/Vertex) or LiteLLM models (OpenAI, Anthropic, Ollama, vLLM), function tools, sub-agent wiring.
- Workflows: sequential, parallel, loop composition.
- Runtime: map YAML runtime to ADK RunConfig; build ADK Runner instances.
- Public API for external CLIs: system/session helpers, run helpers, env-based path helpers.

Design notes
- Conservative by default: when required service parameters are not provided, factories fall back to in-memory implementations (never attempt network/local resources silently).
- Provider defaults: `model_providers` merge into LiteLLM configs (e.g., OpenAI keys, API base) without overwriting explicit values.

Tools
- Function tools: `{type: function, ref: "module:callable", name?}`. The callable must be Python; for cross-language tools use MCP/OpenAPI below.
- MCP toolsets: connect to MCP servers via stdio/SSE/HTTP and expose their tools to agents.
- OpenAPI toolsets: generate `RestApiTool`s from an OpenAPI spec (inline/path/url with allowlist); agents can call REST APIs directly.
- Shared toolsets: define once under `toolsets:` and reference from agents with `{use: name}`.
- Registry references: reference MCP/OpenAPI toolsets declared under `mcp_registry` / `openapi_registry` via `{use: 'mcp:<id>'}`, `{use: 'mcp_group:<id>'}`, `{use: 'openapi:<id>'}`, `{use: 'openapi_group:<id>'}`.
- A2A remote agents: declare remote clients under `a2a_clients` and set `AgentConfig.kind: a2a_remote` + `client: <id>`.

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

      # Registry references (resolved when registries are provided)
      - {use: 'mcp:files'}
      - {use: 'mcp_group:default'}
      - {use: 'openapi:petstore'}
      - {use: 'openapi_group:public'}
```

Requirements
- Python 3.12+
- Optional extras at runtime depending on backends:
  - google-adk, google-adk-extras, litellm
  - For MCP stdio mode: `mcp` package (and any server requirements)

Install
- pip: `pip install agent-compose-kit`
- uv: `uv add agent-compose-kit`

Install (dev)
- uv sync

Quickstart (Programmatic)
```python
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.services.factory import build_session_service, build_artifact_service, build_memory_service
from agent_compose_kit.agents.builder import build_agents
from agent_compose_kit.runtime.supervisor import build_plan, build_run_config

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

Registries (Tools & Agents)
- Define reusable tools and agents in your config, then build registries:
```python
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.tools.builders import build_tool_registry_from_config
from agent_compose_kit.agents.builders_registry import build_agent_registry_from_config

cfg = load_config_file(Path("configs/app.yaml"))
tool_reg = build_tool_registry_from_config(cfg, base_dir=".")
agent_reg = build_agent_registry_from_config(cfg, base_dir=".", provider_defaults=cfg.model_providers, tool_registry=tool_reg)

root = agent_reg.get("parent")  # or agent_reg.get_group("core")[0]
```

MCP/OpenAPI Registries (Config)
```yaml
mcp_registry:
  servers:
    - id: files
      mode: sse        # sse|stdio|http
      url: http://localhost:3000/sse
      headers: {Authorization: 'Bearer ${TOKEN}'}
      tool_filter: [list_directory, read_file]
  groups:
    - {id: default, include: [files]}

openapi_registry:
  fetch_allowlist: ["api.example.com", "*.trusted.com"]
  apis:
    - id: petstore
      spec: {path: ./specs/petstore.yaml}   # or inline: "{...}" or url: https://api.example.com/openapi.json
      spec_type: yaml
      tool_filter: []
  groups:
    - {id: public, include: [petstore]}
```

A2A Remote Agents (Config)
```yaml
a2a_clients:
  - id: my_remote
    url: https://remote.agents.example.com
    headers: {Authorization: 'Bearer ${A2A_TOKEN}'}

agents:
  - name: remote
    kind: a2a_remote
    client: my_remote
    model: gemini-2.0-flash  # still allowed but ignored by remote
```

Public API (for external CLI)
- Build a system and run a message:
```python
from pathlib import Path
from agent_compose_kit.api.public import SystemManager, SessionManager, run_text, event_to_minimal_json

sm = SystemManager(base_dir=Path("./systems/my_system"))
cfg = sm.load("config.yaml")
runner, _resources = sm.build_runner(cfg)

import asyncio

async def main():
    sess = await SessionManager(runner).get_or_create(user_id="u1")
    async for ev in run_text(runner=runner, user_id="u1", session_id=sess.id, text="hello"):
        print(event_to_minimal_json(ev))

asyncio.run(main())
```

Environment variables (optional)
- `AGENT_SYS_DIR`: root directory where systems live (default `./systems`).
- `AGENT_OUTPUTS_DIR`: root directory for outputs/artifacts (default `./outputs`).
- `AGENT_SESSIONS_URI`: default sessions storage URI (default `sqlite:///./sessions.db`).

System Graph (Programmatic)
```python
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.graph.build import build_system_graph

cfg = load_config_file(Path("configs/app.yaml"))
graph = build_system_graph(cfg)
print(graph["nodes"], graph["edges"])  # nodes/edges dicts
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
- `src/tools/registry.py` — global ToolRegistry (ids, groups, caching, close_all).
- `src/agents/registry.py` — global AgentRegistry (ids, groups, sub-agent wiring).
- `src/agents/builders_registry.py` — helpers to build AgentRegistry from AppConfig.
- `src/tools/builders.py` — helpers to build ToolRegistry from AppConfig.
 - `src/tools/mcp_registry.py` — McpRegistry for building/caching MCP toolsets.
 - `src/tools/openapi_registry.py` — OpenAPIRegistry for building/caching OpenAPI toolsets.
- `src/registry/fs.py` — filesystem helpers for saving/loading systems.
 - `src/api/public.py` — public API for external CLIs (SystemManager, SessionManager, run helpers).
 - `src/paths.py` — path/env helpers (AGENT_SYS_DIR, AGENT_OUTPUTS_DIR, AGENT_SESSIONS_URI).

Schema & Registry
- Export AppConfig JSON schema programmatically:
  - `from agent_compose_kit.config.models import export_app_config_schema`
- Save/load system configs:
  - `from agent_compose_kit.registry.fs import save_system, load_system, list_systems, list_versions, promote`
- `src/runtime/supervisor.py` — plan summary, Runner construction, RunConfig mapping.
- `templates/app.yaml` — example config template.

Roadmap
- See `FULL_IMPLEMENTATION_PLAN.md` for detailed milestones (MCP/OpenAPI toolsets, JSON Schema export, registry helpers, observability hooks).

Optional Dependencies
- `mcp` for MCP stdio mode
- `requests` for OpenAPI URL fetching (when using `spec.url`)

Service Config: URI vs dict
```yaml
services:
  # URI strings are accepted and parsed into structured configs
  session_service: "sqlite:///./sessions.db"       # or "redis://localhost:6379/0", "mongodb://localhost/adk"
  artifact_service: "file://./artifacts"           # or "s3://my-bucket/prefix", "sqlite:///./artifacts.db"
  # memory service optional
  # memory_service: "redis://localhost:6379/0"
```

Equivalent programmatic usage:
```python
from agent_compose_kit.services.factory import build_session_service, build_artifact_service

session = build_session_service("sqlite:///./sessions.db")
artifacts = build_artifact_service("file://./artifacts")
```

License
MIT

Publishing plan (summary)
- Finalize metadata in `pyproject.toml`: project name, description, license, classifiers, homepage/repo URLs, keywords.
- Optional extras: define `[project.optional-dependencies]` for `tools` and `dev`.
- Versioning: adopt SemVer; tag releases in VCS (e.g., v0.1.0).
- Build: `python -m build` (ensure `build` in dev deps) or `uv build`.
- Publish: `twine upload dist/*` (or GitHub Actions workflow for publish-on-tag).
- Docs: keep README as long_description; ensure `README.md` renders on PyPI.
- CI: add GitHub Actions for lint/test on PR; optional publish job on tag.
