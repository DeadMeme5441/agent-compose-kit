import importlib.util

import pytest

from agent_compose_kit.services.factory import (
    build_artifact_service,
    build_memory_service,
    build_session_service,
)


def _has_extras() -> bool:
    return importlib.util.find_spec("google_adk_extras") is not None


def _name(obj) -> str:
    return obj.__class__.__name__


@pytest.mark.parametrize(
    "uri,expect",
    [
        ("sqlite:///./x.db", "SQLSessionService"),
        ("postgresql://user@localhost/db", "SQLSessionService"),
        ("redis://localhost:6379/0", "RedisSessionService"),
        ("mongodb://localhost/adk", "MongoSessionService"),
        ("yaml://./sessions", "YamlFileSessionService"),
        ("memory:", "InMemorySessionService"),
    ],
)
def test_session_service_uri_parsing(uri: str, expect: str):
    if not _has_extras() and expect not in {"InMemorySessionService"}:
        pytest.skip("extras not installed")
    svc = build_session_service(uri)
    # When extras are missing, conservative default is in-memory
    if not _has_extras() and expect != "InMemorySessionService":
        assert _name(svc) == "InMemorySessionService"
    else:
        assert expect in _name(svc)


@pytest.mark.parametrize(
    "uri,expect",
    [
        ("file://./artifacts", "LocalFolderArtifactService"),
        ("s3://my-bucket/prefix", "S3ArtifactService"),
        ("mongodb://localhost/adk_artifacts", "MongoArtifactService"),
        ("sqlite:///./a.db", "SQLArtifactService"),
    ],
)
def test_artifact_service_uri_parsing(uri: str, expect: str):
    if not _has_extras():
        pytest.skip("extras not installed")
    art = build_artifact_service(uri)
    assert expect in _name(art)


@pytest.mark.parametrize(
    "uri,expect",
    [
        ("memory:", "InMemoryMemoryService"),
        ("redis://localhost:6379/0", "RedisMemoryService"),
        ("mongodb://localhost/adk_memory", "MongoMemoryService"),
        ("sqlite:///./m.db", "SQLMemoryService"),
        ("yaml://./mem", "YamlFileMemoryService"),
    ],
)
def test_memory_service_uri_parsing(uri: str, expect: str):
    if not _has_extras() and expect not in {"InMemoryMemoryService"}:
        pytest.skip("extras not installed")
    mem = build_memory_service(uri)
    if not _has_extras() and expect != "InMemoryMemoryService":
        assert _name(mem) == "InMemoryMemoryService"
    else:
        assert expect in _name(mem)

