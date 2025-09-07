---
title: Tools
---

# Tools

Function tools
```yaml
agents:
  - name: calc
    model: gemini-2.0-flash
    tools:
      - {type: function, ref: tests.helpers:sample_tool, name: add}
```

MCP toolsets (stdio/SSE/HTTP)
```yaml
toolsets:
  fs_tools:
    type: mcp
    mode: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./sandbox"]
    tool_filter: [list_directory, read_file]
```

OpenAPI toolsets
```yaml
agents:
  - name: api_caller
    model: gemini-2.0-flash
    tools:
      - type: openapi
        spec: {path: ./specs/petstore.yaml}
        # spec_type inferred from extension; or set explicitly: json|yaml
```

Registry references in tools
```yaml
agents:
  - name: rich_tools
    model: gemini-2.0-flash
    tools:
      - {use: 'mcp:files'}
      - {use: 'openapi:petstore'}
```

Notes
- MCP/OpenAPI support requires corresponding ADK components; imports are guarded.
- OpenAPI via URL requires allowlisted host in openapi_registry; inline/path supported directly.

