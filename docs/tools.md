---
title: Tools
---

# Tools

Supported kinds (aligned with ADK):
- Function: `{ kind: 'function', function: RefOrInline|{import|code, deps?}, signature?, policy?, long_running? }`
- MCP: `{ kind: 'mcp', server: RefOrInline<mcp server>, tool: string, config?, auth_config? }`
- OpenAPI: `{ kind: 'openapi', spec: RefOrInline<openapi spec>, operationId: string, parameters?, body?, headers?, auth_config? }`
- Agent: `{ kind: 'agent', agent: string|RegistryRef }`
- OpenAPI toolset: `{ kind: 'openapi_toolset', spec: RefOrInline, auth_config?, tool_filter? }`
- MCP toolset: `{ kind: 'mcp_toolset', server: RefOrInline, auth_config?, tool_filter? }`
- API Hub toolset: `{ kind: 'apihub_toolset', apihub_resource_name: string, auth_config?, tool_filter?, name?, description? }`
- Built-in: `{ kind: 'builtin', name: 'vertex_ai_search'|'url_context'|'google_search'|'code_execution'|'bigquery_toolset'|'spanner_toolset'|'retrieval', params? }`

Auth config:
- `auth_config: { auth_scheme: string, auth_credential?, params? }`

Notes:
- `long_running: true` on function tools maps to ADK LongRunningFunctionTool.
- Toolsets model dynamic providers (they yield many ADK tools at runtime).

