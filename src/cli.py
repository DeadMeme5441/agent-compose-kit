import os
import sys
from pathlib import Path
from typing import Optional

import click

from .runtime.supervisor import build_plan, build_runner_from_yaml
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
                runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content)
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
