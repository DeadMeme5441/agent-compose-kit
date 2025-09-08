from agent_compose_kit.config.models import load_config
from agent_compose_kit.registries.aliases import validate_aliases
from agent_compose_kit.lock import plan_lock
from agent_compose_kit.quickfix import get_quick_fixes


def test_model_alias_registry_parse_and_validate():
    cfg = load_config(
        {
            "schema_version": "0.1.0",
            "metadata": {"name": "demo"},
            "model_aliases": {
                "aliases": [
                    {"id": "chat-default", "resolver": "direct", "model": "gemini-2.0-flash", "provider": "gemini"},
                    {"id": "gpt-mini", "resolver": "litellm", "model": "openai/gpt-4o-mini", "auth_ref": "env:OPENAI_API_KEY", "params": {"api_base": "https://api.openai.com"}},
                    {"id": "claude-vertex", "resolver": "class", "model": "claude-3-7-sonnet@20250219", "class_ref": "google.adk.models.anthropic_llm:Claude"},
                ]
            },
            "agents": [
                {"type": "llm", "name": "a", "instruction": "i", "model": "alias://chat-default"}
            ],
        }
    )
    raw = cfg.model_dump()
    v = validate_aliases(raw)
    assert v["unknown_aliases"] == []


def test_unknown_aliases_yield_quickfix():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "defaults": {"model_alias": "chat-default"},
        "agents": [
            {"type": "llm", "name": "a", "instruction": "i", "model": "alias://missing"}
        ],
    }
    fixes = get_quick_fixes(raw_cfg=raw)
    ids = [f.id for f in fixes]
    assert "add-alias-chat-default" in ids
    assert "add-alias-missing" in ids


def test_plan_lock_alias_pin_extended():
    raw = {
        "schema_version": "0.1.0",
        "metadata": {"name": "demo"},
        "defaults": {"model_alias": "chat-default"},
        "agents": [
            {"type": "llm", "name": "a", "instruction": "i", "model": "alias://chat-default"}
        ],
    }

    def alias_resolve(alias: str):
        if alias == "chat-default":
            return {
                "provider": "openai",
                "model": "openai/gpt-4o-mini",
                "resolver": "litellm",
                "secret_ref": "env:OPENAI_API_KEY",
                "params": {"api_base": "https://api.openai.com"},
            }
        return {}

    def reg_resolve(kind, key, rng):
        return {}

    cfg = load_config(raw)
    plan = plan_lock(cfg, reg_resolve, alias_resolve)
    ap = plan.aliasPins[0]
    assert ap.resolver == "litellm"
    assert ap.params_fingerprint is not None and len(ap.params_fingerprint) == 64

