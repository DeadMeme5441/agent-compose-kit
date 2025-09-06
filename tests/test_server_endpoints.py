from pathlib import Path

import pytest


def _has_fastapi() -> bool:
    try:
        import fastapi  # noqa: F401
        from fastapi.testclient import TestClient  # noqa: F401
        return True
    except Exception:
        return False


def _has_adk() -> bool:
    try:
        import google.adk  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_fastapi(), reason="fastapi not installed")
def test_server_validate_and_start_run(tmp_path: Path):
    if not _has_adk():
        pytest.skip("google-adk not installed")
    # Build a minimal config file
    cfg = tmp_path / "app.yaml"
    cfg.write_text("agents: [{name: a, model: gemini-2.0-flash}]\n", encoding="utf-8")

    from fastapi.testclient import TestClient

    from agent_compose_kit.server.app import get_app

    app = get_app()
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True

    r = client.post("/validate", params={"config_path": str(cfg)})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True and "plan" in data

    r = client.post(
        "/runs",
        params={"config_path": str(cfg), "user_id": "u", "text": "hello"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "run_id" in data and "session_id" in data
