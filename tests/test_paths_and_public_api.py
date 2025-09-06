import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.api.public import event_to_minimal_json
from agent_compose_kit.paths import (
    get_outputs_root,
    get_sessions_uri,
    get_systems_root,
    resolve_outputs_dir,
    resolve_system_dir,
)


def test_paths_defaults_and_resolvers(tmp_path: Path, monkeypatch):
    # Defaults
    assert get_sessions_uri().startswith("sqlite")

    # With env overrides
    monkeypatch.setenv("AGENT_SYS_DIR", str(tmp_path / "systems"))
    monkeypatch.setenv("AGENT_OUTPUTS_DIR", str(tmp_path / "outputs"))
    sys_root = get_systems_root()
    out_root = get_outputs_root()
    assert sys_root.name == "systems"
    assert out_root.name == "outputs"

    d = resolve_system_dir("demo")
    assert d.as_posix().endswith("systems/demo")
    od = resolve_outputs_dir("demo", session_id="s1")
    assert od.as_posix().endswith("outputs/demo/s1")


class _Part:
    def __init__(self, text=None, function_call=None, function_response=None):
        self.text = text
        self.function_call = function_call
        self.function_response = function_response


class _Content:
    def __init__(self, parts):
        self.parts = parts


class _Event:
    def __init__(self):
        self.id = "e1"
        self.author = "assistant"
        self.partial = False
        self.timestamp = 123
        self.content = _Content(parts=[_Part(text="hi")])


def test_event_to_minimal_json_serialization():
    e = _Event()
    out = event_to_minimal_json(e)
    assert out["id"] == "e1"
    assert out["author"] == "assistant"
    assert out["content"]["parts"][0]["text"] == "hi"


@pytest.mark.skipif(
    importlib.util.find_spec("google.adk") is None,
    reason="google-adk not installed",
)
def test_system_manager_root_naming_with_workflow(tmp_path: Path):
    # Only run when google-adk is present; otherwise skip to avoid heavy deps
    from agent_compose_kit.config.models import AgentConfig, AppConfig, WorkflowConfig
    from agent_compose_kit.runtime.supervisor import build_runner_from_yaml

    cfg = AppConfig(
        agents=[
            AgentConfig(name="a", model="gemini-2.0-flash"),
            AgentConfig(name="b", model="gemini-2.0-flash"),
        ],
        workflow=WorkflowConfig(type="sequential", nodes=["a", "b"]),
    )
    import yaml

    p = tmp_path / "app.yaml"
    p.write_text(yaml.safe_dump(cfg.model_dump(), sort_keys=False))
    runner, _session = build_runner_from_yaml(config_path=p, user_id="u")
    assert getattr(runner.agent, "name", None) == "root_agent"
