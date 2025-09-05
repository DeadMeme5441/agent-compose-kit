from pathlib import Path

from agent_compose_kit.config.models import AppConfig, RuntimeConfig
from agent_compose_kit.runtime.supervisor import build_run_config


def test_run_config_mapping_defaults():
    cfg = AppConfig(runtime=RuntimeConfig(streaming_mode="SSE", max_llm_calls=123, save_input_blobs_as_artifacts=True))
    rc = build_run_config(cfg)
    # rc is an ADK RunConfig; check key properties via getattr to avoid import here
    assert getattr(rc, "max_llm_calls") == 123
    assert getattr(rc, "save_input_blobs_as_artifacts") is True
    # streaming_mode is enum; ensure it's set (not None)
    assert getattr(rc, "streaming_mode") is not None
