# Agent Compose Kit

Agent Compose Kit is a Python library that turns YAML into runnable agent systems on top of Google ADK. It’s programmatic-only: no server, no CLI — just focused, composable building blocks for your own CLI, TUI, or Web app.

Highlights

- Config → Objects: validate YAML and construct ADK services, tools, and agents.
- Conservative defaults: in-memory fallbacks when required params are missing.
- Registries-first: enumerate tools/APIs/agents by id/group without building a Runner.
- Graph builder: produce nodes/edges for your UI, no HTTP needed.

What this repo is not

- It does not ship a web server or UI. Use it inside your own app. For server helpers, see google-adk-extras.

Quick links

- Installation: [Install](install/)
- Config schema: [Configuration](config/)
- Services: [Services](services/)
- Tools & Registries: [Tools](tools/), [Registries](registries/)
- Agents & Workflows: [Agents](agents/)
- Graph builder: [Graph](graph/)
- Programmatic API: [Public API](public_api/)
- End-to-end: [Examples](examples/)

Requirements

- Python 3.12+
- google-adk and google-adk-extras (installed automatically via pip when you add this package). Optional extras like MCP/OpenAPI are guarded.
