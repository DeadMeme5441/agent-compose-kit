from pathlib import Path

import pytest


def _has_fastapi() -> bool:
    try:
        import fastapi  # noqa: F401
        from fastapi.testclient import TestClient  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_fastapi(), reason="fastapi not installed")
def test_server_lint_and_schema(tmp_path: Path):
    # Minimal config
    cfg = tmp_path / "app.yaml"
    cfg.write_text("agents: [{name: a, model: gemini-2.0-flash}]\n", encoding="utf-8")

    from fastapi.testclient import TestClient
    from agent_compose_kit.server.app import get_app

    app = get_app()
    client = TestClient(app)

    r = client.get("/schema")
    assert r.status_code == 200
    assert isinstance(r.json(), dict) and "properties" in r.json()

    r = client.post("/lint", params={"config_path": str(cfg)})
    assert r.status_code == 200
    data = r.json()
    assert "diagnostics" in data and isinstance(data["diagnostics"], list)
    assert isinstance(data.get("config"), dict)
