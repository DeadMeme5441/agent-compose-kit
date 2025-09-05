import importlib
import pytest

from agent_compose_kit.agents.builder import build_agents
from agent_compose_kit.config.models import AgentConfig


def helper_tool() -> str:  # used by dotted import
    return "ok"


def test_function_tool_loading(monkeypatch):
    # Build agent with a function tool reference to this module
    cfgs = [
        AgentConfig(
            name="a",
            model="gemini-2.0-flash",
            instruction="",
            tools=[{"type": "function", "ref": __name__ + ":helper_tool", "name": "ht"}],
        )
    ]

    try:
        agents = build_agents(cfgs, provider_defaults={})
    except ImportError:
        pytest.skip("google-adk not installed in environment")
    a = agents["a"]
    # google.adk.tools.FunctionTool sets name attribute
    tool_names = [getattr(t, "name", None) for t in getattr(a, "tools", [])]
    assert "ht" in tool_names
