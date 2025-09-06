from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..config.models import AppConfig


def _sys_dir(root: Path, name: str) -> Path:
    return (root / name).resolve()


def save_system(cfg: AppConfig, *, name: str, version: str, root: str | Path = "registry") -> Path:
    """Save a system config under registry/<name>/<version>/config.yaml.

    Returns the path to the saved config file.
    """
    import yaml

    rootp = Path(root).resolve()
    target = _sys_dir(rootp, name) / version
    target.mkdir(parents=True, exist_ok=True)
    cfg_path = target / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg.model_dump(), sort_keys=False), encoding="utf-8")
    # write manifest
    manifest = {
        "name": name,
        "version": version,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return cfg_path


def list_systems(*, root: str | Path = "registry") -> List[str]:
    """List system names available under the registry root."""
    rootp = Path(root).resolve()
    if not rootp.exists():
        return []
    return sorted([p.name for p in rootp.iterdir() if p.is_dir()])


def list_versions(name: str, *, root: str | Path = "registry") -> List[str]:
    """List versions/tags available for a given system name."""
    base = _sys_dir(Path(root).resolve(), name)
    if not base.exists():
        return []
    return sorted([p.name for p in base.iterdir() if p.is_dir()])


def load_system(name: str, version: str, *, root: str | Path = "registry") -> AppConfig:
    """Load a saved AppConfig for system/version from the filesystem registry."""

    cfg_path = _sys_dir(Path(root).resolve(), name) / version / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(str(cfg_path))
    from ..config.models import load_config_file

    return load_config_file(cfg_path)


def promote(name: str, version: str, tag: str, *, root: str | Path = "registry") -> Path:
    """Create/update a tag (alias) as a copy of the version directory."""
    base = _sys_dir(Path(root).resolve(), name)
    src = base / version
    if not src.exists():
        raise FileNotFoundError(str(src))
    dst = base / tag
    # Remove old tag if exists, then copytree
    import shutil

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst
