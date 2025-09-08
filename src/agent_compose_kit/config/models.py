from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
import re
from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator

# =====================
# Core reference types
# =====================

RegistryKind = Literal["mcp", "openapi", "agent", "function"]


class RegistryRef(BaseModel):
    """Reference to an external registry object.

    Format: registry://{kind}/{key}@{range|version|latest}
    This model stores the raw string and a parsed view for validation and tooling.
    """

    value: str = Field(
        ...,
        json_schema_extra={
            "markdownDescription": "Reference to an external registry object. Format: registry://{kind}/{key}@{version|range|latest}",
            "examples": [
                "registry://mcp/files@latest",
                "registry://openapi/petstore@1.0.0",
                "registry://agent/planner@>=0.2",
            ],
            # Hints for Monaco (non-standard keyword tolerated by many validators)
            "errorMessage": {
                "type": "Must be a string like registry://kind/key@version",
            },
        },
    )
    kind: Optional[RegistryKind] = None
    key: Optional[str] = None
    version: Optional[str] = None

    @model_validator(mode="after")
    def _parse(self) -> "RegistryRef":
        v = self.value
        if not isinstance(v, str) or not v.startswith("registry://"):
            raise ValueError("RegistryRef must start with 'registry://'")
        rest = v[len("registry://") :]
        if "@" in rest:
            path, ver = rest.split("@", 1)
        else:
            path, ver = rest, "latest"
        if "/" not in path:
            raise ValueError("RegistryRef path must be '{kind}/{key}'")
        kind_str, key = path.split("/", 1)
        if kind_str not in ("mcp", "openapi", "agent", "function"):
            raise ValueError("RegistryRef kind must be one of mcp|openapi|agent|function")
        self.kind = kind_str  # type: ignore[assignment]
        self.key = key
        self.version = ver
        return self


class ModelAliasRef(BaseModel):
    """Reference to a named model alias. Format: alias://{alias}"""

    value: str = Field(
        ...,
        json_schema_extra={
            "markdownDescription": "Model alias reference. Format: alias://{alias}",
            "examples": ["alias://chat-default"],
        },
    )

    @model_validator(mode="after")
    def _check(self) -> "ModelAliasRef":
        if not isinstance(self.value, str) or not self.value.startswith("alias://"):
            raise ValueError("ModelAliasRef must start with 'alias://'")
        if len(self.value.split("alias://", 1)[1].strip()) == 0:
            raise ValueError("ModelAliasRef must include an alias name")
        return self


class RefOrInline(BaseModel):
    """Generic wrapper: either an external ref or inline object."""

    ref: Optional[RegistryRef] = None
    inline: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _oneof(self) -> "RefOrInline":
        if bool(self.ref) == bool(self.inline):
            raise ValueError("Provide exactly one of 'ref' or 'inline'")
        return self


# =====================
# Tools (attachable)
# =====================


