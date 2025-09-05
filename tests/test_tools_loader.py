import importlib.util
from pathlib import Path

import pytest

from agent_compose_kit.tools.loader import load_tool_entry, load_tool_list, load_toolsets_map


def _has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def test_function_tool_loading_from_loader(tmp_path: Path):
    entry = {"type": "function", "ref": "tests.helpers:sample_tool", "name": "adder"}
    tool = load_tool_entry(entry, base_dir=tmp_path)
    # google.adk.tools.FunctionTool type; we can only assert attributes
    assert getattr(tool, "name", None) == "adder"


def test_toolsets_map_and_use_reference(tmp_path: Path):
    # Define shared toolset as a function tool
    cfg_toolsets = {
        "adder": {"type": "function", "ref": "tests.helpers:sample_tool", "name": "add"}
    }
    m = load_toolsets_map(cfg_toolsets, base_dir=tmp_path)
    tools = load_tool_list([{"use": "adder"}], base_dir=tmp_path, toolsets_map=m)
    assert len(tools) == 1
    assert getattr(tools[0], "name", None) == "add"


def test_mcp_stdio_loader_constructs_when_available(tmp_path: Path):
    if not _has("google.adk.tools.mcp_tool.mcp_toolset"):
        pytest.skip("MCP toolset not available")
    # mcp stdio requires 'mcp' package for StdioServerParameters; skip if missing
    if not _has("mcp"):
        pytest.skip("mcp package not installed")
    entry = {
        "type": "mcp",
        "mode": "stdio",
        "command": "echo",
        "args": ["hello"],
        "tool_filter": [],
    }
    toolset = load_tool_entry(entry, base_dir=tmp_path)
    # Type repr should mention MCP or Toolset
    assert "Mcp" in type(toolset).__name__ or "MCP" in type(toolset).__name__


def test_openapi_loader_with_inline_spec(tmp_path: Path):
    if not _has("google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset"):
        pytest.skip("OpenAPI toolset not available")
    inline_spec = '{"openapi":"3.0.0","info":{"title":"t","version":"1.0"},"paths":{}}'
    entry = {
        "type": "openapi",
        "spec": {"inline": inline_spec},
        "spec_type": "json",
        "tool_filter": [],
    }
    toolset = load_tool_entry(entry, base_dir=tmp_path)
    assert "OpenAPIToolset" in type(toolset).__name__


def test_openapi_loader_with_path_spec(tmp_path: Path):
    if not _has("google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset"):
        pytest.skip("OpenAPI toolset not available")
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text("openapi: '3.0.0'\ninfo: {title: t, version: '1.0'}\npaths: {}\n")
    entry = {
        "type": "openapi",
        "spec": {"path": str(spec_path)},
        # spec_type can be omitted; inferred from extension
    }
    toolset = load_tool_entry(entry, base_dir=tmp_path)
    assert "OpenAPIToolset" in type(toolset).__name__
