from agent_compose_kit.config.models import load_config
from agent_compose_kit.graph.build import build_system_graph
import pytest


def test_planner_built_in_requires_thinking_config_and_sets_meta():
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {"type": "llm", "name": "a", "instruction": "i", "planner": {"type": "built_in", "thinking_config": {}}},
                ],
            }
        )

    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "planner": {"type": "built_in", "thinking_config": {"effort": "MEDIUM"}},
                    "generate_content_config": {"thinking_config": {"foo": 1}},
                }
            ],
        }
    )
    g = build_system_graph(cfg)
    n = next(n for n in g["nodes"] if n["id"] == "agent:a")
    assert n["meta"].get("planner") == "built_in"
    assert any("thinking_config" in h for h in g["hints"])  # hint to move thinking_config to planner


def test_planner_plan_react_hints_when_output_schema_present():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "planner": {"type": "plan_react"},
                    "output_schema": "pkg.mod:Out",
                }
            ],
        }
    )
    g = build_system_graph(cfg)
    assert any("plan_react" in h and "output_schema" in h for h in g["hints"])  # type: ignore[index]

