import importlib
import pytest


def test_get_app_importable():
    # FastAPI may not be installed in test env; skip if missing
    try:
        import fastapi  # noqa: F401
    except Exception:
        pytest.skip("fastapi not installed")
    mod = importlib.import_module("agent_compose_kit.server.app")
    app = mod.get_app()
    # basic shape
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)
