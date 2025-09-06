from pathlib import Path

import pytest

from agent_compose_kit.config.models import (
    A2AClientConfig,
    AgentConfig,
    AppConfig,
    McpRegistryConfig,
    McpRegistryServer,
    OpenApiApiConfig,
    OpenApiRegistryConfig,
    RegistryGroup,
    validate_app_config,
)


def test_agent_kind_requires_client():
    # kind=a2a_remote must provide client
    with pytest.raises(ValueError):
        AgentConfig(name="r", kind="a2a_remote", model="gemini-2.0-flash")


def test_appconfig_with_registries_and_validation_ok(tmp_path: Path):
    cfg = AppConfig(
        a2a_clients=[A2AClientConfig(id="c1", url="https://example.com/a2a")],
        agents=[AgentConfig(name="local", model="gemini-2.0-flash")],
        mcp_registry=McpRegistryConfig(
            servers=[McpRegistryServer(id="m1", mode="sse", url="https://mcp.local")],
            groups=[RegistryGroup(id="g1", include=["m1"])],
        ),
        openapi_registry=OpenApiRegistryConfig(
            fetch_allowlist=["example.com"],
            apis=[
                OpenApiApiConfig(
                    id="api1",
                    spec={"inline": "{}"},
                    spec_type="json",
                )
            ],
            groups=[RegistryGroup(id="apis", include=["api1"])],
        ),
    )
    issues = validate_app_config(cfg)
    assert issues == []


def test_validation_detects_unknown_group_refs_and_dupes():
    cfg = AppConfig(
        a2a_clients=[A2AClientConfig(id="c1", url="https://example.com/a2a"), A2AClientConfig(id="c1", url="https://example.com/dup")],
        agents=[AgentConfig(name="local", model="gemini-2.0-flash")],
        mcp_registry=McpRegistryConfig(
            servers=[McpRegistryServer(id="m1", mode="sse", url="https://mcp.local")],
            groups=[RegistryGroup(id="g1", include=["m2"])],  # m2 does not exist
        ),
        openapi_registry=OpenApiRegistryConfig(
            apis=[OpenApiApiConfig(id="api1", spec={"inline": "{}"}), OpenApiApiConfig(id="api1", spec={"inline": "{}"})],
            groups=[RegistryGroup(id="apis", include=["x"])],  # unknown api id
        ),
    )
    issues = validate_app_config(cfg)
    assert any("duplicate a2a_client id" in m for m in issues)
    assert any("duplicate openapi api id" in m for m in issues)
    assert any("mcp group 'g1'" in m for m in issues)
    assert any("openapi group 'apis'" in m for m in issues)


def test_openapi_url_requires_allowlist():
    cfg = AppConfig(
        openapi_registry=OpenApiRegistryConfig(
            fetch_allowlist=["api.allowed.com"],
            apis=[OpenApiApiConfig(id="api1", spec={"url": "https://api.blocked.com/spec.json"})],
        )
    )
    issues = validate_app_config(cfg)
    assert any("not allowlisted" in m for m in issues)

