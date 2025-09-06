import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.config.models import (
    AppConfig,
    OpenApiApiConfig,
    OpenApiRegistryConfig,
    RegistryGroup,
)
from agent_compose_kit.tools.loader import load_tool_list
from agent_compose_kit.tools.openapi_registry import OpenAPIRegistry


def _has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


@pytest.mark.skipif(
    not _has("google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset"),
    reason="OpenAPI toolset not available",
)
def test_openapi_registry_build_and_group(tmp_path: Path):
    inline_spec = '{"openapi":"3.0.0","info":{"title":"t","version":"1.0"},"paths":{}}'
    cfg = AppConfig(
        openapi_registry=OpenApiRegistryConfig(
            apis=[OpenApiApiConfig(id="a1", spec={"inline": inline_spec}, spec_type="json")],
            groups=[RegistryGroup(id="g1", include=["a1"])],
        )
    )
    reg = OpenAPIRegistry(cfg.openapi_registry.model_dump(), base_dir=tmp_path)
    t = reg.get("a1")
    assert "OpenAPIToolset" in type(t).__name__
    group = reg.get_group("g1")
    assert len(group) == 1


@pytest.mark.skipif(
    not _has("google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset"),
    reason="OpenAPI toolset not available",
)
def test_loader_resolves_openapi_use(tmp_path: Path):
    inline_spec = '{"openapi":"3.0.0","info":{"title":"t","version":"1.0"},"paths":{}}'
    cfg = AppConfig(
        openapi_registry=OpenApiRegistryConfig(
            apis=[OpenApiApiConfig(id="a1", spec={"inline": inline_spec}, spec_type="json")],
            groups=[RegistryGroup(id="g1", include=["a1"])],
        )
    )
    reg = OpenAPIRegistry(cfg.openapi_registry.model_dump(), base_dir=tmp_path)
    tools = load_tool_list([{"use": "openapi:a1"}, {"use": "openapi_group:g1"}], base_dir=tmp_path, openapi_registry=reg)
    assert len(tools) == 2
    assert any("OpenAPIToolset" in type(t).__name__ for t in tools)

