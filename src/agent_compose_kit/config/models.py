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
    "sql",
    "yaml_file",
    "db",
    "database",
    "s3",
    "local_folder",
]


class SessionServiceConfig(BaseModel):
    """Config for SessionService backends.

    Supported types: in_memory, redis, mongo, sql, yaml_file, db, database
    """
    type: Literal[
        "in_memory",
        "redis",
        "mongo",
        "sql",
        "yaml_file",
        "db",
        "database",
    ] = "in_memory"
    # redis (url or discrete fields)
    redis_url: Optional[str] = None
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_db: Optional[int] = None
    redis_password: Optional[str] = None
    # mongo
    mongo_url: Optional[str] = None
    db_name: Optional[str] = None
    # sql (SQLAlchemy-style URL)
    db_url: Optional[str] = None
    # yaml files
    base_path: Optional[str] = None
    # extra params
    params: Dict[str, Any] = Field(default_factory=dict)


class ArtifactServiceConfig(BaseModel):
    """Config for ArtifactService backends (in-memory, local, s3, mongo, sql)."""
    type: Literal["in_memory", "s3", "local_folder", "mongo", "sql"] = "in_memory"
    # s3/mongo
    bucket_name: Optional[str] = None
    # s3
    endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None
    s3_prefix: Optional[str] = None
    # local
    base_path: Optional[str] = None
    # mongo
    mongo_url: Optional[str] = None
    db_name: Optional[str] = None
    # sql
    db_url: Optional[str] = None
    # generic
    params: Dict[str, Any] = Field(default_factory=dict)


class MemoryServiceConfig(BaseModel):
    """Config for MemoryService (in-memory or extras-backed)."""
    type: Optional[Literal["in_memory", "redis", "mongo", "sql", "yaml_file"]] = None
    # redis (discrete fields)
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_db: Optional[int] = None
    # mongo
    mongo_url: Optional[str] = None
    db_name: Optional[str] = None
    # sql
    db_url: Optional[str] = None
    # yaml
    base_path: Optional[str] = None
    # generic
    params: Dict[str, Any] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    """Runtime tuning for runs (streaming mode, limits, artifact capture)."""
    streaming_mode: Optional[Literal["NONE", "SSE", "BIDI"]] = None
    max_llm_calls: Optional[int] = None
    save_input_blobs_as_artifacts: Optional[bool] = None
    speech: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Agent definition for building LlmAgent instances.

    Supports advanced LlmAgent fields like description, include_contents,
    output_key, generate_content_config, planner, code_executor, and
    structured input/output schemas via dotted imports.
    """
    name: str
    # Phase 1: support remote A2A client kind
    kind: Literal["llm", "a2a_remote"] = "llm"
    client: Optional[str] = None  # required when kind=a2a_remote
    model: Any  # string or mapping (e.g., {type: litellm, model: "openai/gpt-4o", api_base: ...})
    instruction: Optional[str] = None
    description: Optional[str] = None
    tools: List[Any] = Field(default_factory=list)  # may be string or dict entries
    sub_agents: List[str] = Field(default_factory=list)
    # Advanced LlmAgent options (all optional, passed through when present)
    include_contents: Optional[str] = None  # 'default' | 'none'
    output_key: Optional[str] = None
    generate_content_config: Dict[str, Any] = Field(default_factory=dict)
    # Planners and code execution (optional, guarded by availability)
    planner: Optional[Dict[str, Any]] = None  # e.g., {type: built_in, thinking_config:{...}} | {type: plan_react}
    code_executor: Optional[str] = None  # dotted ref to a BaseCodeExecutor factory or instance
    # Structured IO (Python: dotted refs to Pydantic BaseModel classes)
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        # Ensure client is provided when kind=a2a_remote
        if self.kind == "a2a_remote" and not self.client:
            raise ValueError("AgentConfig.client is required when kind='a2a_remote'")


class GroupConfig(BaseModel):
    """Simple named group for convenience, mapping to agent names."""
    name: str
    members: List[str]


class WorkflowConfig(BaseModel):
    """Workflow composition (sequential, parallel, loop) over agent names."""
    type: Optional[Literal["sequential", "parallel", "loop"]] = None
    nodes: List[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Top-level application config loaded from YAML."""
    services: Dict[str, Any] = Field(default_factory=dict)
    # Accept either structured config or URI string for services
    session_service: SessionServiceConfig | str = Field(default_factory=SessionServiceConfig)
    artifact_service: ArtifactServiceConfig | str = Field(default_factory=ArtifactServiceConfig)
    memory_service: Optional[MemoryServiceConfig | str] = None
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
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    # Optional root-level instruction applied to the root agent
    global_instruction: Optional[str] = None

    # Phase 1 additions: external registries and A2A clients
    a2a_clients: List["A2AClientConfig"] = Field(default_factory=list)
    mcp_registry: Optional["McpRegistryConfig"] = None
    openapi_registry: Optional["OpenApiRegistryConfig"] = None


