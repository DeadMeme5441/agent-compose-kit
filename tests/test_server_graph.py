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
def test_server_graph_sequential(tmp_path: Path):
    cfg = tmp_path / "app.yaml"
    cfg.write_text(
        "\n".join(
            [
                "agents:",
                "  - {name: a, model: gemini-2.0-flash}",
                "  - {name: b, model: gemini-2.0-flash}",
                "workflow: {type: sequential, nodes: [a, b]}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from fastapi.testclient import TestClient
    from agent_compose_kit.server.app import get_app

    app = get_app()
    client = TestClient(app)

    r = client.post("/graph", params={"config_path": str(cfg)})
    assert r.status_code == 200
    data = r.json()
    assert any(n.get("id") == "a" for n in data.get("nodes", []))
    assert any(n.get("id") == "b" for n in data.get("nodes", []))
    assert any(e.get("source") == "a" and e.get("target") == "b" for e in data.get("edges", []))

