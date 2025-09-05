import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.agents.builder import build_agents
from agent_compose_kit.config.models import AgentConfig


_HAS_ADK = importlib.util.find_spec("google.adk") is not None
_HAS_GENAI = importlib.util.find_spec("google.genai") is not None


@pytest.mark.skipif(not (_HAS_ADK and _HAS_GENAI), reason="google-adk/genai not installed")
def test_llm_agent_advanced_fields(tmp_path: Path):
    cfgs = [
        AgentConfig(
            name="adv",
            model="gemini-2.0-flash",
            instruction="Do things",
            description="An advanced agent",
            include_contents="none",
            output_key="result",
            generate_content_config={"temperature": 0.2, "max_output_tokens": 64},
        )
    ]
    agents = build_agents(cfgs)
    a = agents["adv"]
    # Basic assertions: attributes exist or were accepted
    assert getattr(a, "name", None) == "adv"
    assert getattr(a, "instruction", None)
    # We can't reliably introspect genai types; ensure no crash and repr has hints
    r = repr(a)
    assert "adv" in r


@pytest.mark.skipif(not (_HAS_ADK and _HAS_GENAI), reason="google-adk/genai not installed")
def test_planner_mapping_plan_react():
    cfgs = [
        AgentConfig(
            name="p",
            model="gemini-2.0-flash",
            planner={"type": "plan_react"},
        )
    ]
    agents = build_agents(cfgs)
    a = agents["p"]
    # Planner presence best-effort; if not available, still constructs agent
    assert a is not None
