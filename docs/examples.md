---
title: Examples
---

# End-to-end Examples

## Minimal YAML + runner
```yaml
services:
  session_service: "sqlite:///./sessions.db"
  artifact_service: "file://./artifacts"

agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: You are a helpful planner.

workflow:
  type: sequential
  nodes: [planner]
```

```python
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.runtime.supervisor import build_run_config
from agent_compose_kit.api.public import SystemManager, SessionManager, run_text, event_to_minimal_json

cfg = load_config_file(Path("./configs/app.yaml"))
sm = SystemManager(base_dir=Path("."))
root = sm.select_root_agent(cfg)
runner, _ = sm.build_runner(cfg, root_agent=root)

import asyncio

async def main():
    sess = await SessionManager(runner).get_or_create(user_id="u1")
    async for ev in run_text(runner=runner, user_id="u1", session_id=sess.id, text="hello"):
        print(event_to_minimal_json(ev))

asyncio.run(main())
```

## Tools via registries
```yaml
tools_registry:
  tools:
    - {id: util.add, type: function, ref: tests.helpers:sample_tool}
  groups:
    - {id: essentials, include: [util.add]}

agents_registry:
  agents:
    - {id: calc, name: calculator, model: gemini-2.0-flash, tools: [{use: 'registry:util.add'}]}
  groups:
    - {id: core, include: [calc]}
```

```python
from agent_compose_kit.tools.builders import build_tool_registry_from_config
from agent_compose_kit.agents.builders_registry import build_agent_registry_from_config

tool_reg = build_tool_registry_from_config(cfg, base_dir=".")
agent_reg = build_agent_registry_from_config(cfg, base_dir=".", provider_defaults=cfg.model_providers, tool_registry=tool_reg)
root = agent_reg.get_group("core")[0]
```

## A2A remote agent by agent card
```yaml
a2a_clients:
  - id: remote
    agent_card_url: https://host:8000/a2a/hello/.well-known/agent-card.json

agents:
  - name: remote
    kind: a2a_remote
    client: remote
```

