import pytest

from agent_compose_kit.config.models import AgentConfig
from agent_compose_kit.agents.builder import build_agents


def test_sub_agents_wiring(monkeypatch):
    cfgs = [
        AgentConfig(name="parent", model="gemini-2.0-flash", sub_agents=["child1", "child2"]),
        AgentConfig(name="child1", model="gemini-2.0-flash"),
        AgentConfig(name="child2", model="gemini-2.0-flash"),
    ]
    try:
        agents = build_agents(cfgs, provider_defaults={})
    except ImportError:
        pytest.skip("google-adk not installed")
    parent = agents["parent"]
    subs = getattr(parent, "sub_agents", [])
    assert len(subs) == 2
    assert {getattr(a, "name", None) for a in subs} == {"child1", "child2"}


def test_litellm_provider_defaults_merge():
    cfgs = [
        AgentConfig(
            name="llm",
            model={"type": "litellm", "model": "openai/gpt-4o-mini"},
        )
    ]
    provider_defaults = {"openai": {"api_base": "http://localhost:11434/v1", "api_key": "x"}}
    try:
        agents = build_agents(cfgs, provider_defaults=provider_defaults)
    except ImportError:
        pytest.skip("google-adk not installed or LiteLLM wrapper missing")
    agent = agents["llm"]
    model_obj = getattr(agent, "model", None)
    # We can only sanity check presence of attributes; specifics are ADK internals
    # Ensure it is not a plain string and likely a LiteLlm instance
    assert not isinstance(model_obj, str)
    # Attributes may or may not be public; check repr contains hints
    assert "openai" in repr(model_obj).lower() or "lite" in repr(model_obj).lower()
