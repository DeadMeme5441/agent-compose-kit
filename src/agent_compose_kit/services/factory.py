from __future__ import annotations

from typing import Any

from ..config.models import ArtifactServiceConfig, MemoryServiceConfig, SessionServiceConfig


def build_session_service(cfg: SessionServiceConfig):
    """Construct and return a SessionService implementation.

    Behavior:
    - in_memory → InMemorySessionService
    - redis → RedisSessionService when `redis_url` provided, else fall back to InMemory
    - mongo → MongoSessionService when `mongo_url` provided, else fall back to InMemory
    - database|db → DatabaseSessionService when `db_url` provided, else fall back to InMemory

    Optional dependencies are imported lazily and guarded. When required
    parameters are missing, the function conservatively returns an in-memory
    implementation to avoid surprise external calls.
    """
    t = cfg.type
    if t == "in_memory":
        from google.adk.sessions import InMemorySessionService  # type: ignore

        return InMemorySessionService()
    if t == "redis":
        if not cfg.redis_url:
            from google.adk.sessions import InMemorySessionService  # type: ignore

            return InMemorySessionService()
        from adk_extra_services.sessions import RedisSessionService  # type: ignore

        return RedisSessionService(redis_url=cfg.redis_url)
    if t == "mongo":
        if not cfg.mongo_url:
            from google.adk.sessions import InMemorySessionService  # type: ignore

            return InMemorySessionService()
        from adk_extra_services.sessions import MongoSessionService  # type: ignore

        return MongoSessionService(mongo_url=cfg.mongo_url, db_name=cfg.db_name or "adk")
    if t in {"db", "database"}:
        # DatabaseSessionService supports SQLAlchemy URLs like sqlite:///./file.db
        from google.adk.sessions import DatabaseSessionService, InMemorySessionService  # type: ignore

        db_url = cfg.db_url or (cfg.params.get("db_url") if cfg.params else None)
        if not db_url:
            return InMemorySessionService()
        return DatabaseSessionService(db_url=db_url)
    # stubs for vertex_ai, db
    raise NotImplementedError(f"Unsupported session service type: {t}")


def build_artifact_service(cfg: ArtifactServiceConfig):
    """Construct and return an ArtifactService implementation.

    Behavior:
    - in_memory → InMemoryArtifactService
    - local_folder → LocalFolderArtifactService when `base_path` provided, else InMemory
    - s3 → S3ArtifactService when `bucket_name` provided, else InMemory
    - gcs → GcsArtifactService when `bucket_name` provided, else InMemory

    Optional dependencies are imported lazily and guarded.
    """
    t = cfg.type
    if t == "in_memory":
        from google.adk.artifacts import InMemoryArtifactService  # type: ignore

        return InMemoryArtifactService()
    if t == "local_folder":
        if not cfg.base_path:
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from adk_extra_services.artifacts import LocalFolderArtifactService  # type: ignore

        return LocalFolderArtifactService(base_path=cfg.base_path)
    if t == "s3":
        if not cfg.bucket_name:
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from adk_extra_services.artifacts import S3ArtifactService  # type: ignore

        return S3ArtifactService(
            bucket_name=cfg.bucket_name,
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.aws_access_key_id,
            aws_secret_access_key=cfg.aws_secret_access_key,
            region_name=cfg.region_name,
        )
    if t == "gcs":
        if not cfg.bucket_name:
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from google.adk.artifacts import GcsArtifactService  # type: ignore

        return GcsArtifactService(bucket_name=cfg.bucket_name)
    raise NotImplementedError(f"Unsupported artifact service type: {t}")


def build_memory_service(cfg: MemoryServiceConfig | None):
    """Construct and return a MemoryService implementation or None.

    Behavior:
    - None or type None → returns None (memory optional)
    - in_memory → InMemoryMemoryService
    - vertex_ai → VertexAiMemoryBankService when required params are present
      (project, location, agent_engine_id); otherwise falls back to in-memory.
    """
    if cfg is None or cfg.type is None:
        return None
    if cfg.type == "in_memory":
        from google.adk.memory import InMemoryMemoryService  # type: ignore

        return InMemoryMemoryService()
    if cfg.type == "vertex_ai":
        from google.adk.memory import InMemoryMemoryService  # type: ignore

        # If required params are not present, fall back conservatively
        params: dict[str, Any] = dict(cfg.params or {})
        if not (params.get("project") and params.get("location") and params.get("agent_engine_id")):
            return InMemoryMemoryService()
        from google.adk.memory import VertexAiMemoryBankService  # type: ignore

        return VertexAiMemoryBankService(
            project=params.get("project"),
            location=params.get("location"),
            agent_engine_id=params.get("agent_engine_id"),
        )
    raise NotImplementedError(f"Unsupported memory service type: {cfg.type}")
