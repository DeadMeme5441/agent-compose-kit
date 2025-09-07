"""
Function tools exposed to the main agent.

These are intentionally conservative (read/search/plan/validate/graph);
write operations will be added later behind explicit approvals.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def list_paths(glob: str = "**/*", base_dir: str | None = None, limit: int = 500) -> List[str]:
    """List project files using a glob (non-hidden by default).

    - glob: a glob pattern like "**/*.py"
    - base_dir: base directory; defaults to repo root (cwd)
    - limit: max entries to return
    """
    root = Path(base_dir or ".").resolve()
    results: List[str] = []
    for p in root.glob(glob):
        # skip directories, venvs, node_modules, .git
        if p.is_dir():
            continue
        rel = str(p.relative_to(root))
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in p.parts):
            continue
        results.append(rel)
        if len(results) >= limit:
            break
    return results


def read_text(path: str, max_bytes: int = 20000) -> str:
    """Read a text file up to max_bytes.

    Returns a best-effort UTF-8 decode; truncates if too large.
    """
    p = Path(path)
    data = p.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return data.decode(errors="replace")


def search_text(query: str, base_dir: str | None = None, exts: list[str] | None = None, limit: int = 200) -> List[str]:
    """Very simple text search across files.

    - query: substring to search for (case-insensitive)
    - base_dir: directory to search
    - exts: if provided, only include files with these suffixes (e.g., [".py", ".md"]) 
    - limit: cap results

    Returns list of lines formatted as: 'path:line_no: line contents'.
    """
    root = Path(base_dir or ".").resolve()
    q = query.lower()
    out: List[str] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in p.parts):
            continue
        if exts and p.suffix not in exts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if q in line.lower():
                out.append(f"{p.relative_to(root)}:{i}: {line}")
                if len(out) >= limit:
                    return out
    return out


def validate_flow(config_path: str = "configs/app.yaml") -> str:
    from ..config.models import load_config_file

    _ = load_config_file(Path(config_path))
    return "Config OK"


def plan_flow(config_path: str = "configs/app.yaml") -> str:
    from ..config.models import load_config_file
    from ..runtime.supervisor import build_plan

    cfg = load_config_file(Path(config_path))
    return build_plan(cfg)


def graph_flow(config_path: str = "configs/app.yaml", dot: bool = False) -> str:
    from ..config.models import load_config_file

    # Reproduce ASCII or DOT graph text similar to CLI
    cfg = load_config_file(Path(config_path))
    agent_names = [a.name for a in cfg.agents]
    edges: list[tuple[str, str]] = []
    subs = {a.name: a.sub_agents for a in cfg.agents}
    for a, children in subs.items():
        for c in children:
            edges.append((a, c))
    if cfg.workflow and cfg.workflow.nodes:
        n = cfg.workflow.nodes
        if cfg.workflow.type == "sequential":
            for i in range(len(n) - 1):
                edges.append((n[i], n[i + 1]))
        elif cfg.workflow.type == "parallel":
            for i in range(1, len(n)):
                edges.append((n[0], n[i]))
        elif cfg.workflow.type == "loop":
            for i in range(len(n)):
                edges.append((n[i], n[(i + 1) % len(n)]))
    if dot:
        lines = ["digraph flow {"]
        lines += [f'  "{a}";' for a in agent_names]
        lines += [f'  "{s}" -> "{d}";' for s, d in edges]
        lines.append("}")
        return "\n".join(lines)
    lines = [f"{s} -> {d}" for s, d in edges]
    return "\n".join(lines) if lines else "(no edges)"
