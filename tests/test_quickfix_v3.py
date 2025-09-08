from agent_compose_kit.quickfix import get_quick_fixes


def test_quickfix_llm_missing_model_uses_defaults_alias():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "defaults": {"model_alias": "chat-default"},
        "agents": [
            {"type": "llm", "name": "a", "instruction": "i"},
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    assert any(f.title.startswith("Set model") and f.ops for f in fixes)


def test_quickfix_unknown_subagent_recommends_closest():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "agents": [
            {"type": "llm", "name": "alpha", "instruction": "i"},
            {"type": "workflow.sequential", "name": "seq", "sub_agents": ["alfa"]},
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    assert any("Replace 'alfa'" in f.title for f in fixes)


def test_quickfix_move_thinking_config_to_planner():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "agents": [
            {
                "type": "llm",
                "name": "a",
                "instruction": "i",
                "generate_content_config": {"thinking_config": {"effort": "MEDIUM"}},
            }
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    assert any(f.id.startswith("move-thinking") for f in fixes)


def test_quickfix_sequential_missing_output_key():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "agents": [
            {"type": "llm", "name": "a", "instruction": "i"},
            {"type": "llm", "name": "b", "instruction": "i"},
            {"type": "workflow.sequential", "name": "seq", "sub_agents": ["a", "b"]},
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    assert any("Add output_key" in f.title for f in fixes)


def test_quickfix_add_defaults_when_missing_model_and_no_defaults():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "agents": [
            {"type": "llm", "name": "a", "instruction": "i"},
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    assert any(f.id == "add-defaults-model-alias" for f in fixes)

