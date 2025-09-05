from __future__ import annotations

from pathlib import Path
from typing import Optional


AGENT_WRAPPER_TEMPLATE = """\
from pathlib import Path
from {pkg}.config.models import load_config_file
from {pkg}.tools.builders import build_tool_registry_from_config
from {pkg}.agents.builders_registry import build_agent_registry_from_config

CFG_PATH = Path(__file__).parent / "config.yaml"
cfg = load_config_file(CFG_PATH)
tool_reg = build_tool_registry_from_config(cfg, base_dir=CFG_PATH.parent)
agent_reg = build_agent_registry_from_config(
    cfg, base_dir=CFG_PATH.parent, provider_defaults=cfg.model_providers, tool_registry=tool_reg
)
# Select your root agent (by id or group)
root_agent = agent_reg.get("parent") if cfg.agents_registry else agent_reg.get_group("core")[0]
"""


APP_PY_TEMPLATE = """\
import os
from google.adk.cli.fast_api import get_fast_api_app

AGENTS_DIR = os.environ.get("AGENTS_DIR", "{agents_dir}")

# Optional URIs: set via env if desired
SESSION_SERVICE_URI = os.environ.get("SESSION_SERVICE_URI")  # e.g., sqlite:///./sessions.db
ARTIFACT_SERVICE_URI = os.environ.get("ARTIFACT_SERVICE_URI")  # e.g., gs://my-bucket
MEMORY_SERVICE_URI = os.environ.get("MEMORY_SERVICE_URI")
EVAL_STORAGE_URI = os.environ.get("EVAL_STORAGE_URI")
ALLOW_ORIGINS = os.environ.get("ALLOW_ORIGINS")

app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    artifact_service_uri=ARTIFACT_SERVICE_URI,
    memory_service_uri=MEMORY_SERVICE_URI,
    eval_storage_uri=EVAL_STORAGE_URI,
    allow_origins=ALLOW_ORIGINS.split(",") if ALLOW_ORIGINS else None,
    web=True,
    a2a=False,
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8000")),
)
"""


DOCKERFILE_TEMPLATE = """\
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies (assumes published package name is {dist})
RUN pip install --no-cache-dir google-adk[web] uvicorn {dist}

# Copy agents dir and server app
COPY agents /app/agents
COPY app.py /app/app.py

ENV AGENTS_DIR=/app/agents
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def write_adk_wrapper(
    *,
    agents_dir: Path,
    system_name: str,
    config_path: Path,
    package_import: str = "agent_compose_kit",
    copy_config: bool = True,
) -> Path:
    """Create agents_dir/<system_name>/agent.py that exposes root_agent built from YAML.

    - package_import: base import path for this library (use "src" for local dev).
    - copy_config: when True, copy the YAML to the wrapper folder as config.yaml.
    Returns the created folder path.
    """
    agents_dir = agents_dir.resolve()
    sys_dir = agents_dir / system_name
    sys_dir.mkdir(parents=True, exist_ok=True)
    agent_py = sys_dir / "agent.py"
    agent_py.write_text(AGENT_WRAPPER_TEMPLATE.format(pkg=package_import), encoding="utf-8")
    if copy_config:
        target_cfg = sys_dir / "config.yaml"
        target_cfg.write_text(Path(config_path).read_text(encoding="utf-8"), encoding="utf-8")
    return sys_dir


def write_fastapi_app_py(*, output_dir: Path, agents_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    app_py = output_dir / "app.py"
    app_py.write_text(APP_PY_TEMPLATE.format(agents_dir=str(agents_dir.resolve())), encoding="utf-8")
    return app_py


def write_docker_scaffold(*, output_dir: Path, dist_name: str = "agent-compose-kit") -> Path:
    output_dir = output_dir.resolve()
    dockerfile = output_dir / "Dockerfile"
    dockerfile.write_text(DOCKERFILE_TEMPLATE.format(dist=dist_name), encoding="utf-8")
    return dockerfile