class ToolAuthConfig(BaseModel):
    """Optional authentication config attached to a tool invocation.

    This kit does not perform authentication; it only validates structure so
    downstream runtimes can act on it. When present, `auth_scheme` must be a
    non-empty string recognized by the runtime (e.g., bearer|header|query|basic|oauth2).
    """

    auth_scheme: str = Field(
        ..., json_schema_extra={"markdownDescription": "Authentication scheme identifier (e.g., bearer, header, query)"}
    )
    auth_credential: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Opaque credential (token, basic creds, etc.) for runtimes that expect a single value."},
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={"markdownDescription": "Scheme-specific parameters (token, header name, etc.)"},
    )

    @field_validator("auth_scheme")
    @classmethod
    def _non_empty_scheme(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("auth_config.auth_scheme must be a non-empty string")
        return v


# =====================
# Planners (attachable)
# =====================


class PlannerBuiltIn(BaseModel):
    type: Literal['built_in'] = 'built_in'
    thinking_config: Dict[str, Any] = Field(
        ..., json_schema_extra={"markdownDescription": "google.genai.types.ThinkingConfig payload (passed to runtime)"}
    )

    @model_validator(mode='after')
    def _non_empty_tc(self) -> 'PlannerBuiltIn':
        if not isinstance(self.thinking_config, dict) or not self.thinking_config:
            raise ValueError('planner.built_in requires non-empty thinking_config')
        return self


class PlannerPlanReAct(BaseModel):
    type: Literal['plan_react'] = 'plan_react'
    options: Dict[str, Any] = Field(default_factory=dict)


Planner = Union[PlannerBuiltIn, PlannerPlanReAct]

class McpTool(BaseModel):
    kind: Literal["mcp"] = Field(
        default="mcp",
        json_schema_extra={"markdownDescription": "MCP tool entry"},
    )
    server: RefOrInline = Field(
        ..., json_schema_extra={"markdownDescription": "Server reference or inline MCP server config"}
    )
    tool: str = Field(..., json_schema_extra={"markdownDescription": "Tool name exposed by the MCP server"})
    config: Dict[str, Any] = Field(
        default_factory=dict, json_schema_extra={"markdownDescription": "Optional per-tool configuration"}
    )
    auth_config: Optional[ToolAuthConfig] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Optional authentication config; when omitted, runtimes may skip auth."},
    )

    @model_validator(mode="after")
    def _validate_kinds(self) -> "McpTool":
        if self.server and self.server.ref:
            if self.server.ref.kind != "mcp":
                raise ValueError("mcp tool 'server.ref' must be kind 'mcp'")
        return self


class OpenApiTool(BaseModel):
    kind: Literal["openapi"] = Field(default="openapi")
    spec: RefOrInline
    operationId: str = Field(..., json_schema_extra={"markdownDescription": "OpenAPI operationId to call"})
    parameters: Dict[str, Any] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    auth_config: Optional[ToolAuthConfig] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Optional authentication config; when omitted, runtimes may skip auth."},
    )

    @model_validator(mode="after")
    def _validate_kinds(self) -> "OpenApiTool":
        if self.spec and self.spec.ref:
            if self.spec.ref.kind != "openapi":
                raise ValueError("openapi tool 'spec.ref' must be kind 'openapi'")
        return self


class FunctionToolDef(BaseModel):
    import_: Optional[str] = Field(default=None, alias="import")
    code: Optional[str] = None
    deps: List[str] = Field(default_factory=list)


class FunctionTool(BaseModel):
    kind: Literal["function"] = Field(default="function")
    function: Union[RefOrInline, FunctionToolDef]
    signature: Dict[str, Any] = Field(default_factory=dict)
    policy: Dict[str, Any] = Field(default_factory=dict)
    long_running: bool = Field(
        default=False,
        json_schema_extra={"markdownDescription": "Mark as a long-running function (maps to ADK LongRunningFunctionTool)"},
    )

    @model_validator(mode="after")
    def _validate_kinds(self) -> "FunctionTool":
        if isinstance(self.function, RefOrInline) and self.function.ref:
            if self.function.ref.kind != "function":
                raise ValueError("function tool 'function.ref' must be kind 'function'")
        return self


class AgentTool(BaseModel):
    kind: Literal["agent"] = Field(default="agent")
    agent: Union[str, RegistryRef] = Field(
        ..., json_schema_extra={"markdownDescription": "Reference to another agent by name or registry ref"}
    )  # AgentRef

    @model_validator(mode="after")
    def _validate_kinds(self) -> "AgentTool":
        if isinstance(self.agent, RegistryRef) and self.agent.kind != "agent":
            raise ValueError("agent tool 'agent' ref must be kind 'agent'")
        return self


class OpenApiToolset(BaseModel):
    kind: Literal["openapi_toolset"] = Field(default="openapi_toolset")
    spec: RefOrInline
    auth_config: Optional[ToolAuthConfig] = None
    tool_filter: Optional[List[str]] = Field(default=None, json_schema_extra={"markdownDescription": "Optional list of tool names to include"})

    @model_validator(mode="after")
    def _validate_spec_kind(self) -> "OpenApiToolset":
        if self.spec and self.spec.ref and self.spec.ref.kind != "openapi":
            raise ValueError("openapi_toolset 'spec.ref' must be kind 'openapi'")
        return self


