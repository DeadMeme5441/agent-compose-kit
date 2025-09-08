"""Unified public facade for core composer functionality (no runtime side-effects).

Exports:
- load_config, load_config_file, export_app_config_schema, AppConfig
- build_system_graph
- get_quick_fixes, PatchOp, QuickFix
- fingerprint, list_dependencies, lint
- plan_lock, LockfilePlan
"""

from __future__ import annotations

from .config.models import AppConfig, export_app_config_schema, load_config, load_config_file
from .graph.build import build_system_graph
from .quickfix import QuickFix, PatchOp, get_quick_fixes
from .quickfix.fixes import fingerprint, list_dependencies, lint
from .registries.aliases import validate_aliases
from .lock import LockfilePlan, plan_lock

__all__ = [
    # config
    "AppConfig",
    "load_config",
    "load_config_file",
    "export_app_config_schema",
    # graph
    "build_system_graph",
    # quickfix
    "get_quick_fixes",
    "QuickFix",
    "PatchOp",
    "fingerprint",
    "list_dependencies",
    "lint",
    "validate_aliases",
    # lock
    "LockfilePlan",
    "plan_lock",
]
