from agent_compose_kit.registries.tools import DeclarativeToolRegistry
from agent_compose_kit.registries.agents import DeclarativeAgentRegistry


def test_declarative_tool_registry_get_and_group():
    spec = {
        "tools": [
            {"id": "read_file", "kind": "mcp", "server": {"ref": {"value": "registry://mcp/files@latest"}}, "tool": "read_file"},
            {"id": "sum", "kind": "function", "function": {"import": "tests.helpers:sample_tool"}},
        ],
        "groups": [{"id": "default", "include": ["read_file", "sum"]}],
    }
    reg = DeclarativeToolRegistry(spec)
    t = reg.get("sum")
    assert getattr(t, "kind") == "function"
    grp = reg.get_group("default")
    assert len(grp) == 2


def test_declarative_agent_registry_get_and_group():
    spec = {
        "agents": [
            {"id": "planner", "type": "llm", "name": "planner", "instruction": "plan"},
            {"id": "seq", "type": "workflow.sequential", "name": "seq", "sub_agents": ["planner"]},
        ],
        "groups": [{"id": "core", "include": ["planner", "seq"]}],
    }
    reg = DeclarativeAgentRegistry(spec)
    a = reg.get("planner")
    assert getattr(a, "type") == "llm"
    grp = reg.get_group("core")
    assert len(grp) == 2

