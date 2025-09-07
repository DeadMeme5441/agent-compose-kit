from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from ..tools.loader import load_tool_entry
from .builder import _resolve_model  # reuse model resolution


class AgentRegistry:
    """Global agent registry for a Runner lifecycle.

    - Builds and caches LlmAgent or RemoteA2aAgent instances by id on first access.
    - Supports groups referencing other agents by id.
    - Uses ToolRegistry for tool resolution when entries use ``use: registry:<tool_id>``.

    Args:
        specs: Parsed ``cfg.agents_registry`` mapping.
        base_dir: Base directory used by the tools loader.
        provider_defaults: Provider defaults for LiteLLM model resolution.
        tool_registry: Optional ToolRegistry instance used to resolve tool references.
        a2a_clients: Optional mapping ``id -> a2a client config`` for remote agents.
    """

    def __init__(
        self,
        specs: Dict[str, Any],
        *,
        base_dir: Path,
        provider_defaults: Mapping[str, Dict[str, Any]] | None = None,
        tool_registry: Any | None = None,
        a2a_clients: Mapping[str, Any] | None = None,
    ) -> None:
        self.base_dir = base_dir
        self.provider_defaults = provider_defaults or {}
        self.tool_registry = tool_registry
        self.a2a_clients = a2a_clients or {}
        self._specs = specs or {}
        self._agents: Dict[str, object] = {}
        # index agent specs by id
        self._agent_specs_by_id: Dict[str, Dict[str, Any]] = {}
        for a in (self._specs.get("agents") or []):
            aid = a.get("id")
            if aid:
                self._agent_specs_by_id[str(aid)] = a
        # groups mapping
        self._groups: Dict[str, List[str]] = {}
        for g in (self._specs.get("groups") or []):
            gid = g.get("id")
            include = g.get("include") or []
            if gid and isinstance(include, list):
                self._groups[str(gid)] = [str(x) for x in include]

    def _resolve_tools(self, tools_entries: List[Any]) -> List[object]:
        """Resolve tool entries including references into concrete tool objects.

        Args:
            tools_entries: List of tool entries from the registry.

        Returns:
            List of concrete tool instances.
        """
        out: List[object] = []
        for e in tools_entries or []:
            if isinstance(e, dict) and isinstance(e.get("use"), str) and e["use"].startswith("registry:"):
                # reference to tools registry
                if not self.tool_registry:
                    raise ValueError("ToolRegistry not provided for registry-based tool reference")
                tool_id = e["use"].split(":", 1)[1]
                out.append(self.tool_registry.get(tool_id))
            else:
                out.append(load_tool_entry(e, base_dir=self.base_dir))
        return out

    def get(self, agent_id: str) -> object:
        """Return a built agent for the given registry id (cached).

        Args:
            agent_id: Agent identifier in the registry.

        Returns:
            Constructed agent instance.

        Raises:
            ValueError: When A2A client references are missing.
        """
        if agent_id in self._agents:
            return self._agents[agent_id]
        spec = self._agent_specs_by_id.get(agent_id)
        if not spec:
            raise KeyError(f"Agent id not found in registry: {agent_id}")
        name = spec.get("name") or agent_id
        instruction = spec.get("instruction") or ""
        if str(spec.get("kind", "llm")) == "a2a_remote":
            cid = spec.get("client")
            if not cid or cid not in self.a2a_clients:
                raise ValueError(f"Unknown a2a client id: {cid}")
            c = self.a2a_clients[cid]
            def _get(obj, key):
                v = getattr(obj, key, None)
                if v is None and isinstance(obj, dict):
                    v = obj.get(key)
                return v
            url = _get(c, "url")
            headers = _get(c, "headers") or {}
            timeout = _get(c, "timeout")
            try:
                try:
                    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent  # type: ignore
                except Exception:
                    from google.adk.agents import RemoteA2aAgent  # type: ignore
            except Exception as e:  # pragma: no cover - optional dep
                raise ImportError("A2A support not available in google-adk") from e
            agent = None
            for kwargs_variant in (
                {"name": name, "base_url": url, "instruction": instruction, "headers": headers, "timeout": timeout},
                {"name": name, "url": url, "instruction": instruction, "headers": headers, "timeout": timeout},
                {"name": name, "base_url": url, "instruction": instruction},
            ):
                try:
                    agent = RemoteA2aAgent(**{k: v for k, v in kwargs_variant.items() if v is not None})
                    break
                except TypeError:
                    continue
            if agent is None:
                raise TypeError("Failed to construct RemoteA2aAgent with supported parameters")
        else:
            from google.adk.agents import LlmAgent  # type: ignore

            model_obj = _resolve_model(spec.get("model"), self.provider_defaults)
            tools = self._resolve_tools(spec.get("tools") or [])
            agent = LlmAgent(name=name, model=model_obj, instruction=instruction, tools=tools)
        # wire sub_agents if specified as registry ids
        sub_ids = spec.get("sub_agents") or []
        subs = [self.get(sid) for sid in sub_ids]
        if subs:
            try:
                setattr(agent, "sub_agents", subs)
            except Exception:
                pass
        self._agents[agent_id] = agent
        return agent

    def get_group(self, group_id: str) -> List[object]:
        """Return a list of agents for a group id, in declared order.

        Args:
            group_id: Group identifier.

        Returns:
            List of constructed agent instances.
        """
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"Agent group id not found: {group_id}")
        return [self.get(aid) for aid in ids]

    # Discovery helpers
    def list_agent_ids(self) -> List[str]:
        """Return all agent ids in the registry."""
        return sorted(self._agent_specs_by_id.keys())

    def list_agent_groups(self) -> List[str]:
        """Return all agent group ids in the registry."""
        return sorted(self._groups.keys())
