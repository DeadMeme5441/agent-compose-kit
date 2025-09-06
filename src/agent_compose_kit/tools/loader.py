from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def _import_dotted(ref: str):
    """Import and return an attribute from a dotted path 'module:attr' or raise.

    This function strictly expects 'module:attr' and raises ValueError when the
    format is invalid. Missing attributes raise ImportError with context.
    """
    if ":" not in ref:
        raise ValueError(f"Invalid dotted reference '{ref}', expected 'module:attr'")
    mod_name, attr = ref.split(":", 1)
    mod = __import__(mod_name, fromlist=[attr])
    try:
        return getattr(mod, attr)
    except AttributeError as e:
        raise ImportError(f"Attribute '{attr}' not found in module '{mod_name}'") from e


def _ensure_list_filter(v: Any) -> Optional[List[str]]:
    """Validate a tool filter value is a list[str] or None."""
    if v is None:
        return None
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return v  # type: ignore[return-value]
    raise ValueError("tool_filter must be a list of strings")


def load_tool_entry(
    entry: Any,
    *,
    base_dir: Path,
    toolsets_map: Optional[Dict[str, object]] = None,
    mcp_registry: Any | None = None,
    openapi_registry: Any | None = None,
) -> object:
    """Load a single tool or toolset from a YAML entry.

    Supports:
    - ``{type:function, ref:'module:callable', name?: str}``
    - ``{type:mcp, mode:stdio|sse|streamable_http, ...}``
    - ``{type:openapi, spec:{path|inline}, spec_type:json|yaml, tool_filter?:[]}``
    - ``{use: <toolset_name>}`` referencing a shared toolset from ``toolsets``
    - ``{use: 'mcp:<id>'}``, ``{use: 'mcp_group:<id>'}`` when an ``McpRegistry`` is provided
    - ``{use: 'openapi:<id>'}``, ``{use: 'openapi_group:<id>'}`` when an ``OpenAPIRegistry`` is provided

    Args:
        entry: Mapping or scalar describing a tool/toolset.
        base_dir: Base directory for resolving local paths.
        toolsets_map: Optional shared toolsets registry (name→object).
        mcp_registry: Optional MCP registry to resolve ``use: mcp:*`` references.
        openapi_registry: Optional OpenAPI registry to resolve ``use: openapi:*`` references.

    Returns:
        A concrete tool/toolset instance or a list of tools (for group refs).

    Raises:
        ValueError: When a required field is missing or a reference is unknown.
        ImportError: When optional MCP/OpenAPI support is not available.
    """
    # Reference to a named toolset
    if isinstance(entry, dict) and "use" in entry:
        if toolsets_map is None:
            # Support registry references when toolsets_map is not used
            name = str(entry["use"]).strip()
            if name.startswith("mcp:"):
                if not mcp_registry:
                    raise ValueError("McpRegistry not provided for 'use: mcp:<id>'")
                return mcp_registry.get(name.split(":", 1)[1])
            if name.startswith("mcp_group:"):
                if not mcp_registry:
                    raise ValueError("McpRegistry not provided for 'use: mcp_group:<id>'")
                return mcp_registry.get_group(name.split(":", 1)[1])
            if name.startswith("openapi:"):
                if not openapi_registry:
                    raise ValueError("OpenAPIRegistry not provided for 'use: openapi:<id>'")
                return openapi_registry.get(name.split(":", 1)[1])
            if name.startswith("openapi_group:"):
                if not openapi_registry:
                    raise ValueError("OpenAPIRegistry not provided for 'use: openapi_group:<id>'")
                return openapi_registry.get_group(name.split(":", 1)[1])
            raise ValueError("No toolsets map provided but 'use' was specified")
        name = str(entry["use"]).strip()
        if name in toolsets_map:
            return toolsets_map[name]
        # Allow passing through registry references even when map present
        if name.startswith("mcp:"):
            if not mcp_registry:
                raise ValueError("McpRegistry not provided for 'use: mcp:<id>'")
            return mcp_registry.get(name.split(":", 1)[1])
        if name.startswith("mcp_group:"):
            if not mcp_registry:
                raise ValueError("McpRegistry not provided for 'use: mcp_group:<id>'")
            return mcp_registry.get_group(name.split(":", 1)[1])
        if name.startswith("openapi:"):
            if not openapi_registry:
                raise ValueError("OpenAPIRegistry not provided for 'use: openapi:<id>'")
            return openapi_registry.get(name.split(":", 1)[1])
        if name.startswith("openapi_group:"):
            if not openapi_registry:
                raise ValueError("OpenAPIRegistry not provided for 'use: openapi_group:<id>'")
            return openapi_registry.get_group(name.split(":", 1)[1])
        raise ValueError(f"Unknown toolset reference: {name}")

    if not isinstance(entry, dict):
        return entry
    t = entry.get("type")
    if t == "function":
        ref = entry.get("ref")
        if not ref:
            raise ValueError("function tool requires 'ref'")
        func = _import_dotted(str(ref))
        from google.adk.tools import FunctionTool  # type: ignore

        tool = FunctionTool(func=func)
        name = entry.get("name")
        if name:
            try:
                setattr(tool, "name", str(name))
            except Exception:
                pass
        return tool

    if t == "mcp":
        try:
            from google.adk.tools.mcp_tool.mcp_toolset import (
                McpToolset,
                SseConnectionParams,
                StdioConnectionParams,
                StreamableHTTPConnectionParams,
            )  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError("MCP support not available. Install google-adk with MCP") from e

        mode = str(entry.get("mode", "stdio")).lower()
        tool_filter = _ensure_list_filter(entry.get("tool_filter"))
        if mode == "stdio":
            try:
                from mcp import StdioServerParameters  # type: ignore
            except Exception as e:  # pragma: no cover - optional dep
                raise ImportError("mcp package not installed for stdio mode") from e
            command = entry.get("command")
            args = entry.get("args", [])
            if not command:
                raise ValueError("mcp stdio requires 'command'")
            if not isinstance(args, list):
                raise ValueError("mcp stdio 'args' must be a list of strings")
            server_params = StdioServerParameters(
                command=str(command),
                args=[str(a) for a in args],
            )
            conn = StdioConnectionParams(
                server_params=server_params,
                timeout=float(entry.get("timeout", 5.0)),
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        if mode == "sse":
            url = entry.get("url")
            if not url:
                raise ValueError("mcp sse requires 'url'")
            headers = entry.get("headers") or {}
            conn = SseConnectionParams(
                url=str(url),
                headers={str(k): v for k, v in dict(headers).items()},
                timeout=float(entry.get("timeout", 5.0)),
                sse_read_timeout=float(entry.get("sse_read_timeout", 300.0)),
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        if mode in ("http", "streamable_http", "streamable-http"):
            url = entry.get("url")
            if not url:
                raise ValueError("mcp streamable_http requires 'url'")
            headers = entry.get("headers") or {}
            conn = StreamableHTTPConnectionParams(
                url=str(url),
                headers={str(k): v for k, v in dict(headers).items()},
                timeout=float(entry.get("timeout", 5.0)),
                sse_read_timeout=float(entry.get("sse_read_timeout", 300.0)),
                terminate_on_close=bool(entry.get("terminate_on_close", True)),
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        raise ValueError(f"Unsupported mcp mode: {mode}")

    if t == "openapi":
        try:
            from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import (
                OpenAPIToolset,
            )  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError("OpenAPI support not available in google-adk") from e
        spec = entry.get("spec") or {}
        spec_str: Optional[str] = None
        spec_type = str(entry.get("spec_type", "json")).lower()
        if not isinstance(spec, dict):
            raise ValueError("openapi 'spec' must be a mapping")
        if spec.get("inline"):
            spec_str = str(spec["inline"])
        elif spec.get("path"):
            p = Path(base_dir) / str(spec["path"])
            spec_str = p.read_text(encoding="utf-8")
            # If caller did not explicitly provide spec_type, infer from extension
            if "spec_type" not in entry:
                spec_type = "yaml" if p.suffix.lower() in (".yaml", ".yml") else "json"
        elif spec.get("url"):
            # avoid network fetch for now; require path or inline for portability
            raise ValueError("openapi 'spec.url' not supported by loader; use path or inline")
        else:
            raise ValueError("openapi 'spec' requires one of: inline, path, or url")
        tool_filter = _ensure_list_filter(entry.get("tool_filter"))
        return OpenAPIToolset(spec_str=spec_str, spec_str_type=spec_type, tool_filter=tool_filter)

    # passthrough for unknown entries (e.g., pre-built BaseTool instances)
    return entry


def load_toolsets_map(cfg_toolsets: Dict[str, Any], *, base_dir: Path) -> Dict[str, object]:
    """Build a name→toolset map from a shared ``toolsets:`` config block.

    Args:
        cfg_toolsets: Mapping of shared toolset specs by name.
        base_dir: Base directory for resolving local files.

    Returns:
        Dictionary mapping toolset name to constructed toolset object.
    """
    out: Dict[str, object] = {}
    for name, spec in cfg_toolsets.items():
        out[name] = load_tool_entry(spec, base_dir=base_dir, toolsets_map=None)
    return out


def load_tool_list(
    entries: List[Any],
    *,
    base_dir: Path,
    toolsets_map: Optional[Dict[str, object]] = None,
    mcp_registry: Any | None = None,
    openapi_registry: Any | None = None,
) -> List[object]:
    """Load tool/toolset entries into concrete tool objects.

    Args:
        entries: List of tool entries from config.
        base_dir: Base directory for resolving local files.
        toolsets_map: Optional shared toolset map.
        mcp_registry: Optional MCP registry for registry references.
        openapi_registry: Optional OpenAPI registry for registry references.

    Returns:
        List of concrete tool objects; group references are flattened.
    """
    tools: List[object] = []
    for e in entries or []:
        obj = load_tool_entry(
            e,
            base_dir=base_dir,
            toolsets_map=toolsets_map,
            mcp_registry=mcp_registry,
            openapi_registry=openapi_registry,
        )
        if isinstance(obj, list):
            tools.extend(obj)
        else:
            tools.append(obj)
    return tools
