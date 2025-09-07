# Agents

LlmAgent from string model

```
agents:
  - name: planner
    model: gemini-2.0-flash
    instruction: Plan tasks and call tools.
```

LiteLLM model mapping with provider defaults

```
model_providers:
  openai:
    api_key: ${OPENAI_API_KEY}

agents:
  - name: planner
    model:
      type: litellm
      model: openai/gpt-4o-mini
```

Sub-agents & workflows

```
agents:
  - name: a
    model: gemini-2.0-flash
  - name: b
    model: gemini-2.0-flash
    sub_agents: [a]

workflow: {type: sequential, nodes: [a, b]}
```

A2A remote agents (agent cards)

```
a2a_clients:
  - id: remote
    agent_card_url: https://host:8000/a2a/hello/.well-known/agent-card.json

agents:
  - name: remote
    kind: a2a_remote
    client: remote
```

Notes

- A2A prefers agent cards (AgentCard or URL). The legacy `url` field is still accepted but is treated as a card URL.
- Advanced options (planner, code executor, structured schemas) are optional and guarded.
