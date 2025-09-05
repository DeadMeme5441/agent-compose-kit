from __future__ import annotations

from pathlib import Path

from ..config.models import AppConfig
from .registry import ToolRegistry


def build_tool_registry_from_config(cfg: AppConfig, *, base_dir: str | Path = ".") -> ToolRegistry:
    """Construct a ToolRegistry from AppConfig's `tools_registry` specs."""
    base = Path(base_dir).resolve()
    specs = cfg.tools_registry or {}
    return ToolRegistry(specs, base_dir=base)
