"""Path and environment helpers for external consumers (e.g., CLI).

Environment variables (defaults in parentheses):
- AGENT_SYS_DIR: base directory for user agent systems ("./systems")
- AGENT_OUTPUTS_DIR: base directory for outputs/artifacts ("./outputs")
- AGENT_SESSIONS_URI: default sessions storage URI ("sqlite:///./sessions.db")

These helpers do not perform any I/O beyond path resolution.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_systems_root() -> Path:
    return Path(os.environ.get("AGENT_SYS_DIR", "./systems")).resolve()


def get_outputs_root() -> Path:
    return Path(os.environ.get("AGENT_OUTPUTS_DIR", "./outputs")).resolve()


def get_sessions_uri() -> str:
    return os.environ.get("AGENT_SESSIONS_URI", "sqlite:///./sessions.db")


def resolve_system_dir(name: str) -> Path:
    """Return the folder for a named system under systems root.

    Convention: each system folder contains a config file (e.g., config.yaml).
    """
    return (get_systems_root() / name).resolve()


def resolve_outputs_dir(system_name: str, session_id: str | None = None) -> Path:
    """Return the folder for outputs; optionally nest by session id."""
    base = get_outputs_root() / system_name
    return (base / session_id) if session_id else base
