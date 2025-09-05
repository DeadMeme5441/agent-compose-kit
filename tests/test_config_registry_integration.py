from pathlib import Path

import yaml
import pytest

from src.config.models import AppConfig, load_config_file
from src.tools.builders import build_tool_registry_from_config
from src.agents.builders_registry import build_agent_registry_from_config


def test_build_registries_from_appconfig(tmp_path: Path):
    cfg_data = {
        "tools_registry": {
            "tools": [
                {"id": "util.add", "type": "function", "ref": "tests.helpers:sample_tool", "name": "add"}
            ]
        },
        "agents_registry": {
            "agents": [
                {
                    "id": "calc",
                    "name": "calculator",
                    "model": "gemini-2.0-flash",
                    "tools": [{"use": "registry:util.add"}],
                }
            ]
        },
    }
    p = tmp_path / "app.yaml"
    p.write_text(yaml.safe_dump(cfg_data, sort_keys=False))
    cfg = load_config_file(p)
    tools = build_tool_registry_from_config(cfg, base_dir=tmp_path)
    try:
        agents = build_agent_registry_from_config(cfg, base_dir=tmp_path, provider_defaults=cfg.model_providers, tool_registry=tools)
    except ImportError:
        pytest.skip("google-adk not installed")
    a = agents.get("calc")
    assert getattr(a, "name", None) == "calculator"
    tools_list = getattr(a, "tools", [])
    assert any(getattr(t, "name", None) == "add" for t in tools_list)

