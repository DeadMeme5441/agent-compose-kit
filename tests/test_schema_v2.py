from textwrap import dedent

import pytest

from agent_compose_kit.config.models import (
    AppConfig,
    export_app_config_schema,
    load_config,
)


def test_llm_agent_minimal_parses():
    yaml_txt = dedent(
        """
        schema_version: 0.1.0
        metadata: { name: demo }
        agents:
          - type: llm
            name: planner
            instruction: You plan.
        """
    )
    cfg = load_config(yaml_txt)
    assert isinstance(cfg, AppConfig)
    assert cfg.agents[0].type == "llm"  # type: ignore[attr-defined]


def test_workflow_agents_parse_and_require_fields():
    # sequential requires sub_agents
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {"type": "workflow.sequential", "name": "seq"},
                ],
            }
        )

    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i"},
                {"type": "workflow.sequential", "name": "seq", "sub_agents": ["a"]},
            ],
        }
    )
    assert cfg.agents[1].type == "workflow.sequential"  # type: ignore[attr-defined]


def test_loop_and_custom_agents_validation():
    # loop must have non-empty until
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "workflow.loop",
                        "name": "looper",
                        "body": "a",
                        "until": " ",
                    }
                ],
            }
        )

    # custom agent must include class
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {"type": "custom", "name": "x"},
                ],
            }
        )

    # happy path
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i"},
                {
                    "type": "workflow.loop",
                    "name": "looper",
                    "body": "a",
                    "until": "iteration >= 3",
                    "max_iters": 5,
                },
                {"type": "custom", "name": "c", "class": "pkg.mod:Class", "params": {}},
            ],
        }
    )
    assert cfg.agents[1].type == "workflow.loop"  # type: ignore[attr-defined]


def test_json_schema_contains_variants_defs():
    schema = export_app_config_schema()
    # The union of agent variants should be present in the schema
    s = str(schema)
    assert "workflow.sequential" in s
    assert "workflow.parallel" in s
    assert "workflow.loop" in s
    assert "llm" in s


def test_llm_tools_variants_schema_and_parse():
    # Ensure schema mentions tool kinds and a config with tools parses
    schema = export_app_config_schema()
    s = str(schema)
    assert "function" in s and "openapi" in s and "mcp" in s and "agent" in s

    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "planner",
                    "instruction": "Use tools",
                    "tools": [
                        {"kind": "function", "function": {"import": "pkg.mod:fn"}},
                        {
                            "kind": "mcp",
                            "server": {"ref": {"value": "registry://mcp/files@latest"}},
                            "tool": "read_file",
                        },
                        {"kind": "agent", "agent": "helper"},
                    ],
                }
            ],
        }
    )
    assert cfg.agents[0].type == "llm"  # type: ignore[attr-defined]
