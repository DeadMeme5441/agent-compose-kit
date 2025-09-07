from __future__ import annotations

from urllib.parse import urlparse

from ..config.models import (
    ArtifactServiceConfig,
    MemoryServiceConfig,
    SessionServiceConfig,
    parse_service_uri,
)


def build_session_service(cfg: SessionServiceConfig | str):
    """Construct and return a SessionService implementation.

    Behavior:
    - in_memory → google.adk InMemorySessionService
    - redis → google-adk-extras RedisSessionService (host/port/db/password or redis_url)
    - mongo → google-adk-extras MongoSessionService (mongo_url, db_name)
    - sql|database|db → google-adk-extras SQLSessionService (db_url)
    - yaml_file → google-adk-extras YamlFileSessionService (base_path)

    Optional dependencies are imported lazily and guarded. When required
    parameters are missing, the function conservatively returns an in-memory
    implementation to avoid surprise external calls.
    """
    if isinstance(cfg, str):
        cfg = parse_service_uri("session", cfg)  # type: ignore[assignment]
    t = cfg.type
    if t == "in_memory":
        from google.adk.sessions import InMemorySessionService  # type: ignore

        return InMemorySessionService()
    if t == "redis":
        host = cfg.redis_host
        port = cfg.redis_port
        db = cfg.redis_db
        password = cfg.redis_password
        if cfg.redis_url and not host:
            # Parse redis://[:password@]host:port/db
            u = urlparse(cfg.redis_url)
            host = u.hostname or host
            port = u.port or port
            if u.path and len(u.path) > 1:
                try:
                    db = int(u.path.lstrip("/"))
                except ValueError:
                    db = db
            if u.password:
                password = u.password
        if not host:
            from google.adk.sessions import InMemorySessionService  # type: ignore

            return InMemorySessionService()
        from google_adk_extras.sessions import (  # type: ignore
            RedisSessionService,
        )

        return RedisSessionService(host=host, port=port or 6379, db=db or 0, password=password)
    if t == "mongo":
        if not cfg.mongo_url:
            from google.adk.sessions import InMemorySessionService  # type: ignore

            return InMemorySessionService()
        from google_adk_extras.sessions import (  # type: ignore
            MongoSessionService,
        )

        return MongoSessionService(connection_string=cfg.mongo_url, database_name=cfg.db_name or "adk_sessions")
    if t in {"db", "database", "sql"}:
        # SQL-backed sessions via extras
        from google.adk.sessions import InMemorySessionService  # type: ignore
        from google_adk_extras.sessions import SQLSessionService  # type: ignore

        db_url = cfg.db_url or (cfg.params.get("db_url") if cfg.params else None)
        if not db_url:
            return InMemorySessionService()
        return SQLSessionService(database_url=db_url)
    if t == "yaml_file":
        from google.adk.sessions import InMemorySessionService  # type: ignore
        from google_adk_extras.sessions import YamlFileSessionService  # type: ignore

        base = cfg.base_path or (cfg.params.get("base_path") if cfg.params else None)
        if not base:
            return InMemorySessionService()
        return YamlFileSessionService(base_directory=base)
    # stubs for vertex_ai, db
    raise NotImplementedError(f"Unsupported session service type: {t}")


