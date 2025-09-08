from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
import difflib
import hashlib


@dataclass
class PatchOp:
    """Single JSON-Pointer patch operation.

    Attributes:
        op: Operation kind: ``add`` | ``replace`` | ``remove``.
        path: JSON Pointer to target location (e.g., ``/agents/0/model``).
        value: Optional value for ``add``/``replace`` operations.
    """
    op: str  # 'add' | 'replace' | 'remove'
    path: str  # JSON Pointer (e.g., /agents/0/model)
    value: Any | None = None


@dataclass
class QuickFix:
    """A human-readable quick fix with machine-applicable patch ops.

    Attributes:
        id: Stable identifier for the fix.
        title: Short, actionable label for UIs.
        description: One-line description of the issue and remedy.
        ops: List of patch operations to apply.
    """
    id: str
    title: str
    description: str
    ops: List[PatchOp] = field(default_factory=list)


def _find_agent_index(raw_cfg: Dict[str, Any], agent_name: str) -> Optional[int]:
    """Return index of an agent by name from a raw config dict.

    Args:
        raw_cfg: Raw configuration mapping.
        agent_name: Agent ``name`` to search for.

    Returns:
        Integer index when found; otherwise ``None``.
    """
    agents = list(raw_cfg.get("agents") or [])
    for i, a in enumerate(agents):
        if isinstance(a, dict) and a.get("name") == agent_name:
            return i
    return None


def _agent_names(raw_cfg: Dict[str, Any]) -> List[str]:
    """Return all declared agent names from a raw config dict."""
    return [a.get("name") for a in (raw_cfg.get("agents") or []) if isinstance(a, dict) and a.get("name")]


