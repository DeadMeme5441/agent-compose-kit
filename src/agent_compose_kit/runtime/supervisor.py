from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..agents.builder import build_agents
from ..config.models import AppConfig, load_config_file
from ..services.factory import (
    build_artifact_service,
    build_memory_service,
    build_session_service,
)


def build_plan(cfg: AppConfig) -> str:
    """Return a human-readable plan summary derived from AppConfig."""
    lines = []
    lines.append("Plan:")
    lines.append(f"- SessionService: {cfg.session_service.type}")
    lines.append(f"- ArtifactService: {cfg.artifact_service.type}")
    if cfg.memory_service and cfg.memory_service.type:
        lines.append(f"- MemoryService: {cfg.memory_service.type}")
    lines.append(f"- Agents: {[a.name for a in cfg.agents]}")
    if cfg.groups:
        lines.append(f"- Groups: {[g.name for g in cfg.groups]}")
    return "\n".join(lines)


def build_runner_from_yaml(*, config_path: Path, user_id: str, session_id: Optional[str] = None):
    """Build a Runner and create a session from a YAML config path.

    Returns a tuple (runner, session). Root agent is named `root_agent`.
    Applies `global_instruction` to the root agent when provided.
    """
    cfg = load_config_file(config_path)

    # Services
    artifact_service = build_artifact_service(cfg.artifact_service)
    session_service = build_session_service(cfg.session_service)
    memory_service = build_memory_service(cfg.memory_service)

    # Agents
    # Build A2A clients mapping for remote agents
    a2a_map: dict[str, object] = {}
    for c in (cfg.a2a_clients or []):
        try:
            a2a_map[c.id] = c
        except Exception:
            a2a_map[str(getattr(c, "id", ""))] = c
    agent_map = build_agents(
        cfg.agents,
        provider_defaults=cfg.model_providers,
        a2a_clients=a2a_map,
    )
    if not agent_map:
        raise ValueError("No agents defined in config")
    # Choose root: workflow if defined, else first agent
    root_agent = None
    if cfg.workflow and cfg.workflow.type and cfg.workflow.nodes:
        wf_type = cfg.workflow.type
        nodes = [agent_map[n] for n in cfg.workflow.nodes if n in agent_map]
        if wf_type == "sequential":
            from google.adk.agents.sequential_agent import SequentialAgent  # type: ignore

            root_agent = SequentialAgent(name="root_agent", sub_agents=nodes)
        elif wf_type == "parallel":
            from google.adk.agents.parallel_agent import ParallelAgent  # type: ignore

            root_agent = ParallelAgent(name="root_agent", sub_agents=nodes)
        elif wf_type == "loop":
            from google.adk.agents.loop_agent import LoopAgent  # type: ignore

            root_agent = LoopAgent(name="root_agent", sub_agents=nodes)
    if root_agent is None:
        root_name = cfg.agents[0].name
        root_agent = agent_map[root_name]
    # Normalize root agent name
    try:
        setattr(root_agent, "name", "root_agent")
    except Exception:
        pass
    # Apply global instruction if provided
    if getattr(cfg, "global_instruction", None):
        try:
            setattr(root_agent, "global_instruction", cfg.global_instruction)
        except Exception:
            pass

    from google.adk.runners import Runner  # type: ignore

    runner = Runner(
        app_name="template-agent-builder",
        agent=root_agent,  # type: ignore[arg-type]
        artifact_service=artifact_service,
        session_service=session_service,
        memory_service=memory_service,
    )

    # Create or resume session
    if session_id:
        session = runner.session_service.get_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
        # if async, user can resume; for simplicity, always create new when not exists
        # In ADK Python, get_session is async; keeping simple here, use create
    # Always create a new session for now
    import asyncio

    async def _create():
        return await runner.session_service.create_session(
            app_name=runner.app_name, user_id=user_id
        )

    session = asyncio.run(_create())
    return runner, session


def build_run_config(cfg: AppConfig):
    """Construct ADK RunConfig from AppConfig.runtime (streaming, limits)."""
    """Construct ADK RunConfig from YAML runtime section."""
    from google.adk.agents.run_config import RunConfig, StreamingMode  # type: ignore

    # Map streaming_mode string to enum
    mode = None
    sm = getattr(cfg.runtime, "streaming_mode", None)
    if isinstance(sm, str):
        sm_up = sm.upper()
        if sm_up in ("NONE", "SSE", "BIDI"):
            mode = getattr(StreamingMode, sm_up)

    return RunConfig(
        streaming_mode=mode,
        max_llm_calls=getattr(cfg.runtime, "max_llm_calls", None) or 500,
        save_input_blobs_as_artifacts=bool(
            getattr(cfg.runtime, "save_input_blobs_as_artifacts", False)
        ),
    )
