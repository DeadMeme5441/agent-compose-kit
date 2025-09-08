from __future__ import annotations

from typing import Any, Dict, List

from ..config.models import (
    Agent,
    CustomAgentCfg,
    LlmAgentCfg,
    LoopAgentCfg,
    ParallelAgentCfg,
    SequentialAgentCfg,
)


def _parse_agent(spec: Dict[str, Any]) -> Agent:
    """Validate and coerce a mapping into an Agent variant.

    Args:
        spec: Agent specification mapping.

    Returns:
        Parsed ``Agent`` Pydantic model instance.

    Raises:
        ValueError: When ``type`` is missing or unsupported.
    """
    t = str(spec.get("type"))
    if t == "llm":
        return LlmAgentCfg.model_validate(spec)
    if t == "workflow.sequential":
        return SequentialAgentCfg.model_validate(spec)
    if t == "workflow.parallel":
        return ParallelAgentCfg.model_validate(spec)
    if t == "workflow.loop":
        return LoopAgentCfg.model_validate(spec)
    if t == "custom":
        return CustomAgentCfg.model_validate(spec)
    raise ValueError(f"Unknown agent type: {t}")


class DeclarativeAgentRegistry:
    """Pure config-based agent registry (no runtime side-effects).

    Spec format:
    {
      "agents": [ {"id": "planner", <AgentSpec> }, ... ],
      "groups": [ {"id": "core", "include": ["planner", ...]} ]
    }
    """

    def __init__(self, spec: Dict[str, Any] | None) -> None:
        self._agents_by_id: Dict[str, Agent] = {}
        self._groups: Dict[str, List[str]] = {}
        spec = spec or {}
        for a in spec.get("agents") or []:
            aid = a.get("id")
            if not aid:
                continue
            # copy minus id
            aspec = {k: v for k, v in a.items() if k != "id"}
            self._agents_by_id[str(aid)] = _parse_agent(aspec)
        for g in spec.get("groups") or []:
            gid = g.get("id")
            if not gid:
                continue
            include = g.get("include") or []
            self._groups[str(gid)] = [str(x) for x in include]

    def get(self, agent_id: str) -> Agent:
        """Return the parsed Agent entry for an id.

        Args:
            agent_id: Identifier declared under ``agents``.

        Returns:
            Pydantic ``Agent`` instance.

        Raises:
            KeyError: If the id is not present in the registry.
        """
        if agent_id not in self._agents_by_id:
            raise KeyError(f"Agent id not found: {agent_id}")
        return self._agents_by_id[agent_id]

    def get_group(self, group_id: str) -> List[Agent]:
        """Return agents for a group id.

        Args:
            group_id: Group identifier declared under ``groups``.

        Returns:
            List of Pydantic ``Agent`` instances in declared order.

        Raises:
            KeyError: If the group id is not found.
        """
        ids = self._groups.get(group_id)
        if ids is None:
            raise KeyError(f"Agent group id not found: {group_id}")
        return [self.get(aid) for aid in ids]

    def list_ids(self) -> List[str]:
        """Return all agent ids in sorted order."""
        return sorted(self._agents_by_id.keys())

    def list_groups(self) -> List[str]:
        """Return all group ids in sorted order."""
        return sorted(self._groups.keys())
