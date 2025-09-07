from pathlib import Path

from agent_compose_kit.config.models import (
    AppConfig,
    McpRegistryConfig,
    McpRegistryServer,
    OpenApiApiConfig,
    OpenApiRegistryConfig,
    RegistryGroup,
)
from agent_compose_kit.tools.builders import (
    build_mcp_registry_from_config,
    build_openapi_registry_from_config,
    build_tool_registry_from_config,
)
from agent_compose_kit.tools.mcp_registry import McpRegistry
from agent_compose_kit.tools.openapi_registry import OpenAPIRegistry
from agent_compose_kit.tools.registry import ToolRegistry


def test_tool_registry_listing(tmp_path: Path):
    cfg = AppConfig.model_validate(
        {
            "tools_registry": {
                "tools": [
                    {"id": "t1", "type": "function", "ref": "tests.helpers:sample_tool"},
                    {"id": "t2", "type": "function", "ref": "tests.helpers:sample_tool"},
                ],
                "groups": [{"id": "g1", "include": ["t1", "t2"]}],
            }
        }
    )
    reg: ToolRegistry = build_tool_registry_from_config(cfg, base_dir=tmp_path)
    assert set(reg.list_tool_ids()) == {"t1", "t2"}
    assert reg.list_tool_groups() == ["g1"]
    # error mode
    try:
        reg.get("missing")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_mcp_registry_listing(tmp_path: Path):
    cfg = AppConfig(
        mcp_registry=McpRegistryConfig(
            servers=[McpRegistryServer(id="s1", mode="sse", url="https://example.com")],
            groups=[RegistryGroup(id="g1", include=["s1"])],
        )
    )
    reg: McpRegistry | None = build_mcp_registry_from_config(cfg, base_dir=tmp_path)
    assert reg is not None
    assert reg.list_ids() == ["s1"]
    assert reg.list_groups() == ["g1"]
    try:
        reg.get("missing")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_openapi_registry_listing(tmp_path: Path):
    inline_spec = '{"openapi":"3.0.0","info":{"title":"t","version":"1.0"},"paths":{}}'
    cfg = AppConfig(
        openapi_registry=OpenApiRegistryConfig(
            apis=[OpenApiApiConfig(id="a1", spec={"inline": inline_spec}, spec_type="json")],
            groups=[RegistryGroup(id="g1", include=["a1"])],
        )
    )
    reg: OpenAPIRegistry | None = build_openapi_registry_from_config(cfg, base_dir=tmp_path)
    assert reg is not None
    assert reg.list_ids() == ["a1"]
    assert reg.list_groups() == ["g1"]
    try:
        reg.get("missing")
        assert False, "expected KeyError"
    except KeyError:
        pass

