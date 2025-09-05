from pathlib import Path

from agent_compose_kit.serve.scaffold import (
    write_adk_wrapper,
    write_docker_scaffold,
    write_fastapi_app_py,
)


def test_scaffold_wrapper_and_app(tmp_path: Path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    cfg = tmp_path / "config.yaml"
    cfg.write_text("agents: [{name: a, model: gemini-2.0-flash}]\n", encoding="utf-8")

    sys_dir = write_adk_wrapper(
        agents_dir=agents_dir,
        system_name="demo",
        config_path=cfg,
        package_import="src",
    )
    assert (sys_dir / "agent.py").exists()
    assert (sys_dir / "config.yaml").exists()

    app_py = write_fastapi_app_py(output_dir=tmp_path, agents_dir=agents_dir)
    assert app_py.exists()
    dockerfile = write_docker_scaffold(output_dir=tmp_path, dist_name="agent-compose-kit")
    assert dockerfile.exists()
