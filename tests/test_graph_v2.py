from agent_compose_kit.config.models import load_config
from agent_compose_kit.graph.build import build_system_graph


def _ids(items):
    return {i["id"] for i in items}


def test_llm_with_tool_and_sub_agent_edges():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "defaults": {"model_alias": "chat-default"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i", "tools": [{"kind": "function", "function": {"import": "p:m"}}]},
                {"type": "llm", "name": "b", "instruction": "i", "sub_agents": ["a"]},
            ],
        }
    )
    g = build_system_graph(cfg)
    node_ids = _ids(g["nodes"])  # type: ignore[index]
    assert "agent:a" in node_ids and "agent:b" in node_ids
    assert any(e for e in g["edges"] if e["type"] == "sub" and e["source"] == "agent:b" and e["target"] == "agent:a")
    assert any(n for n in g["nodes"] if n["type"] == "tool.function")


def test_sequential_parallel_loop_edges_and_hints():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i"},
                {"type": "llm", "name": "b", "instruction": "i"},
                {"type": "workflow.sequential", "name": "seq", "sub_agents": ["a", "b"]},
                {"type": "workflow.parallel", "name": "par", "sub_agents": ["a", "b"]},
                {"type": "workflow.loop", "name": "loop", "sub_agents": ["a"], "max_iterations": 2},
            ],
        }
    )
    g = build_system_graph(cfg)
    # sequential: edge a -> b
    assert any(e for e in g["edges"] if e["type"] == "flow" and e["source"] == "agent:a" and e["target"] == "agent:b")
    # parallel: par -> a and par -> b
    assert any(e for e in g["edges"] if e["type"] == "flow" and e["source"] == "agent:par" and e["target"] == "agent:a")
    assert any(e for e in g["edges"] if e["type"] == "flow" and e["source"] == "agent:par" and e["target"] == "agent:b")
    # loop: loop -> a
    assert any(e for e in g["edges"] if e["type"] == "flow" and e["source"] == "agent:loop" and e["target"] == "agent:a")


def test_custom_agent_declared_sub_agents_are_visualized():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i"},
                {"type": "custom", "name": "c", "class": "pkg.mod:Class", "params": {}, "sub_agents": ["a"]},
            ],
        }
    )
    g = build_system_graph(cfg)
    assert any(e for e in g["edges"] if e["type"] == "sub" and e["source"] == "agent:c" and e["target"] == "agent:a")


def test_hints_missing_model_and_unknown_subagent():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {"type": "llm", "name": "x", "instruction": "i", "sub_agents": ["nope"]},
            ],
        }
    )
    g = build_system_graph(cfg)
    assert any("no model" in h for h in g["hints"])  # missing model and no defaults
    assert any("unknown sub_agent" in h for h in g["hints"])  # unresolved
