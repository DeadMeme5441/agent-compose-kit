"""Agent Compose Kit public API package."""

from .agents.builders_registry import build_agent_registry_from_config
from .agents.registry import AgentRegistry
from .api.public import (
    CancelRegistry,
    SessionManager,
    SystemManager,
    event_to_minimal_json,
    run_text,
)
from .graph.build import build_system_graph
from .paths import (
    get_outputs_root,
    get_sessions_uri,
    get_systems_root,
    resolve_outputs_dir,
    resolve_system_dir,
)
from .tools.builders import (
    build_mcp_registry_from_config,
    build_openapi_registry_from_config,
    build_tool_registry_from_config,
)
from .tools.mcp_registry import McpRegistry
from .tools.openapi_registry import OpenAPIRegistry
from .tools.registry import ToolRegistry

__all__ = [
    # Public API
    "SystemManager",
    "SessionManager",
    "CancelRegistry",
    "run_text",
    "event_to_minimal_json",
    # Graph
    "build_system_graph",
    # Paths
    "get_systems_root",
    "get_outputs_root",
    "get_sessions_uri",
    "resolve_system_dir",
    "resolve_outputs_dir",
    # Registries & builders
    "ToolRegistry",
    "McpRegistry",
    "OpenAPIRegistry",
    "build_tool_registry_from_config",
    "build_mcp_registry_from_config",
    "build_openapi_registry_from_config",
    "AgentRegistry",
    "build_agent_registry_from_config",
]
