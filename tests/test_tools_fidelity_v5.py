from agent_compose_kit.config.models import load_config
from agent_compose_kit.graph.build import build_system_graph


def test_new_tool_kinds_parse_and_graph_nodes():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "defaults": {"model_alias": "chat-default"},
            "agents": [
                {
                    "type": "llm",
                    "name": "a",
                    "instruction": "i",
                    "tools": [
                        {"kind": "function", "function": {"import": "tests.helpers:sample_tool"}, "long_running": True},
                        {"kind": "mcp_toolset", "server": {"ref": {"value": "registry://mcp/files@latest"}}, "tool_filter": ["read_file"]},
                        {"kind": "openapi_toolset", "spec": {"ref": {"value": "registry://openapi/petstore@1"}}},
                        {"kind": "apihub_toolset", "apihub_resource_name": "projects/p/locations/l/apis/x"},
                        {"kind": "builtin", "name": "vertex_ai_search", "params": {"data_store_id": "projects/p/.../dataStores/ds"}},
                        {"kind": "builtin", "name": "url_context"},
                        {"kind": "openapi", "spec": {"ref": {"value": "registry://openapi/petstore@1"}}, "operationId": "op"},
                        {"kind": "mcp", "server": {"inline": {"id": "files", "mode": "sse", "url": "http://localhost"}}, "tool": "read_file", "auth_config": {"auth_scheme": "bearer", "auth_credential": "x"}},
                    ],
                }
            ],
        }
    )
    g = build_system_graph(cfg)
    types = {n["type"] for n in g["nodes"]}
    assert "tool.mcp_toolset" in types
    assert "tool.openapi_toolset" in types
    assert any(t.startswith("tool.builtin:") for t in types)
