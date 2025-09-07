from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .loader import load_tool_entry


class ToolRegistry:
    """Global tool registry for a Runner lifecycle.

    - Builds and caches tool instances by id on first access.
    - Supports simple groups that expand to lists of tool ids.
    - Caller should call close_all() when done to close toolsets.
    """

    def __init__(self, specs: Dict[str, Any], *, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._specs = specs or {}
        self._tools_by_id: Dict[str, object] = {}
        # normalize groups mapping {group_id: [tool_ids]}
        self._groups: Dict[str, List[str]] = {}
        for g in (self._specs.get("groups") or []):
            gid = g.get("id")
            include = g.get("include") or []
            if gid and isinstance(include, list):
                self._groups[str(gid)] = [str(x) for x in include]

        # index specs by id for lookups
        self._tool_specs_by_id: Dict[str, Dict[str, Any]] = {}
        for t in (self._specs.get("tools") or []):
            tid = t.get("id")
            if tid:
                self._tool_specs_by_id[str(tid)] = t

    def get(self, tool_id: str) -> object:
        """Return a built tool object for an id (cached)."""
        if tool_id in self._tools_by_id:
            return self._tools_by_id[tool_id]
        spec = self._tool_specs_by_id.get(tool_id)
        if not spec:
            raise KeyError(f"Tool id not found in registry: {tool_id}")
        # Build using loader from spec minus metadata keys
        entry = {k: v for k, v in spec.items() if k not in ("id", "tags", "enabled")}
        inst = load_tool_entry(entry, base_dir=self.base_dir)
        self._tools_by_id[tool_id] = inst
        return inst

    def get_group(self, group_id: str) -> List[object]:
        """Return a list of tool instances for a group id, de-duplicated."""
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"Tool group id not found: {group_id}")
        out: List[object] = []
        seen: set[str] = set()
        for tid in ids:
            if tid in seen:
                continue
            out.append(self.get(tid))
            seen.add(tid)
        return out

    def close_all(self) -> None:
        """Close all tool instances that expose a `close()` method."""
        for obj in list(self._tools_by_id.values()):
            close = getattr(obj, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

    # Discovery helpers
    def list_tool_ids(self) -> List[str]:
        """Return all tool ids known to the registry."""
        return sorted(self._tool_specs_by_id.keys())

    def list_tool_groups(self) -> List[str]:
        """Return all tool group ids."""
        return sorted(self._groups.keys())
