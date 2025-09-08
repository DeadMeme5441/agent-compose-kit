from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping

from ..config.models import AppConfig
from .registry import AgentRegistry


def build_agent_registry_from_config(
    cfg: AppConfig,
    *,
    base_dir: str | Path = ".",
    provider_defaults: Mapping[str, Dict[str, object]] | None = None,
    tool_registry=None,
) -> AgentRegistry:
    """Construct an AgentRegistry from AppConfig.

    Resolves base_dir, passes provider defaults (e.g., LiteLLM provider
    settings), and connects a ToolRegistry when tool references are used from
    the agents registry (use: registry:<tool_id>).
    """
    base = Path(base_dir).resolve()
    specs = cfg.agents_registry or {}
    # Build a2a clients mapping id→config/dict for registry use
    a2a_map: dict[str, object] = {}
    for c in (cfg.a2a_clients or []):
        try:
            a2a_map[c.id] = c
        except Exception:
            # If already dict-like
            a2a_map[str(getattr(c, "id", ""))] = c
    return AgentRegistry(
        specs,
        base_dir=base,
        provider_defaults=provider_defaults,
        tool_registry=tool_registry,
        a2a_clients=a2a_map,
    )
