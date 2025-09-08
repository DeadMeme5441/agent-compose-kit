"""Agent Compose Kit public API package.

Primary entrypoints live in `agent_compose_kit.compose` for a clean, runtime-free
facade suitable for backend services and tooling.
"""

from . import compose as compose  # re-export module for convenience

__all__: list[str] = ["compose"]
