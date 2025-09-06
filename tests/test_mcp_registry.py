import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.config.models import (
    AppConfig,
    McpRegistryConfig,
    McpRegistryServer,
    RegistryGroup,
)
from agent_compose_kit.tools.loader import load_tool_list
from agent_compose_kit.tools.mcp_registry import McpRegistry


def _has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


@pytest.mark.skipif(
    not _has("google.adk.tools.mcp_tool.mcp_toolset"),
    reason="MCP toolset not available",
)
def test_mcp_registry_build_and_group(tmp_path: Path):
    cfg = AppConfig(
        mcp_registry=McpRegistryConfig(
            servers=[McpRegistryServer(id="s1", mode="sse", url="https://example.com/mcp")],
            groups=[RegistryGroup(id="g1", include=["s1"])],
        )
    )
    reg = McpRegistry(cfg.mcp_registry.model_dump(), base_dir=tmp_path)
    t = reg.get("s1")
    name = type(t).__name__
    assert "Mcp" in name or "MCP" in name
    group = reg.get_group("g1")
    assert len(group) == 1


@pytest.mark.skipif(
    not _has("google.adk.tools.mcp_tool.mcp_toolset"),
    reason="MCP toolset not available",
)
def test_loader_resolves_mcp_use(tmp_path: Path):
    cfg = AppConfig(
        mcp_registry=McpRegistryConfig(
            servers=[McpRegistryServer(id="s1", mode="sse", url="https://example.com/mcp")],
            groups=[RegistryGroup(id="g1", include=["s1"])],
        )
    )
    reg = McpRegistry(cfg.mcp_registry.model_dump(), base_dir=tmp_path)
    tools = load_tool_list([{"use": "mcp:s1"}, {"use": "mcp_group:g1"}], base_dir=tmp_path, mcp_registry=reg)
    assert len(tools) == 2
    assert any("Mcp" in type(t).__name__ or "MCP" in type(t).__name__ for t in tools)

