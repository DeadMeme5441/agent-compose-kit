import os
import sys
from pathlib import Path
from typing import Optional

import click

from .runtime.supervisor import build_plan, build_runner_from_yaml, build_run_config
from .config.models import load_config_file, write_example_config


@click.group(help="Template Agent Builder CLI")
def app() -> None:
    pass


@app.command()
@click.option("--out", "out_path", type=click.Path(dir_okay=False, path_type=Path), default=Path("configs/app.yaml"))
def init(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_example_config(out_path)
    click.echo(f"Wrote template config to {out_path}")


@app.command()
@click.argument("config", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate(config: Path) -> None:
    _ = load_config_file(config)
    click.echo("Config OK ✅")


@app.command()
@click.argument("config", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def plan(config: Path) -> None:
    cfg = load_config_file(config)
    summary = build_plan(cfg)
    click.echo(summary)


@app.command()
@click.argument("config", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--user", "user_id", default="user", help="User ID for the session")
@click.option("--session", "session_id", default=None, help="Optional session id to resume")
def run(config: Path, user_id: str, session_id: Optional[str]) -> None:
    try:
        runner, session = build_runner_from_yaml(config_path=Path(config), user_id=user_id, session_id=session_id)
    except ImportError as e:
        click.echo("google-adk not installed. Please: uv run --with google-adk python -m src.main ...", err=True)
        raise SystemExit(1) from e
    except Exception as e:  # validation or wiring error
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    # Interactive loop
    click.echo("Type 'exit' to quit.\n")
    try:
        from google.genai import types  # type: ignore
    except Exception as e:  # pragma: no cover
        click.echo("google-generativeai missing; install google-adk extras.", err=True)
        raise SystemExit(1) from e

    # Build run config once
    rc = build_run_config(load_config_file(config))

    async def _loop() -> None:
        from google.adk.utils.context_utils import Aclosing  # type: ignore

        while True:
            query = input("[user]: ").strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                break
            content = types.Content(role="user", parts=[types.Part(text=query)])
            async with Aclosing(
                runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content, run_config=rc)
            ) as agen:
                async for event in agen:
                    if event.content and event.content.parts:
                        text = "".join(part.text or "" for part in event.content.parts)
                        if text:
                            click.echo(f"[{event.author}]: {text}")

    import asyncio

    try:
        asyncio.run(_loop())
    finally:
        # best-effort cleanup
        try:
            asyncio.run(runner.close())
        except Exception:
            pass


@app.command()
@click.argument("config", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--dot", is_flag=True, help="Output Graphviz DOT instead of ASCII")
def graph(config: Path, dot: bool) -> None:
    """Print a simple graph of agents and workflow composition."""
    cfg = load_config_file(config)
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
            # star from first
            for i in range(1, len(n)):
                edges.append((n[0], n[i]))
        elif cfg.workflow.type == "loop":
            for i in range(len(n)):
                edges.append((n[i], n[(i + 1) % len(n)]))

    if dot:
        click.echo("digraph flow {")
        for a in agent_names:
            click.echo(f'  "{a}";')
        for s, d in edges:
            click.echo(f'  "{s}" -> "{d}";')
        click.echo("}")
        return

    # ASCII
    seen = set()
    for s, d in edges:
        click.echo(f"{s} -> {d}")
        seen.add(s); seen.add(d)
    missing = [a for a in agent_names if a not in seen]
    if missing:
        click.echo(f"(isolated) {' '.join(missing)}")
