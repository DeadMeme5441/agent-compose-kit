---
title: Agents
---

# Agents

Variants:
- `llm` — language-centric agent, can call tools and delegate
- `workflow.sequential` — run sub_agents in order
- `workflow.parallel` — fan-out to sub_agents
- `workflow.loop` — iterate sub_agents up to `max_iterations` or early exit
- `custom` — visualization-only declaration of a bespoke agent class

LLM agent fields (subset):
- `name`, `instruction` (required)
- `model: string | alias://name`
- `tools: Tool[]` (see Tools)
- `sub_agents: (string | RegistryRef)[]`
- `include_contents: 'default'|'none'`
- `input_schema`, `output_schema`: dotted refs to Pydantic models
- `output_key`: pass values to downstream steps
- `planner`: `{ type: 'built_in', thinking_config: {...} } | { type: 'plan_react' }`
- `code_executor`: dotted ref
- callbacks: before/after model/tool
- delegation flags: `disallow_transfer_to_parent`, `disallow_transfer_to_peers`

Workflows:
- Sequential connects consecutive sub_agents
- Parallel fans out from the workflow node to each sub_agent
- Loop connects loop → each sub_agent (iteration is a runtime concern)

