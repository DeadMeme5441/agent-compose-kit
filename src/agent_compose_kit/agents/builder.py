from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from ..config.models import AgentConfig
from ..tools.loader import load_tool_list, load_toolsets_map
from pathlib import Path


def _resolve_model(model_spec: Any, provider_defaults: Mapping[str, Dict[str, Any]] | None = None):
    """Resolve a model specification into an ADK model object or string id.

    Accepts:
    - A plain string model id (e.g., "gemini-2.0-flash").
    - A mapping for LiteLLM, either {type: litellm, ...} or a dict with a
      `litellm` key. Merges provider defaults (e.g., OpenAI keys) by provider
      prefix of the model name.
    Returns a model object suitable for LlmAgent, or the original spec when
    unrecognized.
    """
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
    """Build concrete LlmAgent instances from AgentConfig entries.

    - Resolves models via `_resolve_model` with provider defaults.
    - Loads tools via unified loader; supports shared `toolsets`.
    - Applies optional LlmAgent advanced parameters when provided (description,
      include_contents, output_key, planner, generate_content_config, code_executor,
      input_schema/output_schema).
    - Performs a second pass to wire `sub_agents` references by name.
    """
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

        kwargs: Dict[str, Any] = {
            "name": cfg.name,
            "model": model_obj,
            "instruction": cfg.instruction or "",
            "tools": tools,
        }
        if cfg.description:
            kwargs["description"] = cfg.description
        if cfg.include_contents:
            kwargs["include_contents"] = cfg.include_contents
        if cfg.output_key:
            kwargs["output_key"] = cfg.output_key
        # generate_content_config mapping
        if cfg.generate_content_config:
            try:
                from google.genai import types  # type: ignore

                kwargs["generate_content_config"] = types.GenerateContentConfig(**cfg.generate_content_config)
            except Exception:
                # Ignore if types not available
                pass
        # input/output schema as dotted refs to Pydantic BaseModel
        def _import_dotted(ref: Optional[str]):
            if not ref:
                return None
            if ":" in ref:
                mod, attr = ref.split(":", 1)
            else:
                parts = ref.split(".")
                mod, attr = ".".join(parts[:-1]), parts[-1]
            m = __import__(mod, fromlist=[attr])
            return getattr(m, attr)

        try:
            if cfg.input_schema:
                kwargs["input_schema"] = _import_dotted(cfg.input_schema)
        except Exception:
            pass
        try:
            if cfg.output_schema:
                kwargs["output_schema"] = _import_dotted(cfg.output_schema)
        except Exception:
            pass
        # Planner
        if cfg.planner:
            ptype = str(cfg.planner.get("type", "")).lower()
            try:
                if ptype in ("built_in", "builtin", "built-in"):
                    from google.adk.planners import BuiltInPlanner  # type: ignore
                    from google.genai import types  # type: ignore

                    tc = cfg.planner.get("thinking_config") or {}
                    thinking_cfg = types.ThinkingConfig(**tc) if tc else None
                    kwargs["planner"] = BuiltInPlanner(thinking_config=thinking_cfg) if thinking_cfg else BuiltInPlanner()
                elif ptype in ("plan_react", "plan-react", "planreact"):
                    from google.adk.planners import PlanReActPlanner  # type: ignore

                    kwargs["planner"] = PlanReActPlanner()
                elif cfg.planner.get("ref"):
                    kwargs["planner"] = _import_dotted(str(cfg.planner["ref"]))
            except Exception:
                # Planner optional
                pass
        # Code executor (dotted ref)
        if cfg.code_executor:
            try:
                kwargs["code_executor"] = _import_dotted(cfg.code_executor)
            except Exception:
                pass

        agent = LlmAgent(**kwargs)
        temp[cfg.name] = agent
        pending_tools[cfg.name] = tools

    # Second pass: wire sub_agents
    for cfg in agent_cfgs:
        if cfg.sub_agents:
            sub = [temp[name] for name in cfg.sub_agents if name in temp]
            temp[cfg.name].sub_agents = sub  # type: ignore[attr-defined]

    agents.update(temp)
    return agents
