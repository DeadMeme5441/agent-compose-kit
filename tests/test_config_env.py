import os
from pathlib import Path

from src.config.models import load_config_file, AppConfig


def test_env_interpolation_and_services(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    content = """
services:
  session_service: {type: in_memory}
  artifact_service: {type: local_folder, base_path: ./artifacts}
model_providers:
  openai: {api_key: ${OPENAI_API_KEY}}
agents:
  - name: a
    model: {type: litellm, model: openai/gpt-4o-mini}
""".strip()
    cfg_path = tmp_path / "app.yaml"
    cfg_path.write_text(content)

    cfg: AppConfig = load_config_file(cfg_path)
    assert cfg.session_service.type == "in_memory"
    assert cfg.artifact_service.type == "local_folder"
    assert cfg.model_providers["openai"]["api_key"] == "sk-test"

