"""
Public API for consumers (e.g., external CLI) to build and interact with
agent systems using this library without bringing in a CLI here.

Surfaces:
- SystemManager: load config, build registries, select root agent, build Runner
- SessionManager: create/resume sessions
- run_text: convenience async generator over Runner.run_async for a text input
- cancel utilities: CancelRegistry (best-effort stub)
- event utils: to_minimal_json for lightweight serialization (no JSONL writing)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from ..agents.builder import build_agents
from ..agents.builders_registry import build_agent_registry_from_config
from ..config.models import AppConfig, load_config_file
from ..runtime.supervisor import build_run_config
from ..tools.builders import build_tool_registry_from_config


class SystemManager:
    """Workspace-aware system builder.

    Usage by external CLI:
    - sm = SystemManager(base_dir=path_to_system)
    - cfg = sm.load()
    - runner, resources = sm.build_runner(cfg)
    """

    def __init__(self, *, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir).resolve()

    def load(self, config_path: str | Path = "config.yaml") -> AppConfig:
        """Load an AppConfig relative to the base_dir (default: config.yaml)."""
        cfg_path = Path(config_path)
        if not cfg_path.is_absolute():
            cfg_path = self.base_dir / cfg_path
        return load_config_file(cfg_path)

    def select_root_agent(self, cfg: AppConfig) -> object:
        """Build registries (if present) or inline agents, and return the root agent.

        Root agent name is normalized to 'root_agent'.
        """
        # Prefer registries when provided
        tool_reg = build_tool_registry_from_config(cfg, base_dir=self.base_dir)
        agent_reg = None
        if cfg.agents_registry:
            agent_reg = build_agent_registry_from_config(
                cfg,
                base_dir=self.base_dir,
                provider_defaults=cfg.model_providers,
                tool_registry=tool_reg,
            )
        root = None
        if agent_reg and (cfg.agents_registry.get("groups") or cfg.agents_registry.get("agents")):
            # Prefer group "core" first member
            try:
                root = agent_reg.get_group("core")[0]
            except Exception:
                # Fall back to an agent id 'parent' commonly used in configs
                try:
                    root = agent_reg.get("parent")
                except Exception:
                    # Fall back to first declared agent id if any
                    ids = [a.get("id") for a in (cfg.agents_registry.get("agents") or []) if a.get("id")]
                    if ids:
                        root = agent_reg.get(ids[0])
        if root is None:
            # Inline agents fallback
            agent_map = build_agents(
                cfg.agents,
                provider_defaults=cfg.model_providers,
                base_dir=str(self.base_dir),
                shared_toolsets=cfg.toolsets,
            )
            if not agent_map:
                raise ValueError("No agents defined in config")
            root = agent_map[cfg.agents[0].name]

        # Normalize name to 'root_agent'
        try:
            setattr(root, "name", "root_agent")
        except Exception:
            pass
        return root

    def build_runner(self, cfg: AppConfig, *, root_agent: Optional[object] = None):
        from google.adk.runners import Runner  # type: ignore

        from ..services.factory import (
            build_artifact_service,
            build_memory_service,
            build_session_service,
        )

        artifact_svc = build_artifact_service(cfg.artifact_service)
        session_svc = build_session_service(cfg.session_service)
        memory_svc = build_memory_service(cfg.memory_service)

        root = root_agent or self.select_root_agent(cfg)
        # Apply global instruction when provided
        if getattr(cfg, "global_instruction", None):
            try:
                setattr(root, "global_instruction", cfg.global_instruction)
            except Exception:
                pass
        runner = Runner(
            app_name="agent-compose-kit",
            agent=root,
            artifact_service=artifact_svc,
            session_service=session_svc,
            memory_service=memory_svc,
        )
        # Provide resources for lifecycle management (e.g., close tool registry)
        resources: Dict[str, Any] = {}
        return runner, resources


class SessionManager:
    def __init__(self, runner) -> None:  # runner: google.adk.runners.Runner
        self.runner = runner

    async def create(self, user_id: str):
        """Create a new session for the given user_id."""
        s = await self.runner.session_service.create_session(
            app_name=self.runner.app_name, user_id=user_id
        )
        return s

    async def get_or_create(self, user_id: str, session_id: Optional[str] = None):
        """Return an existing session or create a new one if missing."""
        if session_id:
            try:
                # In Python ADK, get_session may be async
                sess = await self.runner.session_service.get_session(
                    app_name=self.runner.app_name, user_id=user_id, session_id=session_id
                )
                return sess
            except Exception:
                pass
        return await self.create(user_id)


class CancelRegistry:
    """In-memory cancellation registry (best-effort stub).

    External callers can register a run_id and later request cancellation.
    The run_text generator can consult this registry to stop early.
    """

    def __init__(self) -> None:
        self._cancelled: set[str] = set()

    def cancel(self, run_id: str) -> None:
        self._cancelled.add(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self._cancelled


async def run_text(
    *,
    runner,
    user_id: str,
    session_id: str,
    text: str,
    run_config: Optional[Any] = None,
    run_id: Optional[str] = None,
    cancel_registry: Optional[CancelRegistry] = None,
) -> AsyncGenerator[Any, None]:
    """Convenience wrapper that yields ADK events for a single text input.

    Consumers can stream these events and map to UI as needed.
    """
    from google.genai import types  # type: ignore

    content = types.Content(role="user", parts=[types.Part(text=text)])
    # Note: ADK runner.run_async itself doesn't accept a cancel token; we provide
    # cooperative cancellation by checking registry between yields.
    async for ev in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
        run_config=run_config or build_run_config(AppConfig()),
    ):
        if cancel_registry and run_id and cancel_registry.is_cancelled(run_id):
            break
        yield ev


def event_to_minimal_json(event: Any) -> Dict[str, Any]:
    """Serialize an ADK event into a small, portable dict (no file I/O)."""
    d: Dict[str, Any] = {
        "id": getattr(event, "id", None),
        "author": getattr(event, "author", None),
        "partial": bool(getattr(event, "partial", False)),
        "timestamp": getattr(event, "timestamp", None),
    }
    content = getattr(event, "content", None)
    if content is not None and getattr(content, "parts", None) is not None:
        parts_out = []
        for p in content.parts:
            obj: Dict[str, Any] = {}
            if getattr(p, "text", None) is not None:
                obj["text"] = p.text
            if getattr(p, "function_call", None) is not None:
                fc = getattr(p, "function_call")
                obj["function_call"] = fc._asdict() if hasattr(fc, "_asdict") else str(fc)
            if getattr(p, "function_response", None) is not None:
                fr = getattr(p, "function_response")
                obj["function_response"] = fr._asdict() if hasattr(fr, "_asdict") else str(fr)
            parts_out.append(obj)
        d["content"] = {"parts": parts_out}
    return d
