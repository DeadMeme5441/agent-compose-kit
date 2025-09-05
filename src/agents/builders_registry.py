from __future__ import annotations

from pathlib import Path
from typing import Mapping, Dict

from ..config.models import AppConfig
from .registry import AgentRegistry


def build_agent_registry_from_config(
    cfg: AppConfig,
    *,
    base_dir: str | Path = ".",
    provider_defaults: Mapping[str, Dict[str, object]] | None = None,
    tool_registry=None,
) -> AgentRegistry:
    base = Path(base_dir).resolve()
    specs = cfg.agents_registry or {}
    return AgentRegistry(specs, base_dir=base, provider_defaults=provider_defaults, tool_registry=tool_registry)

