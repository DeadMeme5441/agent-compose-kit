"""Build a simple system graph (nodes/edges) from AppConfig.

This mirrors the logic used by the previous server `/graph` endpoint, but as a
pure function suitable for programmatic use.

Nodes include:
- Inline agents: `{id: <name>, label: <name>, type: 'agent'}`
- Inline groups: `{id: 'group:<name>', label: <name>, type: 'group'}`
- Registry agents: `{id: 'registry:agent:<id>', label: <name|id>, type: 'agent_registry'}`
- Registry groups: `{id: 'registry:group:<id>', label: <id>, type: 'agent_group'}`

Edges include:
- Sub-agent wiring: `{source: parent, target: child, type: 'sub'}`
- Group membership: `{source: groupId, target: memberId, type: 'member'}`
- Workflow order: `{source: a, target: b, type: 'flow'}` for sequential; a star for parallel; cycle for loop.

Example:
    >>> from agent_compose_kit.config.models import AppConfig, AgentConfig, WorkflowConfig
    >>> cfg = AppConfig(
    ...     agents=[AgentConfig(name='a', model='gemini-2.0-flash'), AgentConfig(name='b', model='gemini-2.0-flash')],
    ...     workflow=WorkflowConfig(type='sequential', nodes=['a', 'b'])
    ... )
    >>> g = build_system_graph(cfg)
    >>> any(e for e in g['edges'] if e['source']=='a' and e['target']=='b' and e['type']=='flow')
    True
"""

from __future__ import annotations

from typing import Any, Dict

from ..config.models import AppConfig


def build_system_graph(cfg: AppConfig) -> Dict[str, Any]:
    """Return a dict with `nodes` and `edges` representing the system graph.

    Args:
        cfg: Loaded application configuration.

    Returns:
        Mapping with keys `nodes` (list of node dicts) and `edges` (list of edge dicts).
    """
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    # Inline agents
    agent_names = [a.name for a in (cfg.agents or [])]
    for a in (cfg.agents or []):
        nodes.append({"id": a.name, "label": a.name, "type": "agent"})
        for sub in a.sub_agents or []:
            if sub in agent_names:
                edges.append({"source": a.name, "target": sub, "type": "sub"})

    # Inline groups
    for g in (cfg.groups or []):
        gid = f"group:{g.name}"
        nodes.append({"id": gid, "label": g.name, "type": "group"})
        for m in g.members or []:
            if m in agent_names:
                edges.append({"source": gid, "target": m, "type": "member"})

    # Workflow
    if cfg.workflow and cfg.workflow.nodes:
        seq = cfg.workflow.nodes
        if cfg.workflow.type in (None, "sequential", "loop"):
            for i in range(len(seq) - 1):
                s, t = seq[i], seq[i + 1]
                if s in agent_names and t in agent_names:
                    edges.append({"source": s, "target": t, "type": "flow"})
            if cfg.workflow.type == "loop" and len(seq) > 1:
                s, t = seq[-1], seq[0]
                if s in agent_names and t in agent_names:
                    edges.append({"source": s, "target": t, "type": "flow"})
        elif cfg.workflow.type == "parallel":
            pid = "parallel"
            nodes.append({"id": pid, "label": "parallel", "type": "parallel"})
            for n in seq:
                if n in agent_names:
                    edges.append({"source": pid, "target": n, "type": "flow"})

    # Agents registry (ids/groups)
    reg = getattr(cfg, "agents_registry", None) or {}
    reg_agents = list(reg.get("agents") or [])
    reg_groups = list(reg.get("groups") or [])
    reg_agent_ids = {str(a.get("id")) for a in reg_agents if a.get("id")}
    if reg_agents:
        for a in reg_agents:
            aid = a.get("id")
            if not aid:
                continue
            label = a.get("name") or aid
            nodes.append({"id": f"registry:agent:{aid}", "label": str(label), "type": "agent_registry"})
            for sub in a.get("sub_agents") or []:
                sid = str(sub)
                if sid in reg_agent_ids or any(sid == (x.get("id") and str(x.get("id"))) for x in reg_agents):
                    edges.append({
                        "source": f"registry:agent:{aid}",
                        "target": f"registry:agent:{sid}",
                        "type": "sub",
                    })
    if reg_groups:
        for g in reg_groups:
            gid = g.get("id")
            if not gid:
                continue
            nid = f"registry:group:{gid}"
            nodes.append({"id": nid, "label": str(gid), "type": "agent_group"})
            for m in g.get("include") or []:
                mid = str(m)
                if mid in reg_agent_ids or any(mid == (x.get("id") and str(x.get("id"))) for x in reg_agents):
                    edges.append({"source": nid, "target": f"registry:agent:{mid}", "type": "member"})

    return {"nodes": nodes, "edges": edges}

