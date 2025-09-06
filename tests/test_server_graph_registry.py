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
def test_server_graph_agents_registry(tmp_path: Path):
    cfg = tmp_path / "app.yaml"
    cfg.write_text(
        "\n".join(
            [
                "agents_registry:",
                "  agents:",
                "    - {id: calc, name: calculator, model: gemini-2.0-flash}",
                "    - {id: helper, name: helper, model: gemini-2.0-flash}",
                "  groups:",
                "    - {id: core, include: [calc, helper]}",
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
    # registry agent nodes present
    assert any(n.get("id") == "registry:agent:calc" for n in data.get("nodes", []))
    assert any(n.get("id") == "registry:agent:helper" for n in data.get("nodes", []))
    # group membership edges
    assert any(e.get("source") == "registry:group:core" and e.get("target") == "registry:agent:calc" for e in data.get("edges", []))
    assert any(e.get("source") == "registry:group:core" and e.get("target") == "registry:agent:helper" for e in data.get("edges", []))

