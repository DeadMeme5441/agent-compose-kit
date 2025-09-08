from __future__ import annotations

from typing import Any, Dict, List

from ..config.models import Tool, McpTool, OpenApiTool, FunctionTool, AgentTool


def _parse_tool(spec: Dict[str, Any]) -> Tool:
    """Validate and coerce a mapping into a Tool variant.

    Args:
        spec: Tool specification mapping.

    Returns:
        Parsed ``Tool`` Pydantic model instance.

    Raises:
        ValueError: When ``kind`` is missing or unsupported.
    """
    k = str(spec.get("kind"))
    if k == "mcp":
        return McpTool.model_validate(spec)
    if k == "openapi":
        return OpenApiTool.model_validate(spec)
    if k == "function":
        return FunctionTool.model_validate(spec)
    if k == "agent":
        return AgentTool.model_validate(spec)
    raise ValueError(f"Unknown tool kind: {k}")


class DeclarativeToolRegistry:
    """Pure config-based tool registry (no runtime side-effects).

    Spec format:
    {
      "tools": [ {"id": "read_file", <ToolSpec> }, ... ],
      "groups": [ {"id": "default", "include": ["read_file", ...]} ]
    }
    """

    def __init__(self, spec: Dict[str, Any] | None) -> None:
        self._tools_by_id: Dict[str, Tool] = {}
        self._groups: Dict[str, List[str]] = {}
        spec = spec or {}
        for t in spec.get("tools") or []:
            tid = t.get("id")
            if not tid:
                continue
            tspec = {k: v for k, v in t.items() if k != "id"}
            self._tools_by_id[str(tid)] = _parse_tool(tspec)
        for g in spec.get("groups") or []:
            gid = g.get("id")
            if not gid:
                continue
            include = g.get("include") or []
            self._groups[str(gid)] = [str(x) for x in include]

    def get(self, tool_id: str) -> Tool:
        """Return the parsed Tool entry for an id.

        Args:
            tool_id: Identifier declared under ``tools``.

        Returns:
            Pydantic ``Tool`` instance.

        Raises:
            KeyError: If the id is not present in the registry.
        """
        if tool_id not in self._tools_by_id:
            raise KeyError(f"Tool id not found: {tool_id}")
        return self._tools_by_id[tool_id]

    def get_group(self, group_id: str) -> List[Tool]:
        """Return tools for a group id.

        Args:
            group_id: Group identifier declared under ``groups``.

        Returns:
            List of Pydantic ``Tool`` instances in declared order.

        Raises:
            KeyError: If the group id is not found.
        """
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"Tool group id not found: {group_id}")
        return [self.get(tid) for tid in ids]

    def list_ids(self) -> List[str]:
        """Return all tool ids in sorted order."""
        return sorted(self._tools_by_id.keys())

    def list_groups(self) -> List[str]:
        """Return all group ids in sorted order."""
        return sorted(self._groups.keys())
