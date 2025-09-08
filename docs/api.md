---
title: Compose API
---

# Compose API

Import the unified facade:

```python
from agent_compose_kit import compose
```

Core:
- `compose.load_config(yaml_or_dict) -> AppConfig`
- `compose.load_config_file(path) -> AppConfig`
- `compose.export_app_config_schema() -> dict`

Graph:
- `compose.build_system_graph(cfg) -> { nodes, edges, hints }`

Quick fixes & utils:
- `compose.get_quick_fixes(raw_cfg, validation_error=None, indexes=None) -> QuickFix[]`
- `compose.fingerprint(raw_cfg) -> sha256`
- `compose.list_dependencies(raw_cfg) -> { registryRefs, modelAliases, agentRefs }`
- `compose.lint(raw_cfg) -> { warnings, infos }`

Aliases:
- `compose.validate_aliases(raw_cfg) -> { unknown_aliases: [] }`

Lock plan:
- `compose.plan_lock(cfg, registry_resolves, alias_resolves) -> LockfilePlan`

