from textwrap import dedent

from agent_compose_kit.config.models import load_config


def test_registries_ref_or_inline_and_tool_refs_validate():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "registries": {
                "mcp": [
                    {"inline": {"id": "files", "mode": "sse", "url": "http://localhost:3000/sse"}}
                ],
                "openapi": [
                    {
                        "inline": {
                            "id": "petstore",
                            "spec": {"inline": "{}"},
                            "spec_type": "json",
                        }
                    }
                ],
                "agents": [{"inline": {"id": "helper", "type": "llm", "name": "helper", "instruction": "help"}}],
                "functions": [{"inline": {"id": "add", "import": "pkg.mod:fn"}}],
            },
            "agents": [
                {
                    "type": "llm",
                    "name": "planner",
                    "instruction": "use tools",
                    "tools": [
                        {"kind": "mcp", "server": {"ref": {"value": "registry://mcp/files@latest"}}, "tool": "read_file"},
                        {"kind": "openapi", "spec": {"ref": {"value": "registry://openapi/petstore@1.0.0"}}, "operationId": "listPets"},
                        {"kind": "function", "function": {"ref": {"value": "registry://function/add@latest"}}},
                        {"kind": "agent", "agent": {"value": "registry://agent/helper@latest"}},
                    ],
                }
            ],
        }
    )

    assert cfg.metadata.name == "demo"
    assert cfg.agents[0].type == "llm"  # type: ignore[attr-defined]

