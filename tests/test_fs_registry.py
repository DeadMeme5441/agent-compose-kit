from pathlib import Path

from src.config.models import AppConfig, AgentConfig
from src.registry.fs import save_system, list_systems, list_versions, load_system, promote


def test_fs_registry_save_load_promote(tmp_path: Path):
    cfg = AppConfig(agents=[AgentConfig(name="a", model="gemini-2.0-flash")])
    cfg_path = save_system(cfg, name="demo", version="v1", root=tmp_path)
    assert cfg_path.exists()

    systems = list_systems(root=tmp_path)
    assert systems == ["demo"]
    versions = list_versions("demo", root=tmp_path)
    assert versions == ["v1"]

    loaded = load_system("demo", "v1", root=tmp_path)
    assert loaded.agents[0].name == "a"

    promoted = promote("demo", "v1", "latest", root=tmp_path)
    assert promoted.exists()

