import pytest

from agent_compose_kit.config.models import load_config


def test_schema_version_semver_and_duplicate_names():
    with pytest.raises(ValueError):
        load_config({"schema_version": "0.1", "metadata": {"name": "x"}, "agents": []})

    # duplicate agent names
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "x"},
                "agents": [
                    {"type": "llm", "name": "a", "instruction": "i"},
                    {"type": "llm", "name": "a", "instruction": "i2"},
                ],
            }
        )


def test_kind_mismatch_in_tools_is_rejected():
    # wrong kind for MCP server
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "p",
                        "instruction": "use tools",
                        "tools": [
                            {"kind": "mcp", "server": {"ref": {"value": "registry://openapi/x@1"}}, "tool": "t"}
                        ],
                    }
                ],
            }
        )

    # wrong kind for openapi spec
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "p",
                        "instruction": "use tools",
                        "tools": [
                            {"kind": "openapi", "spec": {"ref": {"value": "registry://mcp/x@1"}}, "operationId": "op"}
                        ],
                    }
                ],
            }
        )

    # wrong kind for function ref
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "p",
                        "instruction": "use tools",
                        "tools": [
                            {"kind": "function", "function": {"ref": {"value": "registry://agent/x@1"}}}
                        ],
                    }
                ],
            }
        )

    # wrong kind for agent tool
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "p",
                        "instruction": "use tools",
                        "tools": [
                            {"kind": "agent", "agent": {"value": "registry://function/x@1"}}
                        ],
                    }
                ],
            }
        )