def _interpolate_env(text: str) -> str:
    """Substitute ${VAR} and $VAR sequences with environment values."""
    def repl(match: "re.Match[str]") -> str:  # type: ignore[name-defined]
        var = match.group(1) or match.group(2)
        return os.environ.get(var, "")

    import re

    pattern = re.compile(r"\$\{([^}]+)\}|\$(\w+)")
    return pattern.sub(repl, text)


def load_config_file(path: Path) -> AppConfig:
    """Load an AppConfig from a YAML file with env interpolation.

    Also supports back-compat for services nested under a `services:` block.
    """
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
    """Write a minimal example config YAML to the target path."""
    path.write_text(EXAMPLE_YAML + "\n", encoding="utf-8")


def export_app_config_schema() -> dict:
    """Return JSON schema for AppConfig for external validators/IDEs."""
    return AppConfig.model_json_schema()


# =======================
# Phase 1 new schema types
# =======================


class A2AClientConfig(BaseModel):
    """Configuration for a remote A2A Agent endpoint consumed by this app.

    Minimal shape for Phase 1; actual client wiring added in a later phase.
    """
    id: str
    url: str
    headers: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[float] = None
    description: Optional[str] = None


def parse_service_uri(kind: str, uri: str) -> SessionServiceConfig | ArtifactServiceConfig | MemoryServiceConfig:
    """Parse a service URI string into a structured config.

    Supported schemes (conservative defaults):
    - Sessions/Memory:
      - redis://host:port/db
      - mongodb://... or mongo://...
      - sqlite:///..., postgresql://..., mysql://... (treated as SQL "db_url")
      - yaml://<base_path>
      - memory: (in-memory)
    - Artifacts:
      - file://<base_path> (or local://<base_path>)
      - s3://bucket/prefix
      - mongodb://... (db_name from path)
      - sqlite/postgresql/mysql (treated as SQL "db_url")

    If insufficient information is provided, returns an in-memory config for the kind.
    """
    from urllib.parse import urlparse

    k = kind.strip().lower()
    u = urlparse(uri)
    scheme = (u.scheme or "").lower()

    def _inmem():
        if k == "session":
            return SessionServiceConfig(type="in_memory")
        if k == "artifact":
            return ArtifactServiceConfig(type="in_memory")
        return MemoryServiceConfig(type="in_memory")

    if not scheme:
        return _inmem()

    # Memory shorthand
    if scheme in {"memory", "inmemory"}:
        return _inmem()

    # YAML-backed
    if scheme in {"yaml", "file+yaml", "yaml+file"}:
        base = (u.netloc + u.path).lstrip("/")
        if k == "session":
            return SessionServiceConfig(type="yaml_file", base_path=base or None)
        if k == "artifact":
            # No YAML artifact store; fall back to local folder if given
            return ArtifactServiceConfig(type="local_folder", base_path=base or None)
        return MemoryServiceConfig(type="yaml_file", base_path=base or None)

    # Redis
    if scheme == "redis":
        if k == "session":
            return SessionServiceConfig(type="redis", redis_url=uri)
        if k == "memory":
            db = None
            try:
                if u.path and len(u.path) > 1:
                    db = int(u.path.lstrip("/"))
            except Exception:
                db = None
            return MemoryServiceConfig(
                type="redis",
                redis_host=u.hostname or None,
                redis_port=u.port or None,
                redis_db=db,
            )
        return _inmem()

    # Mongo
    if scheme in {"mongodb", "mongo"}:
        db_name = u.path.lstrip("/") or None
        if k == "session":
            return SessionServiceConfig(type="mongo", mongo_url=uri, db_name=db_name)
        if k == "artifact":
            return ArtifactServiceConfig(type="mongo", mongo_url=uri, db_name=db_name)
        return MemoryServiceConfig(type="mongo", mongo_url=uri, db_name=db_name)

    # SQL-like (sqlite/postgres/mysql)
    if scheme in {"sqlite", "postgresql", "postgres", "mysql"}:
        if k == "session":
            return SessionServiceConfig(type="sql", db_url=uri)
        if k == "artifact":
            return ArtifactServiceConfig(type="sql", db_url=uri)
        return MemoryServiceConfig(type="sql", db_url=uri)

    # Local folder artifacts
    if k == "artifact" and scheme in {"file", "local"}:
        base = (u.netloc + u.path).lstrip("/")
        return ArtifactServiceConfig(type="local_folder", base_path=base or None)

    # S3 artifacts
    if k == "artifact" and scheme == "s3":
        bucket = u.netloc or None
        prefix = u.path.lstrip("/") or None
        return ArtifactServiceConfig(type="s3", bucket_name=bucket, s3_prefix=prefix)

    # Unknown scheme → in-memory
    return _inmem()