def _closest(name: str, choices: Sequence[str]) -> Optional[str]:
    """Return closest string match using difflib or ``None``.

    Args:
        name: Input string to match.
        choices: Sequence of candidate strings.

    Returns:
        Best match above threshold, or ``None`` when no suitable match exists.
    """
    matches = difflib.get_close_matches(name, choices, n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_quick_fixes(
    *,
    raw_cfg: Dict[str, Any],
    validation_error: Optional[str] = None,
    indexes: Optional[Dict[str, Any]] = None,
) -> List[QuickFix]:
    """Derive quick-fixes from a raw config dict and optional validation error text.

    This is offline and conservative: proposes JSON-Pointer patch ops; it does not mutate input.

    Implemented fixes (S3):
    - LLM missing model and defaults.model_alias → add alias model
    - sequential/parallel with empty/missing sub_agents → seed with a plausible local agent
    - unknown sub_agent name → suggest replacement to closest local name
    - sequential upstream LLM missing output_key → add output_key
    - move generate_content_config.thinking_config → planner.built_in.thinking_config
    - plan_react + output_schema → remove output_schema
    - missing defaults.model_alias with LLM missing model → add defaults with chat-default
    """
    fx: List[QuickFix] = []
    agents = list(raw_cfg.get("agents") or [])
    local_names = _agent_names(raw_cfg)

    # Helper: resolve defaults.model_alias (string)
    defaults = raw_cfg.get("defaults") or {}
    default_alias = defaults.get("model_alias") if isinstance(defaults, dict) else None

    # 1) LLM missing model and defaults.model_alias → add model alias
    for idx, a in enumerate(agents):
        if not isinstance(a, dict):
            continue
        if a.get("type") == "llm" and (a.get("model") is None):
            if default_alias:
                fx.append(
                    QuickFix(
                        id=f"llm-model-{idx}",
                        title=f"Set model to alias://{default_alias}",
                        description="Use defaults.model_alias for this LLM agent",
                        ops=[PatchOp(op="add", path=f"/agents/{idx}/model", value=f"alias://{default_alias}")],
                    )
                )

    # 2) workflow agents with empty/missing sub_agents → seed
    for idx, a in enumerate(agents):
        if not isinstance(a, dict):
            continue
        if a.get("type") in {"workflow.sequential", "workflow.parallel"}:
            subs = a.get("sub_agents")
            if not subs:
                # choose first other local agent
                candidate = next((n for n in local_names if n != a.get("name")), None)
                if candidate:
                    fx.append(
                        QuickFix(
                            id=f"seed-subs-{idx}",
                            title=f"Add sub_agents with '{candidate}'",
                            description="Seed workflow with an existing agent",
                            ops=[PatchOp(op="add", path=f"/agents/{idx}/sub_agents", value=[candidate])],
                        )
                    )

    # 3) unknown sub_agent names → replace with closest
    for idx, a in enumerate(agents):
        if not isinstance(a, dict):
            continue
        subs = a.get("sub_agents") or []
        if not isinstance(subs, list):
            continue
        for j, s in enumerate(subs):
            if isinstance(s, str) and s not in local_names:
                new_name = _closest(s, local_names)
                if new_name:
                    fx.append(
                        QuickFix(
                            id=f"fix-subref-{idx}-{j}",
                            title=f"Replace '{s}' with '{new_name}'",
                            description="Unknown sub_agent reference; replace with closest name",
                            ops=[PatchOp(op="replace", path=f"/agents/{idx}/sub_agents/{j}", value=new_name)],
                        )
                    )

    # 4) sequential upstream LLM missing output_key → add
    # Detect simple chains by name list; for each sequential agent, check consecutive pairs
    for a in agents:
        if not isinstance(a, dict) or a.get("type") != "workflow.sequential":
            continue
        seq = [s for s in (a.get("sub_agents") or []) if isinstance(s, str)]
        for i in range(len(seq) - 1):
            up = seq[i]
            up_idx = _find_agent_index(raw_cfg, up)
            if up_idx is None:
                continue
            up_ag = agents[up_idx]
            if isinstance(up_ag, dict) and up_ag.get("type") == "llm" and not up_ag.get("output_key"):
                key = f"{up_ag.get('name','agent')}_output"
                fx.append(
                    QuickFix(
                        id=f"add-output-key-{up_idx}",
                        title=f"Add output_key '{key}'",
                        description="Sequential pipeline: give upstream LLM an output_key for downstream input",
                        ops=[PatchOp(op="add", path=f"/agents/{up_idx}/output_key", value=key)],
                    )
                )

    # 5) move thinking_config from generate_content_config to planner.built_in
    for idx, a in enumerate(agents):
        if not isinstance(a, dict) or a.get("type") != "llm":
            continue
        gcc = a.get("generate_content_config") or {}
        if isinstance(gcc, dict) and "thinking_config" in gcc:
            tc = gcc.get("thinking_config")
            ops = [
                PatchOp(op="add", path=f"/agents/{idx}/planner", value={"type": "built_in", "thinking_config": tc}),
                PatchOp(op="remove", path=f"/agents/{idx}/generate_content_config/thinking_config"),
            ]
            fx.append(
                QuickFix(
                    id=f"move-thinking-{idx}",
                    title="Move thinking_config to planner.built_in",
                    description="Align with ADK: thinking_config belongs under planner",
                    ops=ops,
                )
            )

    # 6) plan_react with output_schema → remove output_schema
    for idx, a in enumerate(agents):
        if not isinstance(a, dict) or a.get("type") != "llm":
            continue
        if (a.get("planner") or {}).get("type") == "plan_react" and a.get("output_schema"):
            fx.append(
                QuickFix(
                    id=f"rm-output-schema-{idx}",
                    title="Remove output_schema (Plan-Re-Act expects tools)",
                    description="Plan-Re-Act conflicts with structured output; remove output_schema",
                    ops=[PatchOp(op="remove", path=f"/agents/{idx}/output_schema")],
                )
            )

    # 7) No defaults but LLM missing model → add defaults.model_alias
    if not default_alias:
        needs_default = any(isinstance(a, dict) and a.get("type") == "llm" and not a.get("model") for a in agents)
        if needs_default:
            fx.append(
                QuickFix(
                    id="add-defaults-model-alias",
                    title="Add defaults.model_alias: chat-default",
                    description="Provide a default model alias for LLM agents",
                    ops=[PatchOp(op="add", path="/defaults", value={"model_alias": "chat-default"})],
                )
            )

    # 8) Unknown operationId/tool suggestions if indexes provided
    if indexes:
        op_ids = set(indexes.get("openapi_operationIds") or [])
        for idx, a in enumerate(agents):
            if not isinstance(a, dict) or a.get("type") != "llm":
                continue
            for j, t in enumerate(a.get("tools") or []):
                if not isinstance(t, dict):
                    continue
                if t.get("kind") == "openapi":
                    op = t.get("operationId")
                    if isinstance(op, str) and op_ids and op not in op_ids:
                        close = _closest(op, list(op_ids))
                        if close:
                            fx.append(
                                QuickFix(
                                    id=f"fix-opid-{idx}-{j}",
                                    title=f"Replace operationId '{op}' with '{close}'",
                                    description="Unknown operationId; replace with closest match from index",
                                    ops=[PatchOp(op="replace", path=f"/agents/{idx}/tools/{j}/operationId", value=close)],
                                )
                            )

            return fx

    # 9) Missing model alias declarations → add stub entries
    # Collect declared alias ids
    decl: set[str] = set()
    reg = raw_cfg.get("model_aliases") or {}
    for a in reg.get("aliases") or []:
        if isinstance(a, dict) and isinstance(a.get("id"), str):
            decl.add(a["id"])
    # Collect used aliases
    used: set[str] = set()
    dflt = raw_cfg.get("defaults") or {}
    if isinstance(dflt.get("model_alias"), str):
        used.add(dflt["model_alias"])
    for a in agents:
        if isinstance(a, dict):
            m = a.get("model")
            if isinstance(m, str) and m.startswith("alias://"):
                used.add(m.split("alias://", 1)[1])
    for missing in sorted(used - decl):
        fx.append(
            QuickFix(
                id=f"add-alias-{missing}",
                title=f"Declare model alias '{missing}'",
                description="Add a model alias entry (resolver: direct)",
                ops=[
                    PatchOp(
                        op="add",
                        path="/model_aliases/aliases/-",
                        value={
                            "id": missing,
                            "resolver": "direct",
                            "model": "gemini-2.0-flash",
                            "labels": {},
                        },
                    )
                ],
            )
        )

    return fx

    


# Utilities (S7): lightweight helpers consumed by external tooling

def fingerprint(cfg: Dict[str, Any]) -> str:
    """Stable fingerprint for a config dict (sha256 of normalized JSON-like bytes)."""
    import json

    def _normalize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _normalize(obj[k]) for k in sorted(obj.keys())}
        if isinstance(obj, list):
            return [_normalize(x) for x in obj]
        return obj

    norm = _normalize(cfg)
    raw = json.dumps(norm, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def list_dependencies(raw_cfg: Dict[str, Any]) -> Dict[str, List[str]]:
    """Collect external references: registry refs, model aliases, agent refs."""
    reg: List[str] = []
    aliases: List[str] = []
    agent_refs: List[str] = []
    # defaults
    d = raw_cfg.get("defaults") or {}
    if isinstance(d, dict) and isinstance(d.get("model_alias"), str):
        aliases.append(d["model_alias"])  # alias name only
    # agents/tools
    for a in raw_cfg.get("agents") or []:
        if not isinstance(a, dict):
            continue
        m = a.get("model")
        if isinstance(m, str) and m.startswith("alias://"):
            aliases.append(m.split("alias://", 1)[1])
        # sub_agents by name only; registry refs appear as dicts
        for s in a.get("sub_agents") or []:
            if isinstance(s, str):
                agent_refs.append(s)
            elif isinstance(s, dict) and isinstance(s.get("value"), str) and s.get("value").startswith("registry://"):
                reg.append(s["value"])  # store raw
        for t in a.get("tools") or []:
            if not isinstance(t, dict):
                continue
            for key in ("server", "spec", "function", "agent"):
                v = t.get(key)
                if isinstance(v, dict) and isinstance(v.get("ref"), dict) and isinstance(v["ref"].get("value"), str):
                    val = v["ref"]["value"]
                    if val.startswith("registry://"):
                        reg.append(val)
    return {
        "registryRefs": sorted(set(reg)),
        "modelAliases": sorted(set(aliases)),
        "agentRefs": sorted(set(agent_refs)),
    }


def lint(raw_cfg: Dict[str, Any]) -> Dict[str, List[str]]:
    """Light lint rules; advisory only."""
    warnings: List[str] = []
    infos: List[str] = []
    # Single-parent rule (advisory): an agent should not appear in sub_agents of multiple parents frequently
    parent_count: Dict[str, int] = {}
    for a in raw_cfg.get("agents") or []:
        if not isinstance(a, dict):
            continue
        for s in a.get("sub_agents") or []:
            if isinstance(s, str):
                parent_count[s] = parent_count.get(s, 0) + 1
    for name, cnt in parent_count.items():
        if cnt > 1:
            warnings.append(f"Agent '{name}' is referenced by {cnt} parents; consider duplication or registry refs")
    # Parallel fan-out advisory
    for a in raw_cfg.get("agents") or []:
        if not isinstance(a, dict):
            continue
        if a.get("type") == "workflow.parallel":
            n = len(a.get("sub_agents") or [])
            if n > 6:
                infos.append(f"Parallel agent '{a.get('name','')}' fans out to {n} sub_agents; ensure downstream synthesis")
    return {"warnings": warnings, "infos": infos}
