# Registries

ToolRegistry (inline)

```
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.tools.builders import build_tool_registry_from_config

cfg = load_config_file(Path("configs/app.yaml"))
tool_reg = build_tool_registry_from_config(cfg, base_dir=".")
print(tool_reg.list_tool_ids())
```

McpRegistry / OpenAPIRegistry

```
from agent_compose_kit.tools.builders import build_mcp_registry_from_config, build_openapi_registry_from_config

mcp_reg = build_mcp_registry_from_config(cfg, base_dir=".")
openapi_reg = build_openapi_registry_from_config(cfg, base_dir=".")
```

AgentRegistry

```
from agent_compose_kit.agents.builders_registry import build_agent_registry_from_config

agent_reg = build_agent_registry_from_config(cfg, base_dir=".", provider_defaults=cfg.model_providers, tool_registry=tool_reg)
root = agent_reg.get_group("core")[0]
```

Groups

- Each registry supports simple groups (id → include list).
- Use `list_*` helpers to enumerate ids/groups before resolution.

Notes

- OpenAPI registry enforces a strict allowlist for fetching specs via URL.
- Call `close_all()` on ToolRegistry or registries that hold long-lived connections when your app shuts down.
