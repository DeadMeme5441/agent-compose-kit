from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class OpenAPIRegistry:
    """Registry for OpenAPI toolsets from AppConfig.openapi_registry.

    Supports inline/path/url spec entries. URL fetch requires host present in
    fetch_allowlist. Builds OpenAPIToolset instances and caches by id.
    
    Args:
        specs: Parsed ``cfg.openapi_registry`` (dict) or None.
        base_dir: Base directory for resolving relative ``spec.path`` entries.
    """

    def __init__(self, specs: Dict[str, Any] | None, *, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self._specs = specs or {}
        self._apis_by_id: Dict[str, Dict[str, Any]] = {}
        for a in (self._specs.get("apis") or []):
            aid = a.get("id")
            if aid:
                self._apis_by_id[str(aid)] = a
        self._groups: Dict[str, List[str]] = {}
        for g in (self._specs.get("groups") or []):
            gid = g.get("id")
            include = g.get("include") or []
            if gid and isinstance(include, list):
                self._groups[str(gid)] = [str(x) for x in include]
        self._allow: List[str] = list(self._specs.get("fetch_allowlist") or [])
        self._toolsets: Dict[str, object] = {}

    def _allow_host(self, host: str) -> bool:
        """Return True if hostname matches the allowlist.

        Supports exact matches and wildcard patterns like ``*.example.com``.

        Args:
            host: Hostname extracted from a URL.

        Returns:
            True when allowed; otherwise False.
        """
        host = (host or "").lower()
        for pat in self._allow:
            p = pat.lower().strip()
            if p == host:
                return True
            if p.startswith("*.") and host.endswith(p[1:]):
                return True
        return False

    def _build_toolset(self, api_spec: Dict[str, Any]) -> object:
        """Construct an ADK ``OpenAPIToolset`` from one API spec.

        Args:
            api_spec: Mapping describing an API entry (id, spec, headers, etc.).

        Returns:
            Constructed ``OpenAPIToolset``.

        Raises:
            ImportError: When OpenAPI support is not available in ADK.
            ValueError: When required fields are missing/invalid, or URL host
                is not allowlisted.
        """
        try:
            from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import (
                OpenAPIToolset,
            )  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise ImportError("OpenAPI support not available in google-adk") from e

        spec = api_spec.get("spec") or {}
        if not isinstance(spec, dict):
            raise ValueError("openapi api.spec must be a mapping")

        spec_type = (api_spec.get("spec_type") or "json").lower()
        spec_str: str | None = None
        if spec.get("inline"):
            spec_str = str(spec["inline"])
        elif spec.get("path"):
            p = self.base_dir / str(spec["path"])
            spec_str = p.read_text(encoding="utf-8")
            # infer when not explicitly provided
            if not api_spec.get("spec_type"):
                spec_type = "yaml" if p.suffix.lower() in (".yaml", ".yml") else "json"
        elif spec.get("url"):
            # Only allow if host allowlisted
            from urllib.parse import urlparse

            url = str(spec["url"])  # type: ignore[index]
            host = urlparse(url).netloc
            if not self._allow_host(host):
                raise ValueError(f"openapi url host '{host}' not allowlisted")
            # Fetch content
            import requests  # type: ignore

            resp = requests.get(url, timeout=float(api_spec.get("timeout") or 10.0))
            resp.raise_for_status()
            spec_str = resp.text
            if not api_spec.get("spec_type"):
                # naive sniffing: yaml if it starts with openapi: else json
                st = spec_str.lstrip()
                spec_type = "yaml" if st.startswith("openapi:") else "json"
        else:
            raise ValueError("openapi api.spec requires one of: inline, path, url")

        tool_filter = api_spec.get("tool_filter") or []
        # For now, forward only tool_filter. Additional filters/auth may be wired later.
        return OpenAPIToolset(spec_str=spec_str, spec_str_type=spec_type, tool_filter=tool_filter)

    def get(self, api_id: str) -> object:
        """Return a cached or newly built OpenAPI toolset by id.

        Args:
            api_id: API identifier.

        Returns:
            ADK ``OpenAPIToolset`` instance.

        Raises:
            KeyError: When id is not present in registry.
        """
        if api_id in self._toolsets:
            return self._toolsets[api_id]
        spec = self._apis_by_id.get(api_id)
        if not spec:
            raise KeyError(f"OpenAPI api id not found: {api_id}")
        toolset = self._build_toolset(spec)
        self._toolsets[api_id] = toolset
        return toolset

    def get_group(self, group_id: str) -> List[object]:
        """Return toolsets for a registry API group.

        Args:
            group_id: Group identifier.

        Returns:
            List of ``OpenAPIToolset`` instances.

        Raises:
            KeyError: When group id is missing.
        """
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"OpenAPI group id not found: {group_id}")
        out: List[object] = []
        seen: set[str] = set()
        for aid in ids:
            if aid in seen:
                continue
            out.append(self.get(aid))
            seen.add(aid)
        return out

    def close_all(self) -> None:
        """Close all toolsets that expose ``close()``."""
        for obj in list(self._toolsets.values()):
            close = getattr(obj, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

    # Discovery helpers
    def list_ids(self) -> List[str]:
        """Return all OpenAPI ids in the registry."""
        return sorted(self._apis_by_id.keys())

    def list_groups(self) -> List[str]:
        """Return all OpenAPI group ids."""
        return sorted(self._groups.keys())