def build_artifact_service(cfg: ArtifactServiceConfig | str):
    """Construct and return an ArtifactService implementation.

    Behavior:
    - in_memory → google.adk InMemoryArtifactService
    - local_folder → google-adk-extras LocalFolderArtifactService when `base_path` provided, else InMemory
    - s3 → google-adk-extras S3ArtifactService when `bucket_name` provided, else InMemory
    - mongo → google-adk-extras MongoArtifactService (mongo_url, db_name)
    - sql → google-adk-extras SQLArtifactService (db_url)

    Optional dependencies are imported lazily and guarded.
    """
    if isinstance(cfg, str):
        cfg = parse_service_uri("artifact", cfg)  # type: ignore[assignment]
    t = cfg.type
    if t == "in_memory":
        from google.adk.artifacts import InMemoryArtifactService  # type: ignore

        return InMemoryArtifactService()
    if t == "local_folder":
        if not cfg.base_path:
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from google_adk_extras.artifacts import (  # type: ignore
            LocalFolderArtifactService,
        )

        return LocalFolderArtifactService(base_directory=str(cfg.base_path))
    if t == "s3":
        if not cfg.bucket_name:
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from google_adk_extras.artifacts import S3ArtifactService  # type: ignore

        return S3ArtifactService(
            bucket_name=cfg.bucket_name,
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.aws_access_key_id,
            aws_secret_access_key=cfg.aws_secret_access_key,
            region_name=cfg.region_name,
            prefix=(cfg.s3_prefix or (cfg.params.get("prefix") if cfg.params else None) or "adk-artifacts"),
        )
    if t == "mongo":
        if not (cfg.mongo_url and cfg.db_name):
            from google.adk.artifacts import InMemoryArtifactService  # type: ignore

            return InMemoryArtifactService()
        from google_adk_extras.artifacts import MongoArtifactService  # type: ignore

        return MongoArtifactService(connection_string=cfg.mongo_url, database_name=cfg.db_name)
    if t == "sql":
        from google.adk.artifacts import InMemoryArtifactService  # type: ignore
        from google_adk_extras.artifacts import SQLArtifactService  # type: ignore

        db_url = cfg.db_url or (cfg.params.get("db_url") if cfg.params else None)
        if not db_url:
            return InMemoryArtifactService()
        return SQLArtifactService(database_url=db_url)
    raise NotImplementedError(f"Unsupported artifact service type: {t}")


def build_memory_service(cfg: MemoryServiceConfig | str | None):
    """Construct and return a MemoryService implementation or None.

    Behavior:
    - None or type None → returns None (memory optional)
    - in_memory → google.adk InMemoryMemoryService
    - redis → google-adk-extras RedisMemoryService
    - mongo → google-adk-extras MongoMemoryService
    - sql → google-adk-extras SQLMemoryService
    - yaml_file → google-adk-extras YamlFileMemoryService
    - No Vertex AI memory support (removed)
    """
    if cfg is None:
        return None
    if isinstance(cfg, str):
        cfg = parse_service_uri("memory", cfg)  # type: ignore[assignment]
    if cfg.type is None:
        return None
    if cfg.type == "in_memory":
        from google.adk.memory import InMemoryMemoryService  # type: ignore

        return InMemoryMemoryService()
    if cfg.type == "redis":
        from google.adk.memory import InMemoryMemoryService  # type: ignore
        from google_adk_extras.memory import RedisMemoryService  # type: ignore

        host = cfg.redis_host or (cfg.params.get("host") if cfg.params else None)
        port = cfg.redis_port or (cfg.params.get("port") if cfg.params else None)
        db = cfg.redis_db or (cfg.params.get("db") if cfg.params else None)
        if not host:
            return InMemoryMemoryService()
        return RedisMemoryService(host=host, port=port or 6379, db=db or 0)
    if cfg.type == "mongo":
        from google.adk.memory import InMemoryMemoryService  # type: ignore
        from google_adk_extras.memory import MongoMemoryService  # type: ignore

        if not cfg.mongo_url:
            return InMemoryMemoryService()
        return MongoMemoryService(connection_string=cfg.mongo_url, database_name=cfg.db_name or "adk_memory")
    if cfg.type in {"sql"}:
        from google.adk.memory import InMemoryMemoryService  # type: ignore
        from google_adk_extras.memory import SQLMemoryService  # type: ignore

        db_url = cfg.db_url or (cfg.params.get("db_url") if cfg.params else None)
        if not db_url:
            return InMemoryMemoryService()
        return SQLMemoryService(database_url=db_url)
    if cfg.type == "yaml_file":
        from google.adk.memory import InMemoryMemoryService  # type: ignore
        from google_adk_extras.memory import YamlFileMemoryService  # type: ignore

        base = cfg.base_path or (cfg.params.get("base_path") if cfg.params else None)
        if not base:
            return InMemoryMemoryService()
        return YamlFileMemoryService(base_directory=base)
    raise NotImplementedError(f"Unsupported memory service type: {cfg.type}")
