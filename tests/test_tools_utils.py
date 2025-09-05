from pathlib import Path

from agent_compose_kit.agents import tools as util
from agent_compose_kit.config.models import AppConfig, AgentConfig


def test_list_read_search(tmp_path: Path):
    a = tmp_path / "a.txt"
    a.write_text("hello world\n")
    b = tmp_path / "b.md"
    b.write_text("greetings Earth\n")

    files = util.list_paths("**/*", base_dir=str(tmp_path))
    assert set(files) == {"a.txt", "b.md"}

    txt = util.read_text(str(a))
    assert "hello" in txt

    hits = util.search_text("greetings", base_dir=str(tmp_path))
    assert any("b.md" in h for h in hits)


def test_validate_plan_graph(tmp_path: Path):
    # Build a simple config file
    cfg = AppConfig(
        agents=[AgentConfig(name="p", model="gemini-2.0-flash")],
        groups=[],
    )
    import yaml

    p = tmp_path / "app.yaml"
    p.write_text(yaml.safe_dump(cfg.model_dump(), sort_keys=False))

    ok = util.validate_flow(str(p))
    assert ok == "Config OK"

    plan = util.plan_flow(str(p))
    assert plan.startswith("Plan:")

    graph = util.graph_flow(str(p))
    assert isinstance(graph, str)

    dot = util.graph_flow(str(p), dot=True)
    assert dot.startswith("digraph flow")
