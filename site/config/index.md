# Configuration

Configs are Pydantic-based and support environment variable interpolation.

Load and validate

```
from pathlib import Path
from agent_compose_kit.config.models import load_config_file

cfg = load_config_file(Path("configs/app.yaml"))
```

Top-level shape (AppConfig)

- services: `session_service`, `artifact_service`, `memory_service` — each accepts a dict or a URI string.
- model_providers: defaults merged into LiteLLM model definitions.
- toolsets: shared toolsets reusable by agents.
- agents, groups, workflow: define agent graph and composition.
- registries: `tools_registry`, `agents_registry`, `mcp_registry`, `openapi_registry`.
- a2a_clients: remote agent clients (agent card URLs).
- runtime: ADK RunConfig tuning (streaming, limits).
- global_instruction: optional instruction applied to the root agent at runtime.

Environment interpolation

- `${VAR}` and `$VAR` sequences are substituted from the process env.

Service URIs

- Sessions: `sqlite:///...`, `postgresql://...`, `mysql://...`, `redis://host:port/db`, `mongodb://...`, `yaml://path`, `memory:`
- Artifacts: `file://path`, `s3://bucket/prefix`, `mongodb://...`, `sqlite:///...`
- Memory: `redis://...`, `mongodb://...`, `sqlite:///...`, `yaml://...`, `memory:`

Programmatic parsing

```
from agent_compose_kit.config.models import parse_service_uri

cfg = parse_service_uri("session", "sqlite:///./sessions.db")
```
