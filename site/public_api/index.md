# Public API

Use these helpers to integrate quickly without dealing with low-level plumbing.

SystemManager

```
from pathlib import Path
from agent_compose_kit.api.public import SystemManager

sm = SystemManager(base_dir=Path("./systems/my_system"))
cfg = sm.load("config.yaml")
root = sm.select_root_agent(cfg)
runner, resources = sm.build_runner(cfg, root_agent=root)
```

SessionManager

```
from agent_compose_kit.api.public import SessionManager
sess_mgr = SessionManager(runner)
session = await sess_mgr.get_or_create(user_id="u1")
```

run_text

```
from agent_compose_kit.api.public import run_text, event_to_minimal_json

async for ev in run_text(runner=runner, user_id="u1", session_id=session.id, text="hello"):
    print(event_to_minimal_json(ev))
```

Notes

- `SystemManager.select_root_agent` prefers agents_registry when provided.
- `event_to_minimal_json` serializes events for light UIs; extend as needed for your app.
