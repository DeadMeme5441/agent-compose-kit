from pathlib import Path

import pytest

from agent_compose_kit.tools.registry import ToolRegistry
from agent_compose_kit.agents.registry import AgentRegistry


def test_tool_registry_get_and_group(tmp_path: Path):
    specs = {
        "tools": [
            {"id": "util.add", "type": "function", "ref": "tests.helpers:sample_tool", "name": "add"}
        ],
        "groups": [{"id": "essentials", "include": ["util.add", "util.add"]}],
    }
    reg = ToolRegistry(specs, base_dir=tmp_path)
    t1 = reg.get("util.add")
    t2 = reg.get("util.add")
    assert t1 is t2  # cached
    group = reg.get_group("essentials")
    assert len(group) == 1  # de-dup
    assert getattr(group[0], "name", None) == "add"


def test_agent_registry_with_tool_registry(tmp_path: Path):
    tool_specs = {
        "tools": [
            {"id": "util.add", "type": "function", "ref": "tests.helpers:sample_tool", "name": "add"}
        ]
    }
    tools = ToolRegistry(tool_specs, base_dir=tmp_path)
    agent_specs = {
        "agents": [
            {
                "id": "calc",
                "name": "calculator",
                "model": "gemini-2.0-flash",
                "instruction": "Use add tool.",
                "tools": [{"use": "registry:util.add"}],
            },
            {
                "id": "parent",
                "model": "gemini-2.0-flash",
                "sub_agents": ["calc"],
            },
        ],
        "groups": [{"id": "team", "include": ["calc", "parent"]}],
    }
    try:
        reg = AgentRegistry(agent_specs, base_dir=tmp_path, provider_defaults={}, tool_registry=tools)
    except ImportError:
        pytest.skip("google-adk not installed")
    a = reg.get("calc")
    tool_names = [getattr(t, "name", None) for t in getattr(a, "tools", [])]
    assert "add" in tool_names
    p = reg.get("parent")
    subs = getattr(p, "sub_agents", [])
    assert len(subs) == 1 and getattr(subs[0], "name", None) == "calculator"
    team = reg.get_group("team")
    assert len(team) == 2
