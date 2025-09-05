from __future__ import annotations

from typing import Any, Dict, List, Mapping

from ..config.models import AgentConfig
from ..tools.loader import load_tool_list, load_toolsets_map
from pathlib import Path


def _resolve_model(model_spec: Any, provider_defaults: Mapping[str, Dict[str, Any]] | None = None):
    # Accept plain string or LiteLLM mapping
    if isinstance(model_spec, str):
        return model_spec

    if isinstance(model_spec, dict):
        t = model_spec.get("type") or ("litellm" if "litellm" in model_spec else None)
        if t == "litellm":
            cfg = dict(model_spec.get("litellm", model_spec))
            # Merge provider-level defaults if present
            provider_defaults = provider_defaults or {}
            model_name = cfg.get("model", "")
            if isinstance(model_name, str) and "/" in model_name:
                provider = model_name.split("/", 1)[0]
                defaults = provider_defaults.get(provider, {})
                # do not overwrite explicit values
                for k, v in defaults.items():
                    cfg.setdefault(k, v)
            from google.adk.models.lite_llm import LiteLlm  # type: ignore

            return LiteLlm(
                model=cfg.get("model"),
                api_base=cfg.get("api_base"),
                api_key=cfg.get("api_key"),
                extra_headers=cfg.get("extra_headers"),
            )

    # Fallback: pass through
    return model_spec


def build_agents(
    agent_cfgs: List[AgentConfig],
    *,
    provider_defaults: Mapping[str, Dict[str, Any]] | None = None,
    base_dir: str | None = None,
    shared_toolsets: Mapping[str, Any] | None = None,
):
    # Build concrete LlmAgent instances from configs
    agents: Dict[str, object] = {}
    from google.adk.agents import LlmAgent  # type: ignore
    base = Path(base_dir or ".").resolve()
    toolsets_map = load_toolsets_map(shared_toolsets or {}, base_dir=base)

    # First pass: create shells without sub_agents to allow references
    temp: Dict[str, Any] = {}
    pending_tools: Dict[str, List[Any]] = {}
    for cfg in agent_cfgs:
        model_obj = _resolve_model(cfg.model, provider_defaults)
        tools = load_tool_list(cfg.tools or [], base_dir=base, toolsets_map=toolsets_map)
        agent = LlmAgent(name=cfg.name, model=model_obj, instruction=cfg.instruction or "", tools=tools)
        temp[cfg.name] = agent
        pending_tools[cfg.name] = tools

    # Second pass: wire sub_agents
    for cfg in agent_cfgs:
        if cfg.sub_agents:
            sub = [temp[name] for name in cfg.sub_agents if name in temp]
            temp[cfg.name].sub_agents = sub  # type: ignore[attr-defined]

    agents.update(temp)
    return agents
