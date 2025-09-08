---
title: Examples
---

# Examples

## Minimal LLM agent
```yaml
schema_version: 0.1.0
metadata: { name: demo }
defaults: { model_alias: chat-default }
model_aliases:
  aliases:
    - { id: chat-default, resolver: direct, model: gemini-2.0-flash }
agents:
  - type: llm
    name: planner
    instruction: Plan tasks and call tools
```

## Tools
```yaml
agents:
  - type: llm
    name: api_caller
    instruction: Call API tools
    tools:
      - { kind: openapi_toolset, spec: { ref: { value: registry://openapi/petstore@1 } } }
      - { kind: mcp_toolset, server: { ref: { value: registry://mcp/files@latest } }, tool_filter: [read_file] }
      - { kind: function, function: { import: tests.helpers:sample_tool }, long_running: true }
```

## Validate, graph, and quick-fix (Python)
```python
from pathlib import Path
from agent_compose_kit import compose

cfg = compose.load_config_file(Path("./configs/app.yaml"))
graph = compose.build_system_graph(cfg)
fixes = compose.get_quick_fixes(cfg.model_dump())
lock = compose.plan_lock(cfg, registry_resolves=lambda k, x, r: {}, alias_resolves=lambda a: {})
```

