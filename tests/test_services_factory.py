"""Unit tests for service factory behavior.

These tests assert conservative defaults (in-memory when config is incomplete)
and successful instantiation when required parameters are provided.
"""

import importlib.util
import pytest

from src.config.models import ArtifactServiceConfig, MemoryServiceConfig, SessionServiceConfig
from src.services.factory import build_artifact_service, build_memory_service, build_session_service


def _cls_name(obj) -> str:
    return obj.__class__.__name__


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def test_session_in_memory_default():
    svc = build_session_service(SessionServiceConfig(type="in_memory"))
    assert _cls_name(svc) == "InMemorySessionService"


def test_session_redis_fallback_to_memory_when_missing_url():
    svc = build_session_service(SessionServiceConfig(type="redis"))
    assert _cls_name(svc) == "InMemorySessionService"


def test_session_redis_with_url_instantiates():
    if not _has_module("adk_extra_services"):
        pytest.skip("adk-extra-services not installed")
    svc = build_session_service(SessionServiceConfig(type="redis", redis_url="redis://localhost:6379"))
    assert "RedisSessionService" in _cls_name(svc)


def test_session_mongo_fallback_to_memory_when_missing_url():
    svc = build_session_service(SessionServiceConfig(type="mongo"))
    assert _cls_name(svc) == "InMemorySessionService"


def test_session_mongo_with_url_instantiates():
    if not _has_module("adk_extra_services"):
        pytest.skip("adk-extra-services not installed")
    svc = build_session_service(SessionServiceConfig(type="mongo", mongo_url="mongodb://localhost:27017", db_name="adk"))
    assert "MongoSessionService" in _cls_name(svc)


def test_session_database_fallback_when_missing_db_url():
    svc = build_session_service(SessionServiceConfig(type="database"))
    assert _cls_name(svc) == "InMemorySessionService"


def test_session_database_with_db_url_instantiates():
    if not _has_module("google.adk"):
        pytest.skip("google-adk not installed")
    svc = build_session_service(SessionServiceConfig(type="database", db_url="sqlite:///./test.db"))
    assert "DatabaseSessionService" in _cls_name(svc)


def test_artifact_in_memory_default():
    art = build_artifact_service(ArtifactServiceConfig(type="in_memory"))
    assert _cls_name(art) == "InMemoryArtifactService"


def test_artifact_local_folder_fallback_when_missing_base_path():
    art = build_artifact_service(ArtifactServiceConfig(type="local_folder"))
    assert _cls_name(art) == "InMemoryArtifactService"


def test_artifact_local_folder_with_path_instantiates(tmp_path):
    if not _has_module("adk_extra_services"):
        pytest.skip("adk-extra-services not installed")
    art = build_artifact_service(ArtifactServiceConfig(type="local_folder", base_path=str(tmp_path)))
    assert "LocalFolderArtifactService" in _cls_name(art)


def test_artifact_s3_fallback_when_missing_bucket():
    art = build_artifact_service(ArtifactServiceConfig(type="s3"))
    assert _cls_name(art) == "InMemoryArtifactService"


def test_artifact_s3_with_bucket_instantiates():
    if not _has_module("adk_extra_services"):
        pytest.skip("adk-extra-services not installed")
    art = build_artifact_service(ArtifactServiceConfig(type="s3", bucket_name="my-bucket"))
    assert "S3ArtifactService" in _cls_name(art)


def test_artifact_gcs_fallback_when_missing_bucket():
    art = build_artifact_service(ArtifactServiceConfig(type="gcs"))
    assert _cls_name(art) == "InMemoryArtifactService"


def test_artifact_gcs_with_bucket_instantiates(monkeypatch):
    # Requires Google Cloud ADC; skip if not configured in environment
    import os

    if not _has_module("google.adk"):
        pytest.skip("google-adk not installed")
    if not (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
    ):
        pytest.skip("GCS ADC not configured; skipping instantiation test")
    art = build_artifact_service(ArtifactServiceConfig(type="gcs", bucket_name="adk-artifacts"))
    assert "GcsArtifactService" in _cls_name(art)


def test_memory_none_returns_none():
    assert build_memory_service(None) is None


def test_memory_in_memory():
    mem = build_memory_service(MemoryServiceConfig(type="in_memory"))
    assert _cls_name(mem) == "InMemoryMemoryService"


def test_memory_vertex_ai_fallback_when_missing_params():
    mem = build_memory_service(MemoryServiceConfig(type="vertex_ai", params={}))
    assert _cls_name(mem) == "InMemoryMemoryService"
