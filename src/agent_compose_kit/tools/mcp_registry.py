from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class McpRegistry:
    """Registry for MCP toolsets built from AppConfig.mcp_registry.

    - get(id) builds/caches a McpToolset for a server id
    - get_group(id) returns a list of toolsets for a group
    - close_all() calls close() when available
    """

    def __init__(self, specs: Dict[str, Any] | None, *, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self._specs = specs or {}
        self._servers_by_id: Dict[str, Dict[str, Any]] = {}
        for s in (self._specs.get("servers") or []):
            sid = s.get("id")
            if sid:
                self._servers_by_id[str(sid)] = s
        self._groups: Dict[str, List[str]] = {}
        for g in (self._specs.get("groups") or []):
            gid = g.get("id")
            include = g.get("include") or []
            if gid and isinstance(include, list):
                self._groups[str(gid)] = [str(x) for x in include]
        self._toolsets: Dict[str, object] = {}

    def _build_toolset(self, server_spec: Dict[str, Any]) -> object:
        try:
            from google.adk.tools.mcp_tool.mcp_toolset import (
                McpToolset,
                SseConnectionParams,
                StdioConnectionParams,
                StreamableHTTPConnectionParams,
            )  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError("MCP support not available. Install google-adk with MCP") from e

        mode = str(server_spec.get("mode", "sse")).lower()
        tool_filter = server_spec.get("tool_filter") or []
        auth_scheme = server_spec.get("auth_scheme")
        auth_credential = server_spec.get("auth_credential")
        if mode == "stdio":
            try:
                from mcp import StdioServerParameters  # type: ignore
            except Exception as e:  # pragma: no cover - optional dep
                raise ImportError("mcp package not installed for stdio mode") from e
            command = server_spec.get("command")
            args = server_spec.get("args", [])
            if not command:
                raise ValueError("mcp stdio requires 'command'")
            if not isinstance(args, list):
                raise ValueError("mcp stdio 'args' must be a list")
            server_params = StdioServerParameters(command=str(command), args=[str(a) for a in args])
            conn = StdioConnectionParams(
                server_params=server_params,
                timeout=float(server_spec.get("timeout", 5.0)),
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        if mode == "sse":
            url = server_spec.get("url")
            if not url:
                raise ValueError("mcp sse requires 'url'")
            headers = server_spec.get("headers") or {}
            conn = SseConnectionParams(
                url=str(url),
                headers={str(k): v for k, v in dict(headers).items()},
                timeout=float(server_spec.get("timeout") or 5.0),
                sse_read_timeout=float(server_spec.get("sse_read_timeout") or 300.0),
                auth_scheme=auth_scheme,
                auth_credential=auth_credential,
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        if mode in ("http", "streamable_http", "streamable-http"):
            url = server_spec.get("url")
            if not url:
                raise ValueError("mcp http requires 'url'")
            headers = server_spec.get("headers") or {}
            conn = StreamableHTTPConnectionParams(
                url=str(url),
                headers={str(k): v for k, v in dict(headers).items()},
                timeout=float(server_spec.get("timeout") or 5.0),
                sse_read_timeout=float(server_spec.get("sse_read_timeout") or 300.0),
                terminate_on_close=bool(server_spec.get("terminate_on_close", True)),
                auth_scheme=auth_scheme,
                auth_credential=auth_credential,
            )
            return McpToolset(connection_params=conn, tool_filter=tool_filter)
        raise ValueError(f"Unsupported mcp mode: {mode}")

    def get(self, server_id: str) -> object:
        if server_id in self._toolsets:
            return self._toolsets[server_id]
        spec = self._servers_by_id.get(server_id)
        if not spec:
            raise KeyError(f"MCP server id not found: {server_id}")
        toolset = self._build_toolset(spec)
        self._toolsets[server_id] = toolset
        return toolset

    def get_group(self, group_id: str) -> List[object]:
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"MCP group id not found: {group_id}")
        out: List[object] = []
        seen: set[str] = set()
        for sid in ids:
            if sid in seen:
                continue
            out.append(self.get(sid))
            seen.add(sid)
        return out

    def close_all(self) -> None:
        for obj in list(self._toolsets.values()):
            close = getattr(obj, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
