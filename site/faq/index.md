# Frequently Asked Questions

Does this library include a server?

- No. It is programmatic-only. If you need a hosted API, use google-adk-extras to build a FastAPI app and wire your agents.

Do I need google-adk-extras?

- Yes for most storage/IO backends (Redis, Mongo, SQL, S3, local folders, YAML). It is a dependency of this package and gets installed automatically, but you still need to configure your URIs/secrets.

How do I connect to MCP or OpenAPI toolsets?

- MCP and OpenAPI adapters come from ADK. This library builds and caches toolsets. Ensure the corresponding ADK components are installed and available.

Can I fetch OpenAPI specs by URL?

- Yes via OpenAPIRegistry only, and only when the hostname is allowlisted to avoid surprises. Inline/path specs are always supported.

Can I enumerate agents/tools without building a Runner?

- Yes. Use registries and their `list_*` helpers.
