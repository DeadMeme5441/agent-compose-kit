---
title: Graph
---

# Graph Builder

`compose.build_system_graph(cfg)` returns `{ nodes, edges, hints }` describing the agent/tool topology.

Nodes include:
- `agent.llm`, `agent.workflow.sequential`, `agent.workflow.parallel`, `agent.workflow.loop`, `agent.custom`
- `tool.function`, `tool.mcp`, `tool.openapi`, `tool.agent`
- `tool.openapi_toolset`, `tool.mcp_toolset`, `tool.apihub_toolset`, `tool.builtin:<name>`
- `agent.registry` for referenced registry agents

Edges:
- `llm -> tool.*` (attached tools)
- `llm -> agent.*` (sub_agents)
- `sequential`: ordered flow `a -> b`
- `parallel`: fan-out from the parallel node
- `loop`: loop node -> each sub_agent

Hints:
- LLM missing `model` and no `defaults.model_alias`
- LLM with `output_schema` + tools (runtime disables tools)
- `sequential` upstream LLM missing `output_key`
- `planner: plan_react` combined with `output_schema` (conflict)
- `thinking_config` under `generate_content_config` (suggest moving to `planner.built_in`)
- Unknown sub_agent references