class McpToolset(BaseModel):
    kind: Literal["mcp_toolset"] = Field(default="mcp_toolset")
    server: RefOrInline
    auth_config: Optional[ToolAuthConfig] = None
    tool_filter: Optional[List[str]] = Field(default=None, json_schema_extra={"markdownDescription": "Optional list of tool names to include"})

    @model_validator(mode="after")
    def _validate_server_kind(self) -> "McpToolset":
        if self.server and self.server.ref and self.server.ref.kind != "mcp":
            raise ValueError("mcp_toolset 'server.ref' must be kind 'mcp'")
        return self


class ApiHubToolset(BaseModel):
    kind: Literal["apihub_toolset"] = Field(default="apihub_toolset")
    apihub_resource_name: str
    auth_config: Optional[ToolAuthConfig] = None
    tool_filter: Optional[List[str]] = None
    name: Optional[str] = None
    description: Optional[str] = None


class BuiltInTool(BaseModel):
    kind: Literal["builtin"] = Field(default="builtin")
    name: Literal[
        "vertex_ai_search",
        "url_context",
        "google_search",
        "code_execution",
        "bigquery_toolset",
        "spanner_toolset",
        "retrieval",
    ]
    params: Dict[str, Any] = Field(default_factory=dict)


Tool = Union[McpTool, OpenApiTool, FunctionTool, AgentTool, OpenApiToolset, McpToolset, ApiHubToolset, BuiltInTool]


# =====================
# Agents (variants)
# =====================


