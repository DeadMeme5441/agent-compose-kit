from click.testing import CliRunner
from src.cli import app


def test_cli_help():
    runner = CliRunner()
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "Template Agent Builder CLI" in r.output
