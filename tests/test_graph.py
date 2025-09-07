from pathlib import Path

from agent_compose_kit.config.models import AppConfig
from agent_compose_kit.graph.build import build_system_graph


def test_graph_sequential_inline(tmp_path: Path):
    cfg = AppConfig.model_validate(
        {
            "agents": [
                {"name": "a", "model": "gemini-2.0-flash"},
                {"name": "b", "model": "gemini-2.0-flash"},
            ],
            "workflow": {"type": "sequential", "nodes": ["a", "b"]},
        }
    )
    g = build_system_graph(cfg)
    assert any(n.get("id") == "a" for n in g["nodes"]) and any(n.get("id") == "b" for n in g["nodes"]) \
        and any(e.get("source") == "a" and e.get("target") == "b" for e in g["edges"])  # noqa: E501


def test_graph_agents_registry(tmp_path: Path):
    cfg = AppConfig.model_validate(
        {
            "agents_registry": {
                "agents": [
                    {"id": "calc", "name": "calculator", "model": "gemini-2.0-flash"},
                    {"id": "helper", "name": "helper", "model": "gemini-2.0-flash"},
                ],
                "groups": [{"id": "core", "include": ["calc", "helper"]}],
            }
        }
    )
    g = build_system_graph(cfg)
    assert any(n.get("id") == "registry:agent:calc" for n in g["nodes"])  # nodes present
    assert any(n.get("id") == "registry:agent:helper" for n in g["nodes"])  # nodes present
    assert any(e.get("source") == "registry:group:core" and e.get("target") == "registry:agent:calc" for e in g["edges"])  # noqa: E501
    assert any(e.get("source") == "registry:group:core" and e.get("target") == "registry:agent:helper" for e in g["edges"])  # noqa: E501

