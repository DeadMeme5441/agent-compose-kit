from pathlib import Path

from click.testing import CliRunner

from src.cli import app


def test_cli_init_validate_plan_and_graph(tmp_path: Path, monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # init
        r = runner.invoke(app, ["init"])  # writes configs/app.yaml
        assert r.exit_code == 0
        cfg_path = Path("configs/app.yaml")
        assert cfg_path.exists()

        # validate
        r = runner.invoke(app, ["validate", str(cfg_path)])
        assert r.exit_code == 0
        assert "Config OK" in r.output

        # plan
        r = runner.invoke(app, ["plan", str(cfg_path)])
        assert r.exit_code == 0
        assert "Plan:" in r.output

        # graph (ASCII)
        r = runner.invoke(app, ["graph", str(cfg_path)])
        assert r.exit_code == 0

