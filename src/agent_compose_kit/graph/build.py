"""Build an ADK-aware system graph (nodes, edges, hints) from the declarative config.

Nodes
- agent.llm | agent.workflow.sequential | agent.workflow.parallel | agent.workflow.loop | agent.custom
- tool.function | tool.mcp | tool.openapi | tool.agent
- registry:agent:* when referenced via RegistryRef

Edges
- agent.llm -> tool.* (attached tools)
- agent.llm -> agent.* (sub_agents)
- workflow.sequential: ordered edges sub[i] -> sub[i+1]
- workflow.parallel: fan-out from parallel agent -> sub_agents; optional edge parallel -> merge
- workflow.loop: loop agent -> body

Hints
- Missing LLM model and no defaults.model_alias
- Unknown sub_agent (string) that doesn't refer to a local agent
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

from ..config.models import (
    Agent,
    AppConfig,
    LlmAgentCfg,
    LoopAgentCfg,
    ParallelAgentCfg,
    RegistryRef,
    SequentialAgentCfg,
    AgentTool,
    FunctionTool,
    McpTool,
    OpenApiTool,
    OpenApiToolset,
    McpToolset,
    ApiHubToolset,
    BuiltInTool,
)


def _agent_node_id(a: Union[LlmAgentCfg, SequentialAgentCfg, ParallelAgentCfg, LoopAgentCfg]) -> str:
    """Return canonical node id for an agent.

    Args:
        a: Agent configuration instance.

    Returns:
        Canonical graph node id for the agent (e.g., ``agent:planner``).
    """
    return f"agent:{a.name}"


def _registry_agent_id(ref: RegistryRef) -> str:
    """Return graph node id for a referenced registry agent.

    Args:
        ref: Registry reference of kind ``agent``.

    Returns:
        Registry node id (e.g., ``registry:agent:helper@1.0.0``).
    """
    v = ref.version or "latest"
    return f"registry:agent:{ref.key}@{v}"


def _tool_node_id(owner_id: str, idx: int, kind: str) -> str:
    """Return canonical node id for a tool attached to an agent.

    Args:
        owner_id: Graph node id of the owning agent.
        idx: 0-based index of the tool on the agent.
        kind: Short kind label (e.g., ``function``, ``openapi``).

    Returns:
        Canonical tool node id (e.g., ``agent:planner:tool:0:function``).
    """
    return f"{owner_id}:tool:{idx}:{kind}"


def build_system_graph(cfg: AppConfig) -> Dict[str, Any]:
    """Build a deterministic ADK-aware graph from a config.

    Args:
        cfg: Parsed ``AppConfig`` instance.

    Returns:
        A dictionary with keys:
        - ``nodes``: list of node dicts {id,label,type,meta?}
        - ``edges``: list of edge dicts {source,target,type}
        - ``hints``: list of advisory strings
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    hints: List[str] = []

    # Map local agents by name and collect nodes
    local: Dict[str, Tuple[str, Agent]] = {}
    for ag in cfg.agents:
        if isinstance(ag, LlmAgentCfg):
            nid = _agent_node_id(ag)
            meta = {}
            if getattr(ag, "output_key", None):
                meta["output_key"] = ag.output_key
            # planner meta
            p = getattr(ag, "planner", None)
            if p is not None:
                try:
                    meta["planner"] = getattr(p, 'type', None)
                except Exception:
                    pass
            nodes.append({"id": nid, "label": ag.name, "type": "agent.llm", "meta": meta})
            local[ag.name] = (nid, ag)
        elif isinstance(ag, SequentialAgentCfg):
            nid = _agent_node_id(ag)
            nodes.append({"id": nid, "label": ag.name, "type": "agent.workflow.sequential"})
            local[ag.name] = (nid, ag)
        elif isinstance(ag, ParallelAgentCfg):
            nid = _agent_node_id(ag)
            nodes.append({"id": nid, "label": ag.name, "type": "agent.workflow.parallel"})
            local[ag.name] = (nid, ag)
        elif isinstance(ag, LoopAgentCfg):
            nid = _agent_node_id(ag)
            nodes.append({"id": nid, "label": ag.name, "type": "agent.workflow.loop"})
            local[ag.name] = (nid, ag)
        else:
            # Custom
            name = getattr(ag, "name", "custom")
            nid = f"agent:{name}"
            nodes.append({"id": nid, "label": name, "type": "agent.custom"})
            local[name] = (nid, ag)

    # Edges for LLM agents
    for name, (nid, ag) in local.items():
        if not isinstance(ag, LlmAgentCfg):
            continue
        # Hints: missing model and no defaults
        if ag.model is None and not (cfg.defaults and cfg.defaults.model_alias):
            hints.append(f"agent '{ag.name}' has no model and no defaults.model_alias")
        # Tools
        for i, t in enumerate(ag.tools):
            kind = None
            if isinstance(t, FunctionTool):
                kind = "tool.function"
            elif isinstance(t, McpTool):
                kind = "tool.mcp"
            elif isinstance(t, OpenApiTool):
                kind = "tool.openapi"
            elif isinstance(t, AgentTool):
                kind = "tool.agent"
            elif isinstance(t, OpenApiToolset):
                kind = "tool.openapi_toolset"
            elif isinstance(t, McpToolset):
                kind = "tool.mcp_toolset"
            elif isinstance(t, ApiHubToolset):
                kind = "tool.apihub_toolset"
            elif isinstance(t, BuiltInTool):
                kind = f"tool.builtin:{t.name}"
            if kind is None:
                continue
            tid = _tool_node_id(nid, i, kind.split(".")[-1])
            nodes.append({"id": tid, "label": kind, "type": kind})
            edges.append({"source": nid, "target": tid, "type": "tool"})
        # Hint when output_schema is set and tools present (runtime disables tools per ADK)
        if getattr(ag, "output_schema", None) and ag.tools:
            hints.append(f"agent '{ag.name}' has output_schema set; tools will be disabled at runtime")
        # Planner-specific hints
        if getattr(ag, 'planner', None) is not None:
            p = ag.planner
            try:
                ptype = getattr(p, 'type', None)
                if ptype == 'built_in':
                    # If generate_content_config contains thinking_config, suggest moving to planner
                    gcc = getattr(ag, 'generate_content_config', {}) or {}
                    if isinstance(gcc, dict) and 'thinking_config' in gcc:
                        hints.append(f"agent '{ag.name}' has thinking_config in generate_content_config; move it to planner.built_in.thinking_config")
                elif ptype == 'plan_react':
                    if getattr(ag, 'output_schema', None):
                        hints.append(f"agent '{ag.name}' uses plan_react planner but has output_schema; this disables tools expected by Plan-Re-Act")
            except Exception:
                pass
        # Sub-agents
        for ref in ag.sub_agents:
            if isinstance(ref, str):
                tgt = local.get(ref)
                if tgt:
                    edges.append({"source": nid, "target": tgt[0], "type": "sub"})
                else:
                    hints.append(f"agent '{ag.name}' references unknown sub_agent '{ref}'")
            elif isinstance(ref, RegistryRef):
                rid = _registry_agent_id(ref)
                nodes.append({"id": rid, "label": ref.key or "agent", "type": "agent.registry"})
                edges.append({"source": nid, "target": rid, "type": "sub"})

    # Workflow: sequential / parallel / loop
    for name, (nid, ag) in local.items():
        if isinstance(ag, SequentialAgentCfg):
            # edges between consecutive sub agents
            seq: List[str] = []
            for s in ag.sub_agents:
                if isinstance(s, str) and s in local:
                    seq.append(local[s][0])
                elif isinstance(s, RegistryRef):
                    rid = _registry_agent_id(s)
                    nodes.append({"id": rid, "label": s.key or "agent", "type": "agent.registry"})
                    seq.append(rid)
                else:
                    hints.append(f"sequential '{ag.name}' includes unknown sub_agent '{s}'")
            for i in range(len(seq) - 1):
                edges.append({"source": seq[i], "target": seq[i + 1], "type": "flow"})
            # Hints: upstream LLM without output_key
            for i in range(len(seq) - 1):
                src = seq[i]
                # find agent by node id
                for aname, (anid, aobj) in local.items():
                    if anid == src and isinstance(aobj, LlmAgentCfg):
                        if not getattr(aobj, "output_key", None):
                            hints.append(
                                f"sequential '{ag.name}' upstream agent '{aname}' has no output_key; downstream may lack inputs"
                            )
        elif isinstance(ag, ParallelAgentCfg):
            for s in ag.sub_agents:
                if isinstance(s, str) and s in local:
                    edges.append({"source": nid, "target": local[s][0], "type": "flow"})
                elif isinstance(s, RegistryRef):
                    rid = _registry_agent_id(s)
                    nodes.append({"id": rid, "label": s.key or "agent", "type": "agent.registry"})
                    edges.append({"source": nid, "target": rid, "type": "flow"})
                else:
                    hints.append(f"parallel '{ag.name}' includes unknown sub_agent '{s}'")
        elif isinstance(ag, LoopAgentCfg):
            # loop -> each sub_agent
            for s in ag.sub_agents:
                if isinstance(s, str) and s in local:
                    edges.append({"source": nid, "target": local[s][0], "type": "flow"})
                elif isinstance(s, RegistryRef):
                    rid = _registry_agent_id(s)
                    nodes.append({"id": rid, "label": s.key or "agent", "type": "agent.registry"})
                    edges.append({"source": nid, "target": rid, "type": "flow"})
                else:
                    hints.append(f"loop '{ag.name}' includes unknown sub_agent '{s}'")
        else:
            # Custom: draw edges to declared sub_agents (visualization-only)
            subs = getattr(ag, "sub_agents", [])
            for s in subs:
                if isinstance(s, str) and s in local:
                    edges.append({"source": nid, "target": local[s][0], "type": "sub"})
                elif isinstance(s, RegistryRef):
                    rid = _registry_agent_id(s)
                    nodes.append({"id": rid, "label": s.key or "agent", "type": "agent.registry"})
                    edges.append({"source": nid, "target": rid, "type": "sub"})
                else:
                    hints.append(f"custom '{getattr(ag, 'name', 'custom')}' includes unknown sub_agent '{s}'")

    return {"nodes": nodes, "edges": edges, "hints": hints}
