from src.config.models import export_app_config_schema


def test_export_app_config_schema():
    schema = export_app_config_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema and "agents" in schema["properties"]

