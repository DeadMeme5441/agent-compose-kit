Implementation Plan: A2A + MCP/OpenAPI Registries
=================================================

Scope (library-only)
- Add A2A remote-agent consumption (no hosting).
- Add MCP registry (SSE-first; stdio/http optional).
- Add OpenAPI registry with URL/path/inline spec + allowlist for URL fetch.
- Validation + /lint diagnostics. Keep server dev-only. No deploy/infra.

Schema changes (Pydantic)
- AppConfig:
  - a2a_clients: [{id, url, headers?, timeout?, description?}]
  - mcp_registry: {servers:[{id, mode: sse|stdio|http, url?, headers?, timeout?, sse_read_timeout?, command?, args?, env?, tool_filter?, auth_scheme?, auth_credential?}], groups:[{id, include:[]}]} 
  - openapi_registry: {fetch_allowlist?:[str], apis:[{id, spec:{inline|path|url}, spec_type?, headers?, auth:{type: bearer|header|query, name?, value?}, operation_filter?, tag_filter?, tool_filter?, timeout?}], groups:[{id, include:[]}]} 
- AgentConfig:
  - kind: "llm" (default) | "a2a_remote"
  - client: str (required when kind="a2a_remote")

Builders & registries
- A2A: build_agents() constructs RemoteA2aAgent when kind=a2a_remote (guard imports), sets name/instruction; usable in workflows/groups.
- McpRegistry (tools/mcp_registry.py): get()/get_group()/close_all(); build McpToolset with Sse/Http/Stdio params; pass tool_filter + auth_scheme/credential.
- OpenAPIRegistry (tools/openapi_registry.py): get()/get_group()/close_all(); build OpenAPIToolset from spec_str/spec_dict; URL fetch only if host allowlisted; apply auth and filters.
- Loader (tools/loader.py): support {use: mcp:<id>}, {use: mcp_group:<id>}, {use: openapi:<id>}, {use: openapi_group:<id>} when registries provided; keep existing function tools.
- AgentRegistry: resolve {use: registry:mcp:<id>} and {use: registry:openapi:<id>} when registries provided.

Validation & /lint
- validate_registry(cfg): unknown a2a/mcp/openapi ids, bad groups, duplicates, invalid headers/auth/filter types, URL not allowlisted.
- Server /lint returns normalized config + diagnostics.

Server QoL
- /schema, /graph; /runs/{id}/cancel; SSE keepalive (~15s comments). Optional health endpoints for MCP/A2A when deps present.

Testing
- Unit: schema parsing, registries lifecycle, loader resolution.
- Guarded integration (requires google-adk + mcp/openapi): toolset construction, filters, close_all; a2a remote agent creation.
- Keep current tests; add new ones alongside.

DX & docs
- Friendly import errors with install hints (MCP/OpenAPI/A2A).
- README: new config blocks + examples; templates for MCP/OpenAPI/A2A.

Phases
1) Schema models + validation helpers + docs.
2) McpRegistry + loader/agent-registry wiring + tests.
3) OpenAPIRegistry + URL allowlist fetch + tests.
4) A2A remote agent + tests.
5) /lint diagnostics + server QoL (SSE keepalive) + tests.
