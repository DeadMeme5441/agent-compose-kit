from __future__ import annotations

from typing import Any, Dict, List


def validate_aliases(raw_cfg: Dict[str, Any]) -> Dict[str, List[str]]:
    """Return unknown aliases referenced by defaults or agents.

    Does not mutate; expects a raw dict (e.g., cfg.model_dump()).
    """
    declared = set()
    reg = raw_cfg.get("model_aliases") or {}
    for a in reg.get("aliases", []) or []:
        if isinstance(a, dict) and isinstance(a.get("id"), str):
            declared.add(a["id"])

    used = set()
    dflt = raw_cfg.get("defaults") or {}
    if isinstance(dflt.get("model_alias"), str):
        used.add(dflt["model_alias"])
    for a in raw_cfg.get("agents") or []:
        if not isinstance(a, dict):
            continue
        m = a.get("model")
        if isinstance(m, str) and m.startswith("alias://"):
            used.add(m.split("alias://", 1)[1])

    unknown = sorted(used - declared)
    return {"unknown_aliases": unknown}

