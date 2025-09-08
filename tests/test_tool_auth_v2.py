import pytest

from agent_compose_kit.config.models import load_config


def test_openapi_tool_auth_optional_and_validates():
    # Missing auth_config is allowed (runtime may skip auth)
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "tools": [
                        {
                            "kind": "openapi",
                            "spec": {"inline": {"spec": {"inline": "{}"}, "spec_type": "json"}},
                            "operationId": "op",
                        }
                    ],
                }
            ],
        }
    )
    assert cfg.metadata.name == "demo"

    # auth_config present but missing auth_scheme should fail fast
    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "a",
                        "instruction": "i",
                        "tools": [
                            {
                                "kind": "openapi",
                                "spec": {"inline": {"spec": {"inline": "{}"}, "spec_type": "json"}},
                                "operationId": "op",
                                "auth_config": {"params": {"token": "abc"}},
                            }
                        ],
                    }
                ],
            }
        )

    # Valid auth_config
    cfg2 = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "tools": [
                        {
                            "kind": "openapi",
                            "spec": {"inline": {"spec": {"inline": "{}"}, "spec_type": "json"}},
                            "operationId": "op",
                            "auth_config": {"auth_scheme": "bearer", "params": {"token": "abc"}},
                        }
                    ],
                }
            ],
        }
    )
    assert cfg2.metadata.name == "demo"


def test_mcp_tool_auth_optional_and_validates():
    # Missing auth_config is allowed (runtime may skip auth)
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "tools": [
                        {
                            "kind": "mcp",
                            "server": {"inline": {"id": "files", "mode": "sse", "url": "http://localhost/sse"}},
                            "tool": "read_file",
                        }
                    ],
                }
            ],
        }
    )
    assert cfg.metadata.name == "demo"

    # auth_config present but missing auth_scheme should fail fast
    import pytest

    with pytest.raises(ValueError):
        load_config(
            {
                "schema_version": "0.1.0",
                "metadata": {"name": "demo"},
                "agents": [
                    {
                        "type": "llm",
                        "name": "a",
                        "instruction": "i",
                        "tools": [
                            {
                                "kind": "mcp",
                                "server": {"inline": {"id": "files", "mode": "sse", "url": "http://localhost/sse"}},
                                "tool": "read_file",
                                "auth_config": {"params": {"token": "abc"}},
                            }
                        ],
                    }
                ],
            }
        )

    # Valid auth_config
    cfg2 = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "tools": [
                        {
                            "kind": "mcp",
                            "server": {"inline": {"id": "files", "mode": "sse", "url": "http://localhost/sse"}},
                            "tool": "read_file",
                            "auth_config": {"auth_scheme": "bearer", "params": {"token": "abc"}},
                        }
                    ],
                }
            ],
        }
    )
    assert cfg2.metadata.name == "demo"
