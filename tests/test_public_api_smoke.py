import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.api.public import SystemManager
from agent_compose_kit.config.models import AgentConfig, AppConfig


@pytest.mark.skipif(importlib.util.find_spec("google.adk") is None, reason="google-adk not installed")
def test_system_manager_select_root_agent(tmp_path: Path):
    cfg = AppConfig(
        agents=[AgentConfig(name="solo", model="gemini-2.0-flash")],
    )
    sm = SystemManager(base_dir=tmp_path)
    root = sm.select_root_agent(cfg)
    assert getattr(root, "name", None) == "root_agent"

