from pathlib import Path

import pytest

from src.config.models import AppConfig, AgentConfig, WorkflowConfig
from src.runtime.supervisor import build_runner_from_yaml


def write_cfg(tmp_path: Path, cfg: AppConfig) -> Path:
    import yaml

    p = tmp_path / "app.yaml"
    data = cfg.model_dump()
    p.write_text(yaml.safe_dump(data, sort_keys=False))
    return p


def test_sequential_workflow_builds(tmp_path: Path):
    cfg = AppConfig(
        agents=[
            AgentConfig(name="a", model="gemini-2.0-flash"),
            AgentConfig(name="b", model="gemini-2.0-flash"),
        ],
        workflow=WorkflowConfig(type="sequential", nodes=["a", "b"]),
    )
    cfg_path = write_cfg(tmp_path, cfg)
    try:
        runner, session = build_runner_from_yaml(config_path=cfg_path, user_id="u")
    except ImportError:
        pytest.skip("google-adk not installed in environment")
    # Root agent is a sequential agent named 'workflow'
    root = runner.agent
    assert root.name == "workflow"
    assert any(getattr(root, "sub_agents", [])), "expected sub_agents on workflow"

