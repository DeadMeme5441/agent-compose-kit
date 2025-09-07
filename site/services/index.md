# Services

The factories in `agent_compose_kit.services.factory` build ADK services. They’re conservative: if required params are missing, they return in-memory implementations.

SessionService

```
from agent_compose_kit.services.factory import build_session_service

svc = build_session_service("sqlite:///./sessions.db")  # or dict config
```

ArtifactService

```
from agent_compose_kit.services.factory import build_artifact_service

art = build_artifact_service("file://./artifacts")
```

MemoryService (optional)

```
from agent_compose_kit.services.factory import build_memory_service

mem = build_memory_service("memory:")  # or redis/mongo/sql/yaml
```

Backends

- In-memory (default fallbacks)
- Redis, MongoDB, SQL (via google-adk-extras)
- YAML file stores (sessions/memory)
- Artifacts: local folder, S3, MongoDB, SQL

Notes

- Missing or incomplete params → in-memory fallback.
- No GCS support in this library (keep scope aligned with extras).