class McpRegistryServer(BaseModel):
    id: str
    mode: Literal["sse", "stdio", "http"] = "sse"
    # SSE/HTTP
    url: Optional[str] = None
    headers: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[float] = None
    sse_read_timeout: Optional[float] = None
    # stdio
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    # filters and auth surface (forwarded to toolset later)
    tool_filter: List[str] = Field(default_factory=list)
    auth_scheme: Optional[str] = None
    auth_credential: Optional[str] = None


class RegistryGroup(BaseModel):
    id: str
    include: List[str] = Field(default_factory=list)


class McpRegistryConfig(BaseModel):
    servers: List[McpRegistryServer] = Field(default_factory=list)
    groups: List[RegistryGroup] = Field(default_factory=list)


class OpenApiAuthConfig(BaseModel):
    """Auth configuration for OpenAPI toolsets.

    - bearer: uses `value` as token
    - header: use `name` and `value`
    - query: use `name` and `value`
    """
    type: Literal["bearer", "header", "query"]
    name: Optional[str] = None
    value: Optional[str] = None


class OpenApiApiConfig(BaseModel):
    id: str
    spec: Dict[str, Any]
    spec_type: Literal["json", "yaml"] | None = None
    headers: Dict[str, Any] = Field(default_factory=dict)
    auth: Optional[OpenApiAuthConfig] = None
    operation_filter: List[str] = Field(default_factory=list)
    tag_filter: List[str] = Field(default_factory=list)
    tool_filter: List[str] = Field(default_factory=list)
    timeout: Optional[float] = None


class OpenApiRegistryConfig(BaseModel):
    fetch_allowlist: List[str] = Field(default_factory=list)
    apis: List[OpenApiApiConfig] = Field(default_factory=list)
    groups: List[RegistryGroup] = Field(default_factory=list)


# ======================
# Validation entry points
# ======================


def validate_app_config(cfg: AppConfig) -> List[str]:
    """Validate cross-references and groups for registries and agents.

    Args:
        cfg: Application configuration to validate.

    Returns:
        List of human-readable diagnostics. Empty list means OK.
    """
    issues: List[str] = []

    # Uniqueness for ids
    def _check_dupes(items: List[str], label: str) -> None:
        seen: Dict[str, int] = {}
        for x in items:
            seen[x] = seen.get(x, 0) + 1
        for k, n in seen.items():
            if n > 1:
                issues.append(f"duplicate {label} id: {k}")

    _check_dupes([a.id for a in cfg.a2a_clients], "a2a_client")
    if cfg.mcp_registry:
        _check_dupes([s.id for s in cfg.mcp_registry.servers], "mcp server")
        # Group includes validity
        valid = {s.id for s in cfg.mcp_registry.servers}
        for g in cfg.mcp_registry.groups:
            for ref in g.include:
                if ref not in valid:
                    issues.append(f"mcp group '{g.id}' includes unknown server id '{ref}'")

    if cfg.openapi_registry:
        _check_dupes([a.id for a in cfg.openapi_registry.apis], "openapi api")
        valid = {a.id for a in cfg.openapi_registry.apis}
        for g in cfg.openapi_registry.groups:
            for ref in g.include:
                if ref not in valid:
                    issues.append(f"openapi group '{g.id}' includes unknown api id '{ref}'")

        # If spec.url is used, ensure it is allowlisted
        allow = cfg.openapi_registry.fetch_allowlist
        if allow:
            from urllib.parse import urlparse

            for api in cfg.openapi_registry.apis:
                spec = api.spec or {}
                url = spec.get("url") if isinstance(spec, dict) else None
                if url:
                    host = urlparse(str(url)).netloc
                    if not _host_allowlisted(host, allow):
                        issues.append(
                            f"openapi api '{api.id}' url host '{host}' not allowlisted"
                        )

    # Agent kind cross-checks
    for a in cfg.agents:
        if a.kind == "a2a_remote":
            if not a.client:
                issues.append(f"agent '{a.name}' requires 'client' when kind=a2a_remote")
            elif all(c.id != a.client for c in cfg.a2a_clients):
                issues.append(
                    f"agent '{a.name}' references unknown a2a_client id '{a.client}'"
                )

    return issues


def _host_allowlisted(host: str, allowlist: List[str]) -> bool:
    """Simple hostname allowlist with wildcard prefix support (e.g., *.example.com)."""
    host = host.lower()
    for pat in allowlist:
        p = pat.lower().strip()
        if p == host:
            return True
        if p.startswith("*."):
            suffix = p[1:]  # keep leading dot
            if host.endswith(suffix):
                return True
    return False
