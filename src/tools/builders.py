from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import ToolRegistry
from ..config.models import AppConfig


def build_tool_registry_from_config(cfg: AppConfig, *, base_dir: str | Path = ".") -> ToolRegistry:
    base = Path(base_dir).resolve()
    specs = cfg.tools_registry or {}
    return ToolRegistry(specs, base_dir=base)

