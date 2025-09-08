from agent_compose_kit.config.models import export_app_config_schema


def test_schema_includes_error_messages_for_core_fields():
    schema = export_app_config_schema()
    s = str(schema)
    # Non-normative keyword but we add it for Monaco UX
    assert "errorMessage" in s
    # Check a couple of specific placements we injected
    assert "schema_version" in s
    assert "Agent name must start" in s

