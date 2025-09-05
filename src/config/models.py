from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


ServiceType = Literal[
    "in_memory",
    "redis",
    "mongo",
    "vertex_ai",
    "db",
    "database",
    "gcs",
    "s3",
    "local_folder",
]


class SessionServiceConfig(BaseModel):
    type: Literal["in_memory", "redis", "mongo", "vertex_ai", "db", "database"] = "in_memory"
    # redis
    redis_url: Optional[str] = None
    # mongo
    mongo_url: Optional[str] = None
    db_name: Optional[str] = None
    # database (sqlalchemy URL)
    db_url: Optional[str] = None
    # vertex ai / db may need extra fields; keep generic for now
    params: Dict[str, Any] = Field(default_factory=dict)


class ArtifactServiceConfig(BaseModel):
    type: Literal["in_memory", "gcs", "s3", "local_folder"] = "in_memory"
    # gcs
    bucket_name: Optional[str] = None
    # s3
    endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None
    # local
    base_path: Optional[str] = None
    # generic
    params: Dict[str, Any] = Field(default_factory=dict)


class MemoryServiceConfig(BaseModel):
    type: Optional[Literal["in_memory", "vertex_ai"]] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    name: str
    host: str
    port: int
    token_env: Optional[str] = None
    tool_allowlist: List[str] = Field(default_factory=list)


class RuntimeConfig(BaseModel):
    streaming_mode: Optional[Literal["NONE", "SSE", "BIDI"]] = None
    max_llm_calls: Optional[int] = None
    save_input_blobs_as_artifacts: Optional[bool] = None
    speech: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    name: str
    model: Any  # string or mapping (e.g., {type: litellm, model: "openai/gpt-4o", api_base: ...})
    instruction: Optional[str] = None
    tools: List[Any] = Field(default_factory=list)  # may be string or dict entries
    sub_agents: List[str] = Field(default_factory=list)


class GroupConfig(BaseModel):
    name: str
    members: List[str]


class WorkflowConfig(BaseModel):
    type: Optional[Literal["sequential", "parallel", "loop"]] = None
    nodes: List[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    services: Dict[str, Any] = Field(default_factory=dict)
    session_service: SessionServiceConfig = Field(default_factory=SessionServiceConfig)
    artifact_service: ArtifactServiceConfig = Field(default_factory=ArtifactServiceConfig)
    memory_service: Optional[MemoryServiceConfig] = None
    workflow: Optional[WorkflowConfig] = None
    # Defaults for LiteLLM providers, keyed by provider name (e.g., openai, ollama_chat)
    model_providers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # Optional shared toolsets that agents can reference by name via {use: <key>}
    toolsets: Dict[str, Any] = Field(default_factory=dict)
    # Optional global registries
    tools_registry: Dict[str, Any] = Field(default_factory=dict)
    agents_registry: Dict[str, Any] = Field(default_factory=dict)
    agents: List[AgentConfig] = Field(default_factory=list)
    groups: List[GroupConfig] = Field(default_factory=list)
    mcp: List[MCPServerConfig] = Field(default_factory=list)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)


def _interpolate_env(text: str) -> str:
    def repl(match: "re.Match[str]") -> str:  # type: ignore[name-defined]
        var = match.group(1) or match.group(2)
        return os.environ.get(var, "")

    import re

    pattern = re.compile(r"\$\{([^}]+)\}|\$(\w+)")
    return pattern.sub(repl, text)


def load_config_file(path: Path) -> AppConfig:
    raw = Path(path).read_text(encoding="utf-8")
    raw = _interpolate_env(raw)
    data = yaml.safe_load(raw) or {}
    # Back-compat: allow services: {session_service, artifact_service, memory_service}
    if isinstance(data.get("services"), dict):
        svc = data["services"]
        for key in ("session_service", "artifact_service", "memory_service"):
            if key in svc and key not in data:
                data[key] = svc[key]
    try:
        return AppConfig.model_validate(data)
    except ValidationError as e:  # pragma: no cover
        # Re-raise with a shorter message for CLI
        raise ValueError(e) from e


EXAMPLE_YAML = """
services:
  session_service: {type: in_memory}
  artifact_service: {type: local_folder, base_path: ./artifacts_storage}

agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: You are a helpful planner.
    tools: []

groups:
  - name: demo
    members: [planner]

runtime:
  streaming_mode: NONE
  max_llm_calls: 200
""".strip()


def write_example_config(path: Path) -> None:
    path.write_text(EXAMPLE_YAML + "\n", encoding="utf-8")


def export_app_config_schema() -> dict:
    """Return JSON schema for AppConfig for external validators/IDEs."""
    return AppConfig.model_json_schema()
