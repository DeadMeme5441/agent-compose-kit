from pathlib import Path

from agent_compose_kit.config.models import load_config_file, AppConfig, write_example_config


def test_services_back_compat(tmp_path: Path):
    content = {
        "services": {
            "session_service": {"type": "in_memory"},
            "artifact_service": {"type": "in_memory"},
            "memory_service": {"type": "in_memory"},
        },
        "agents": [{"name": "a", "model": "gemini-2.0-flash"}],
    }
    import yaml

    p = tmp_path / "app.yaml"
    p.write_text(yaml.safe_dump(content, sort_keys=False))
    cfg: AppConfig = load_config_file(p)
    assert cfg.session_service.type == "in_memory"
    assert cfg.artifact_service.type == "in_memory"
    assert cfg.memory_service is not None
    assert cfg.memory_service.type == "in_memory"


def test_write_example_config(tmp_path: Path):
    p = tmp_path / "example.yaml"
    write_example_config(p)
    data = p.read_text()
    assert "session_service" in data and "artifact_service" in data and "agents:" in data
