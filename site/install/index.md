# Installation

Agent Compose Kit is published on PyPI. It depends on Google ADK and google-adk-extras. We recommend using `uv` for reliable, fast environments.

Using uv

```
uv add agent-compose-kit
```

Using pip

```
pip install agent-compose-kit
```

Optional dependencies

- MCP stdio support: `uv add agent-compose-kit[tools]` (installs `mcp`)
- Docs (for contributors): `uv add --dev agent-compose-kit[docs]`

Python compatibility

- Python 3.12+

Notes

- Certain backends (Redis, Mongo, SQL, S3) require google-adk-extras at runtime. It is listed in this package’s dependencies and will be installed automatically, but you must still provide valid connection details at runtime.