class LlmAgentCfg(BaseModel):
    type: Literal["llm"] = "llm"
    name: str = Field(
        ...,
        json_schema_extra={
            "markdownDescription": "Agent name (^[A-Za-z][-_A-Za-z0-9]{0,63}$)",
            "errorMessage": {
                "pattern": "Agent name must start with a letter and contain only letters, numbers, '-' or '_' (max 64).",
                "type": "Agent name must be a string",
            },
        },
    )
    description: Optional[str] = None
    model: Optional[Union[str, ModelAliasRef]] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "string model id or alias://name"},
    )
    instruction: str = Field(
        ..., json_schema_extra={
            "markdownDescription": "System instruction for the agent",
            "errorMessage": {"type": "instruction must be a non-empty string"},
        }
    )
    # Tools & sub-agents
    tools: List[Tool] = Field(
        default_factory=list,
        json_schema_extra={
            "markdownDescription": "Attachable tools (mcp, openapi, function, or agent)",
            "examples": [
                {"kind": "function", "function": {"import": "pkg.mod:fn"}},
                {"kind": "mcp", "server": {"ref": {"value": "registry://mcp/files@latest"}}, "tool": "read_file"},
                {"kind": "agent", "agent": "helper"},
            ],
        },
    )
    sub_agents: List[Union[str, RegistryRef]] = Field(default_factory=list)
    # Delegation/transfer controls (align to ADK booleans)
    disallow_transfer_to_parent: bool = Field(
        default=False,
        json_schema_extra={"markdownDescription": "When true, LLM cannot transfer to parent"},
    )
    disallow_transfer_to_peers: bool = Field(
        default=False,
        json_schema_extra={"markdownDescription": "When true, LLM cannot transfer to peer agents"},
    )
    # Content & schemas
    include_contents: Literal['default','none'] = Field(
        default='default',
        json_schema_extra={"markdownDescription": "default: include relevant history; none: no history"},
    )
    input_schema: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Dotted ref to Pydantic BaseModel used when agent is a tool (module:Class)"},
    )
    output_schema: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "markdownDescription": "Dotted ref to Pydantic BaseModel for structured replies; disables tool use when set (runtime).",
        },
    )
    output_key: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Session state key to store the agent's output (used by downstream steps)"},
    )
    # Advanced
    generate_content_config: Dict[str, Any] = Field(default_factory=dict)
    planner: Optional[Planner] = Field(default=None)
    code_executor: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Dotted ref to code executor (advisory)"},
    )
    # Callbacks (lists of dotted refs)
    before_model_callbacks: List[str] = Field(default_factory=list)
    after_model_callbacks: List[str] = Field(default_factory=list)
    before_tool_callbacks: List[str] = Field(default_factory=list)
    after_tool_callbacks: List[str] = Field(default_factory=list)
    # Global instruction (root-only advisory)
    global_instruction: Optional[str] = None
    
    @field_validator("instruction")
    @classmethod
    def _non_empty_instruction(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("instruction must be a non-empty string")
        return v

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v):
            raise ValueError("agent name must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v

    @model_validator(mode="after")
    def _validate_sub_agents_kinds(self) -> "LlmAgentCfg":
        for r in self.sub_agents:
            if isinstance(r, RegistryRef) and r.kind != "agent":
                raise ValueError("llm sub_agents registry refs must be kind 'agent'")
        return self

    @field_validator("input_schema", "output_schema")
    @classmethod
    def _validate_dotted_ref(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Accept "module:Attr" or "module.sub.Mod:Attr" or "module.Class"
        if ":" in v:
            mod, attr = v.split(":", 1)
            if not mod or not attr:
                raise ValueError("schema dotted ref must be 'module:Attr'")
        else:
            # Allow simple module.Class form
            parts = v.split(".")
            if len(parts) < 2:
                raise ValueError("schema dotted ref must include module and attribute")
        return v


class SequentialAgentCfg(BaseModel):
    type: Literal["workflow.sequential"] = "workflow.sequential"
    name: str = Field(
        ..., json_schema_extra={
            "markdownDescription": "Agent name (^[A-Za-z][-_A-Za-z0-9]{0,63}$)",
            "errorMessage": {
                "pattern": "Agent name must start with a letter and contain only letters, numbers, '-' or '_' (max 64).",
                "type": "Agent name must be a string",
            },
        }
    )
    description: Optional[str] = None
    sub_agents: List[Union[str, RegistryRef]] = Field(
        ..., json_schema_extra={"markdownDescription": "Run sub_agents in order"}
    )
    parent_agent: Optional[str] = None  # advisory only
    before_agent_callback: Optional[Union[str, List[str]]] = None
    after_agent_callback: Optional[Union[str, List[str]]] = None

    @field_validator("sub_agents")
    @classmethod
    def _non_empty_subs(cls, v: List[Union[str, RegistryRef]]):
        if not v:
            raise ValueError("sequential agent requires at least one sub_agent")
        return v

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v):
            raise ValueError("agent name must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v


class ParallelAgentCfg(BaseModel):
    type: Literal["workflow.parallel"] = "workflow.parallel"
    name: str = Field(
        ..., json_schema_extra={
            "markdownDescription": "Agent name (^[A-Za-z][-_A-Za-z0-9]{0,63}$)",
            "errorMessage": {
                "pattern": "Agent name must start with a letter and contain only letters, numbers, '-' or '_' (max 64).",
                "type": "Agent name must be a string",
            },
        }
    )
    description: Optional[str] = None
    sub_agents: List[Union[str, RegistryRef]] = Field(
        ..., json_schema_extra={"markdownDescription": "Run sub_agents in parallel"}
    )
    parent_agent: Optional[str] = None  # advisory only
    before_agent_callback: Optional[Union[str, List[str]]] = None
    after_agent_callback: Optional[Union[str, List[str]]] = None

    @field_validator("sub_agents")
    @classmethod
    def _non_empty_parallel_subs(cls, v: List[Union[str, RegistryRef]]):
        if not v:
            raise ValueError("parallel agent requires at least one sub_agent")
        return v

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v):
            raise ValueError("agent name must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v

    # no merge field in ADK parallel agent; synthesis is done by a downstream agent


class LoopAgentCfg(BaseModel):
    type: Literal["workflow.loop"] = "workflow.loop"
    name: str = Field(
        ..., json_schema_extra={
            "markdownDescription": "Agent name (^[A-Za-z][-_A-Za-z0-9]{0,63}$)",
            "errorMessage": {
                "pattern": "Agent name must start with a letter and contain only letters, numbers, '-' or '_' (max 64).",
                "type": "Agent name must be a string",
            },
        }
    )
    description: Optional[str] = None
    sub_agents: List[Union[str, RegistryRef]] = Field(
        ..., json_schema_extra={"markdownDescription": "Agents to run each iteration in order"}
    )
    max_iterations: Optional[int] = Field(
        default=None, json_schema_extra={"markdownDescription": "Maximum loop iterations; stops earlier if a sub-agent escalates"}
    )
    parent_agent: Optional[str] = None  # advisory only
    before_agent_callback: Optional[Union[str, List[str]]] = None
    after_agent_callback: Optional[Union[str, List[str]]] = None

    @field_validator("max_iterations")
    @classmethod
    def _positive_iters(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("max_iters must be positive when provided")
        return v

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v):
            raise ValueError("agent name must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v


class CustomAgentCfg(BaseModel):
    type: Literal["custom"] = "custom"
    name: str = Field(
        ..., json_schema_extra={
            "markdownDescription": "Agent name (^[A-Za-z][-_A-Za-z0-9]{0,63}$)",
            "errorMessage": {
                "pattern": "Agent name must start with a letter and contain only letters, numbers, '-' or '_' (max 64).",
                "type": "Agent name must be a string",
            },
        }
    )
    class_: str = Field(alias="class", json_schema_extra={"markdownDescription": "Import path to concrete agent class"})
    params: Dict[str, Any] = Field(default_factory=dict)
    # Optional declaration for visualization only; runtime is free to wire differently
    sub_agents: List[Union[str, RegistryRef]] = Field(
        default_factory=list,
        json_schema_extra={
            "markdownDescription": "Optional sub-agents this custom agent orchestrates (for graph visualization only)",
        },
    )

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v):
            raise ValueError("agent name must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v


Agent = Union[LlmAgentCfg, SequentialAgentCfg, ParallelAgentCfg, LoopAgentCfg, CustomAgentCfg]


# =====================
# Top-level config
# =====================


class Metadata(BaseModel):
    name: str = Field(
        ...,
        json_schema_extra={
            "markdownDescription": "Application name",
            "errorMessage": {"type": "metadata.name must be a string"},
        },
    )
    description: Optional[str] = Field(default=None, json_schema_extra={"markdownDescription": "Short description"})
    labels: Dict[str, str] = Field(default_factory=dict, json_schema_extra={"markdownDescription": "Freeform labels"})


class Defaults(BaseModel):
    model_alias: Optional[str] = Field(default=None, json_schema_extra={"markdownDescription": "Default model alias for LLM agents"})
    runner_policy: Optional[Literal["sandbox", "burst"]] = Field(default=None)
    egress_policy: List[str] = Field(default_factory=list, json_schema_extra={"markdownDescription": "Allowed egress host patterns"})


class Registries(BaseModel):
    mcp: List[RefOrInline] = Field(default_factory=list, json_schema_extra={"markdownDescription": "MCP servers"})
    openapi: List[RefOrInline] = Field(default_factory=list, json_schema_extra={"markdownDescription": "OpenAPI specs"})
    agents: List[RefOrInline] = Field(default_factory=list, json_schema_extra={"markdownDescription": "Agent registries"})
    functions: List[RefOrInline] = Field(default_factory=list, json_schema_extra={"markdownDescription": "Function registries"})


# =====================
# Model Alias Registry (pure declarative)
# =====================


class ModelAliasEntry(BaseModel):
    id: str = Field(..., json_schema_extra={"markdownDescription": "Alias name. Used as alias://{id}"})
    resolver: Literal["direct", "litellm", "class"] = Field(
        ...,
        json_schema_extra={"markdownDescription": "Resolution strategy: direct string id, LiteLLM adapter, or explicit BaseLlm subclass"},
    )
    model: str = Field(
        ...,
        json_schema_extra={
            "markdownDescription": "Model identifier or endpoint string (for 'direct' & 'class'), or provider-prefixed LiteLLM model id (for 'litellm')",
        },
    )
    class_ref: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Dotted ref 'module:Class' for resolver=='class' (no import here)"},
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={"markdownDescription": "Optional runtime parameters (no secrets). Backend may whitelist fields."},
    )
    auth_ref: Optional[str] = Field(
        default=None,
        json_schema_extra={"markdownDescription": "Reference to an external auth profile or secret (e.g., env:OPENAI_API_KEY, vault://path)"},
    )
    provider: Optional[str] = Field(default=None, json_schema_extra={"markdownDescription": "Advisory provider label (gemini, openai, anthropic, vertex_ai, ollama, etc.)"})
    labels: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None

    @field_validator("id")
    @classmethod
    def _valid_alias_id(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z][-_A-Za-z0-9]{0,63}$", v or ""):
            raise ValueError("alias id must match ^[A-Za-z][-_A-Za-z0-9]{0,63}$")
        return v

    @model_validator(mode="after")
    def _class_ref_required_when_class(self) -> "ModelAliasEntry":
        if self.resolver == "class":
            if not self.class_ref:
                raise ValueError("class_ref is required when resolver=='class'")
            # validate dotted shape without importing
            if ":" not in self.class_ref:
                raise ValueError("class_ref must be 'module:Class'")
        return self


class ModelAliasRegistry(BaseModel):
    aliases: List[ModelAliasEntry] = Field(default_factory=list)

    def index(self) -> Dict[str, ModelAliasEntry]:  # pragma: no cover - convenience
        return {a.id: a for a in self.aliases}


class SharedBackends(BaseModel):
    sessions: Optional[Dict[str, Any]] = Field(default=None, json_schema_extra={"markdownDescription": "Declared session backend (not executed here)"})
    memory: Optional[Dict[str, Any]] = Field(default=None, json_schema_extra={"markdownDescription": "Declared memory backend (not executed here)"})
    artifacts: Optional[Dict[str, Any]] = Field(default=None, json_schema_extra={"markdownDescription": "Declared artifacts backend (not executed here)"})


class AppConfig(BaseModel):
    schema_version: str = Field(
        ...,
        json_schema_extra={
            "examples": ["0.1.0"],
            "markdownDescription": "Semantic version of the schema",
            "errorMessage": {
                "pattern": "schema_version must be like 0.1.0 (semver)",
                "type": "schema_version must be a string",
            },
        },
    )
    metadata: Metadata
    defaults: Optional[Defaults] = None
    registries: Optional[Registries] = None
    model_aliases: Optional[ModelAliasRegistry] = Field(default=None, json_schema_extra={"markdownDescription": "Registry of model aliases referenced by alias://name"})
    agents: List[Agent] = Field(
        ..., json_schema_extra={
            "markdownDescription": "List of agent definitions (LLM, workflow, custom)",
            "examples": [
                {
                    "type": "llm",
                    "name": "planner",
                    "instruction": "Plan tasks and call tools",
                    "model": "gemini-2.5-flash",
                }
            ],
        },
    )
    backends: Optional[SharedBackends] = Field(
        default=None, json_schema_extra={"markdownDescription": "Declare shared backends only; not executed here."}
    )

    @field_validator("schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("schema_version must be semver, e.g., 0.1.0")
        return v

    @model_validator(mode="after")
    def _unique_agent_names(self) -> "AppConfig":
        names: Dict[str, int] = {}
        for a in self.agents:
            name = getattr(a, "name", None)
            if not name:
                continue
            names[name] = names.get(name, 0) + 1
        dups = [n for n, c in names.items() if c > 1]
        if dups:
            raise ValueError(f"duplicate agent names: {', '.join(sorted(dups))}")
        return self


# =====================
# Loader & Schema Export
# =====================


def load_config(yaml_or_dict: Union[str, Dict[str, Any]]) -> AppConfig:
    data: Dict[str, Any]
    if isinstance(yaml_or_dict, str):
        data = yaml.safe_load(yaml_or_dict) or {}
    else:
        data = yaml_or_dict
    try:
        return AppConfig.model_validate(data)
    except ValidationError as e:
        # Bubble up a concise error for callers; tests assert on structure
        raise ValueError(str(e))


def load_config_file(path: Path) -> AppConfig:
    """Load and validate an AppConfig from a YAML file.

    Args:
        path: Filesystem path to the YAML document.

    Returns:
        Parsed ``AppConfig`` instance.

    Raises:
        ValueError: When the file content fails schema validation.
    """
    raw = Path(path).read_text(encoding="utf-8")
    return load_config(raw)


def export_app_config_schema() -> dict:
    """Return JSON schema for AppConfig with ADK‑aligned agent variants."""
    return AppConfig.model_json_schema()
