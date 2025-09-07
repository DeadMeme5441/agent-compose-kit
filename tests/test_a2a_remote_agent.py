import importlib.util

import pytest

from agent_compose_kit.agents.builder import build_agents
from agent_compose_kit.config.models import A2AClientConfig, AgentConfig, AppConfig


def _has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


@pytest.mark.skipif(
    not _has("google.adk.agents") or not (_has("google.adk.agents.remote_a2a_agent") or _has("google.adk.agents")),
    reason="A2A remote agent not available",
)
def test_build_a2a_remote_agent():
    cfg = AppConfig(
        a2a_clients=[A2AClientConfig(id="r1", url="https://example.com/a2a", headers={"X": "1"})],
        agents=[AgentConfig(name="remote", kind="a2a_remote", client="r1", model="gemini-2.0-flash")],
    )
    a2a_map = {c.id: c for c in cfg.a2a_clients}
    try:
        agents = build_agents(cfg.agents, provider_defaults=cfg.model_providers, a2a_clients=a2a_map)
    except ImportError:
        pytest.skip("A2A support missing in google-adk")
    a = agents["remote"]
    assert getattr(a, "name", None) == "remote"

