from __future__ import annotations

from pathlib import Path

from ..config.models import AppConfig
from .mcp_registry import McpRegistry
from .openapi_registry import OpenAPIRegistry
from .registry import ToolRegistry


def build_tool_registry_from_config(cfg: AppConfig, *, base_dir: str | Path = ".") -> ToolRegistry:
    """Construct a ToolRegistry from AppConfig's `tools_registry` specs."""
    base = Path(base_dir).resolve()
    specs = cfg.tools_registry or {}
    return ToolRegistry(specs, base_dir=base)


def build_mcp_registry_from_config(cfg: AppConfig, *, base_dir: str | Path = ".") -> McpRegistry | None:
    """Construct an McpRegistry from AppConfig's `mcp_registry` block when present."""
    base = Path(base_dir).resolve()
    specs = cfg.mcp_registry.model_dump() if getattr(cfg, "mcp_registry", None) else None
    if specs is None:
        return None
    return McpRegistry(specs, base_dir=base)


def build_openapi_registry_from_config(
    cfg: AppConfig, *, base_dir: str | Path = "."
) -> OpenAPIRegistry | None:
    """Construct an OpenAPIRegistry from AppConfig's `openapi_registry` block when present."""
    base = Path(base_dir).resolve()
    specs = cfg.openapi_registry.model_dump() if getattr(cfg, "openapi_registry", None) else None
    if specs is None:
        return None
    return OpenAPIRegistry(specs, base_dir=base)
