from agent_compose_kit.config.models import load_config
from agent_compose_kit.graph.build import build_system_graph


def test_llm_agent_extended_fields_parse():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "include_contents": "none",
                    "output_key": "draft",
                    "input_schema": "pkg.mod:Input",
                    "output_schema": "pkg.mod:Output",
                    "disallow_transfer_to_parent": True,
                    "disallow_transfer_to_peers": False,
                    "generate_content_config": {"temperature": 0.2},
                    # planner optional: provide plan_react by default
                    "planner": {"type": "plan_react"},
                    "code_executor": "pkg.exec:Exec",
                    "before_model_callbacks": ["pkg.cb:before"],
                    "after_model_callbacks": ["pkg.cb:after"],
                    "before_tool_callbacks": ["pkg.cb:bt"],
                    "after_tool_callbacks": ["pkg.cb:at"],
                    "global_instruction": "be nice",
                }
            ],
        }
    )
    a = cfg.agents[0]
    assert getattr(a, "output_key") == "draft"  # type: ignore[attr-defined]
    assert getattr(a, "include_contents") == "none"  # type: ignore[attr-defined]


def test_hints_output_schema_disables_tools_and_missing_output_key_in_seq():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i", "tools": [{"kind": "function", "function": {"import": "p:m"}}], "output_schema": "pkg.mod:Out"},
                {"type": "llm", "name": "b", "instruction": "i"},  # no output_key
                {"type": "workflow.sequential", "name": "seq", "sub_agents": ["b", "a"]},
            ],
        }
    )
    g = build_system_graph(cfg)
    assert any("output_schema" in h for h in g["hints"])  # type: ignore[index]
    assert any("no output_key" in h for h in g["hints"])  # type: ignore[index]
