from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RegistryPin:
    kind: str
    key: str
    range: str
    pinned: Optional[str]  # resolved version
    etag: Optional[str] = None
    uri: Optional[str] = None
    ref: Optional[str] = None  # original raw ref string
    error: Optional[str] = None


@dataclass(frozen=True)
class AliasPin:
    alias: str
    provider: Optional[str]
    model: Optional[str]
    resolver: Optional[str] = None
    secret_ref: Optional[str] = None
    params_fingerprint: Optional[str] = None


@dataclass(frozen=True)
class LockfilePlan:
    registryPins: List[RegistryPin]
    aliasPins: List[AliasPin]


def _to_raw(cfg: Any) -> Dict[str, Any]:
    """Return a plain dict for a Pydantic model or mapping.

    Args:
        cfg: ``AppConfig`` instance or raw mapping.

    Returns:
        A plain Python ``dict`` suitable for dependency scanning.
    """
    if hasattr(cfg, "model_dump"):
        return cfg.model_dump()  # type: ignore[attr-defined]
    return dict(cfg)


def _parse_registry_ref(value: str) -> Tuple[str, str, str]:
    """Parse a registry ref into components.

    Args:
        value: Reference like ``registry://{kind}/{key}@{version|range|latest}``.

    Returns:
        Tuple ``(kind, key, range)`` with defaults applied.

    Raises:
        ValueError: If the value is not a registry ref or is malformed.
    """
    if not isinstance(value, str) or not value.startswith("registry://"):
        raise ValueError("invalid registry ref")
    rest = value[len("registry://") :]
    if "@" in rest:
        path, ver = rest.split("@", 1)
    else:
        path, ver = rest, "latest"
    if "/" not in path:
        raise ValueError("invalid registry ref path")
    kind, key = path.split("/", 1)
    return kind, key, ver


def plan_lock(
    cfg: Any,
    registry_resolves: Callable[[str, str, str], Dict[str, Any]],
    alias_resolves: Callable[[str], Dict[str, Any]],
) -> LockfilePlan:
    """Compute a deterministic lock plan from a config and resolver callbacks.

    - Extracts unique registry refs and model aliases (order-independent).
    - Calls provided resolvers to pin versions and alias details (offline).
    - Returns a stable structure suitable for serialization.
    """
    from ..quickfix.fixes import list_dependencies

    raw = _to_raw(cfg)
    deps = list_dependencies(raw)
    reg_values: List[str] = deps.get("registryRefs", [])
    aliases: List[str] = deps.get("modelAliases", [])

    # Registry pins
    reg_pins: List[RegistryPin] = []
    seen_reg: set[Tuple[str, str, str]] = set()
    for ref in sorted(set(reg_values)):
        try:
            kind, key, rng = _parse_registry_ref(ref)
        except Exception as e:
            reg_pins.append(RegistryPin(kind="unknown", key=ref, range="", pinned=None, ref=ref, error=str(e)))
            continue
        triple = (kind, key, rng)
        if triple in seen_reg:
            continue
        seen_reg.add(triple)
        try:
            resolved = registry_resolves(kind, key, rng) or {}
            pin = RegistryPin(
                kind=kind,
                key=key,
                range=rng,
                pinned=resolved.get("version"),
                etag=resolved.get("etag"),
                uri=resolved.get("uri"),
                ref=ref,
            )
        except Exception as e:
            pin = RegistryPin(kind=kind, key=key, range=rng, pinned=None, ref=ref, error=str(e))
        reg_pins.append(pin)

    # Alias pins
    alias_pins: List[AliasPin] = []
    for alias in sorted(set(aliases)):
        try:
            r = alias_resolves(alias) or {}
            params = r.get("params") or {}
            # fingerprint params if provided as dict
            params_fp = None
            if isinstance(params, dict) and params:
                import json, hashlib

                raw = json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")
                params_fp = hashlib.sha256(raw).hexdigest()
            alias_pins.append(
                AliasPin(
                    alias=alias,
                    provider=r.get("provider"),
                    model=r.get("model"),
                    resolver=r.get("resolver"),
                    secret_ref=r.get("secret_ref"),
                    params_fingerprint=params_fp,
                )
            )
        except Exception:
            alias_pins.append(AliasPin(alias=alias, provider=None, model=None, resolver=None, secret_ref=None, params_fingerprint=None))

    # Sort deterministically
    reg_pins = sorted(reg_pins, key=lambda p: (p.kind or "", p.key or "", p.range or "", p.pinned or ""))
    alias_pins = sorted(alias_pins, key=lambda a: a.alias)
    return LockfilePlan(registryPins=reg_pins, aliasPins=alias_pins)
