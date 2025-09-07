# Graph

Produce a simple system graph for UIs — no HTTP server required.

```
from pathlib import Path
from agent_compose_kit.config.models import load_config_file
from agent_compose_kit.graph.build import build_system_graph

cfg = load_config_file(Path("configs/app.yaml"))
g = build_system_graph(cfg)
print(g["nodes"], g["edges"])  # nodes/edges dicts
```

Nodes

- Inline agents and groups
- Registry agents and groups (`registry:*` node ids)

Edges

- Sub-agent wiring, group membership, workflow order
