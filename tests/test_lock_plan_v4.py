from agent_compose_kit.config.models import load_config
from agent_compose_kit.lock import plan_lock


def test_plan_lock_from_appconfig_and_raw_dict():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "defaults": {"model_alias": "chat-default"},
        "agents": [
            {
                "type": "llm",
                "name": "a",
                "instruction": "i",
                "tools": [
                    {
                        "kind": "mcp",
                        "server": {"ref": {"value": "registry://mcp/files@latest"}},
                        "tool": "read_file",
                    },
                    {
                        "kind": "openapi",
                        "spec": {"ref": {"value": "registry://openapi/petstore@1"}},
                        "operationId": "getPet",
                    },
                ],
            },
            {
                "type": "llm",
                "name": "b",
                "instruction": "i",
                "sub_agents": [
                    {"value": "registry://agent/helper@>=0.2", "kind": "agent", "key": "helper", "version": ">=0.2"}
                ],
            },
        ],
    }

    def reg_resolve(kind: str, key: str, rng: str):
        if (kind, key, rng) == ("mcp", "files", "latest"):
            return {"version": "1.2.3", "etag": "abc", "uri": "https://ex/files@1.2.3"}
        if (kind, key, rng) == ("openapi", "petstore", "1"):
            return {"version": "1", "uri": "file://petstore.yaml"}
        if (kind, key, rng) == ("agent", "helper", ">=0.2"):
            return {"version": "0.3.0"}
        return {}

    def alias_resolve(alias: str):
        if alias == "chat-default":
            return {"provider": "openai", "model": "gpt-4o-mini", "secret_ref": "env:OPENAI_API_KEY"}
        return {}

    # From AppConfig
    cfg = load_config(raw)
    plan = plan_lock(cfg, reg_resolve, alias_resolve)
    kinds = [p.kind for p in plan.registryPins]
    assert set(kinds) == {"agent", "mcp", "openapi"}
    assert any(p.kind == "mcp" and p.pinned == "1.2.3" for p in plan.registryPins)
    assert any(a.alias == "chat-default" and a.model == "gpt-4o-mini" for a in plan.aliasPins)

    # From raw dict
    plan2 = plan_lock(raw, reg_resolve, alias_resolve)
    assert len(plan2.registryPins) == len(plan.registryPins)

