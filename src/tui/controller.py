from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Optional

from ..config.models import load_config_file
from ..runtime.supervisor import build_plan, build_runner_from_yaml, build_run_config


def validate_config(path: Path) -> tuple[bool, str]:
    try:
        _ = load_config_file(path)
        return True, "Config OK"
    except Exception as e:  # pragma: no cover
        return False, str(e)


def plan_config(path: Path) -> str:
    cfg = load_config_file(path)
    return build_plan(cfg)


def graph_ascii(path: Path) -> str:
    # reuse CLI logic simplified
    cfg = load_config_file(path)
    agent_names = [a.name for a in cfg.agents]
    edges = []
    # sub_agent edges
    subs = {a.name: a.sub_agents for a in cfg.agents}
    for a, children in subs.items():
        for c in children:
            edges.append((a, c))
    # workflow edges
    if cfg.workflow and cfg.workflow.nodes:
        n = cfg.workflow.nodes
        if cfg.workflow.type == "sequential":
            for i in range(len(n) - 1):
                edges.append((n[i], n[i + 1]))
        elif cfg.workflow.type == "parallel":
            for i in range(1, len(n)):
                edges.append((n[0], n[i]))
        elif cfg.workflow.type == "loop":
            for i in range(len(n)):
                edges.append((n[i], n[(i + 1) % len(n)]))
    lines = [f"{s} -> {d}" for s, d in edges]
    if not lines:
        lines.append("(no edges)")
    return "\n".join(lines)


async def run_stream(path: Path, user_id: str = "user", session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    from google.genai import types  # type: ignore
    from google.adk.utils.context_utils import Aclosing  # type: ignore

    runner, session = build_runner_from_yaml(config_path=path, user_id=user_id, session_id=session_id)
    rc = build_run_config(load_config_file(path))
    # Greeter
    yield "[system]: Running. Type 'exit' in CLI mode to stop."
    # For TUI, we can emit a placeholder; the actual interactive input will come from UI.
    # Here we just perform a single turn with a default prompt for smoke; UI will manage its own turns.
    content = types.Content(role="user", parts=[types.Part(text="hello")])
    async with Aclosing(
        runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content, run_config=rc)
    ) as agen:
        async for event in agen:
            if event.content and event.content.parts:
                text = "".join(part.text or "" for part in event.content.parts)
                if text:
                    yield f"[{event.author}]: {text}"
    yield "[system]: Finished"

