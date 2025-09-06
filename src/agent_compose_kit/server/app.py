from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional


def get_app():
    """Return a FastAPI app that exposes validate/run/stream endpoints.

    Endpoints:
    - GET /health → {ok: true}
    - POST /validate → {ok: true, plan: str}
    - POST /runs → {run_id, session_id}
    - GET /runs/{run_id}/events → SSE stream of ADK events

    Notes:
    - Builds services, registries, and a root agent named `root_agent`.
    - Applies `global_instruction` to the root agent when present.
    - FastAPI is an optional dependency (import guarded).
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import StreamingResponse
    except Exception as e:  # pragma: no cover - optional dep
        raise ImportError("FastAPI is required to use the server module") from e

    import yaml
    from pydantic import BaseModel

    from ..agents.builder import build_agents
    from ..agents.builders_registry import build_agent_registry_from_config
    from ..config.models import AppConfig, load_config_file, export_app_config_schema, validate_app_config
    from ..runtime.supervisor import build_plan, build_run_config
    from ..services.factory import (
        build_artifact_service,
        build_memory_service,
        build_session_service,
    )
    from ..tools.builders import build_tool_registry_from_config

    app = FastAPI(title="agent-compose-kit server", version="0.1.0")

    class ValidateRequest(BaseModel):
        config_path: Optional[str] = None
        config_inline: Optional[str] = None

    class RunRequest(BaseModel):
        user_id: str
        text: str
        session_id: Optional[str] = None
        config_path: Optional[str] = None
        config_inline: Optional[str] = None

    runs: Dict[str, Dict[str, Any]] = {}

    @app.get("/schema")
    def schema():
        """Return the AppConfig JSON schema for IDEs and tooling."""
        return export_app_config_schema()

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.post("/validate")
    def validate(req: Optional[ValidateRequest] = None, config_path: Optional[str] = None, config_inline: Optional[str] = None):
        cfg = _load_cfg(req=req, config_path=config_path, config_inline=config_inline)
        plan = build_plan(cfg)
        return {"ok": True, "plan": plan}

    @app.post("/lint")
    def lint(req: Optional[ValidateRequest] = None, config_path: Optional[str] = None, config_inline: Optional[str] = None):
        """Return normalized config and diagnostics for validation."""
        cfg = _load_cfg(req=req, config_path=config_path, config_inline=config_inline)
        diags = validate_app_config(cfg)
        return {"ok": len(diags) == 0, "diagnostics": diags, "config": cfg.model_dump(mode="json")}

    @app.post("/graph")
    def graph(req: Optional[ValidateRequest] = None, config_path: Optional[str] = None, config_inline: Optional[str] = None):
        """Return a simple graph representation (nodes/edges) of the system.

        Nodes include agents and groups; edges represent sub-agent wiring and workflow order.
        """
        cfg = _load_cfg(req=req, config_path=config_path, config_inline=config_inline)
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        # Agents (inline)
        agent_names = [a.name for a in (cfg.agents or [])]
        for a in (cfg.agents or []):
            nodes.append({"id": a.name, "label": a.name, "type": "agent"})
            # sub_agents
            for sub in a.sub_agents or []:
                if sub in agent_names:
                    edges.append({"source": a.name, "target": sub, "type": "sub"})

        # Groups (inline)
        for g in (cfg.groups or []):
            gid = f"group:{g.name}"
            nodes.append({"id": gid, "label": g.name, "type": "group"})
            for m in g.members:
                if m in agent_names:
                    edges.append({"source": gid, "target": m, "type": "member"})

        # Workflow (inline)
        if cfg.workflow and cfg.workflow.nodes:
            seq = cfg.workflow.nodes
            if cfg.workflow.type in (None, "sequential", "loop"):
                # connect sequentially
                for i in range(len(seq) - 1):
                    s, t = seq[i], seq[i + 1]
                    if s in agent_names and t in agent_names:
                        edges.append({"source": s, "target": t, "type": "flow"})
            elif cfg.workflow.type == "parallel":
                # connect virtual parallel node
                pid = "parallel"
                nodes.append({"id": pid, "label": "parallel", "type": "parallel"})
                for n in seq:
                    if n in agent_names:
                        edges.append({"source": pid, "target": n, "type": "flow"})

        # Agents registry (optional)
        ar = cfg.agents_registry or {}
        reg_agents = ar.get("agents") or []
        reg_groups = ar.get("groups") or []
        # index for quick existence checks
        reg_agent_ids: set[str] = set()
        for a in reg_agents:
            aid = str(a.get("id")) if a.get("id") else None
            if not aid:
                continue
            reg_agent_ids.add(aid)
            label = a.get("name") or aid
            nodes.append({"id": f"registry:agent:{aid}", "label": str(label), "type": "agent_registry"})
            for sub in a.get("sub_agents") or []:
                sid = str(sub)
                if sid in reg_agent_ids or any(sid == (x.get("id") and str(x.get("id"))) for x in reg_agents):
                    edges.append({
                        "source": f"registry:agent:{aid}",
                        "target": f"registry:agent:{sid}",
                        "type": "sub",
                    })
        for g in reg_groups:
            gid = g.get("id")
            if not gid:
                continue
            nid = f"registry:group:{gid}"
            nodes.append({"id": nid, "label": str(gid), "type": "agent_group"})
            for m in g.get("include") or []:
                mid = str(m)
                if mid in reg_agent_ids or any(mid == (x.get("id") and str(x.get("id"))) for x in reg_agents):
                    edges.append({
                        "source": nid,
                        "target": f"registry:agent:{mid}",
                        "type": "member",
                    })

        return {"nodes": nodes, "edges": edges}

    @app.post("/runs")
    def start_run(
        req: Optional[RunRequest] = None,
        user_id: Optional[str] = None,
        text: Optional[str] = None,
        session_id: Optional[str] = None,
        config_path: Optional[str] = None,
        config_inline: Optional[str] = None,
    ):
        cfg = _load_cfg(req=req, config_path=config_path, config_inline=config_inline)
        base_dir = (
            Path(req.config_path).resolve().parent
            if (req and req.config_path)
            else (Path(config_path).resolve().parent if config_path else Path(".").resolve())
        )

        # Build services
        artifact_svc = build_artifact_service(cfg.artifact_service)
        session_svc = build_session_service(cfg.session_service)
        memory_svc = build_memory_service(cfg.memory_service)

        # Build root agent via registries if present, else fallback to inline agents
        tool_reg = build_tool_registry_from_config(cfg, base_dir=base_dir)
        try:
            agent_reg = build_agent_registry_from_config(cfg, base_dir=base_dir, provider_defaults=cfg.model_providers, tool_registry=tool_reg)
        except ImportError as e:  # pragma: no cover
            raise HTTPException(status_code=500, detail=str(e))

        root = None
        if cfg.agents_registry and (cfg.agents_registry.get("groups") or cfg.agents_registry.get("agents")):
            # Prefer group "core" if present, else first agent id in registry
            try:
                group = agent_reg.get_group("core")
                root = group[0]
            except Exception:
                agents_ids = list((cfg.agents_registry.get("agents") or []))
                if agents_ids:
                    first_id = agents_ids[0].get("id")
                    if first_id:
                        root = agent_reg.get(first_id)
        if root is None:
            # Fallback to inline agents
            agent_map = build_agents(cfg.agents, provider_defaults=cfg.model_providers, base_dir=str(base_dir), shared_toolsets=cfg.toolsets)
            if not agent_map:
                raise HTTPException(status_code=400, detail="No agents defined")
            root = agent_map[cfg.agents[0].name]
        # Normalize root agent name
        try:
            setattr(root, "name", "root_agent")
        except Exception:
            pass

        # Construct Runner
        try:
            from google.adk.runners import Runner  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise HTTPException(status_code=500, detail="google-adk is required") from e

        runner = Runner(
            app_name="agent-compose-kit",
            agent=root,
            artifact_service=artifact_svc,
            session_service=session_svc,
            memory_service=memory_svc,
        )
        rc = build_run_config(cfg)

        # Create or resume session
        import asyncio

        async def _ensure_session():
            s_id = (req.session_id if req else None) or session_id
            if not s_id:
                s = await runner.session_service.create_session(app_name=runner.app_name, user_id=(req.user_id if req else user_id))
                return s.id
            return s_id

        session_id = asyncio.run(_ensure_session())
        # Apply global instruction if configured
        if getattr(cfg, "global_instruction", None):
            try:
                setattr(root, "global_instruction", cfg.global_instruction)
            except Exception:
                pass

        run_id = _gen_id()
        runs[run_id] = {
            "runner": runner,
            "rc": rc,
            "user_id": (req.user_id if req else user_id),
            "session_id": session_id,
            "text": (req.text if req else text),
            "tool_reg": tool_reg,
        }
        return {"run_id": run_id, "session_id": session_id}

    @app.get("/runs/{run_id}/events")
    async def stream_events(run_id: str):
        run = runs.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        runner = run["runner"]
        rc = run["rc"]
        user_id = run["user_id"]
        session_id = run["session_id"]
        text = run["text"]

        from google.genai import types  # type: ignore

        async def _gen() -> AsyncGenerator[bytes, None]:
            import asyncio

            q: "asyncio.Queue[bytes]" = asyncio.Queue()
            stop = asyncio.Event()

            async def produce_events():
                try:
                    content = types.Content(role="user", parts=[types.Part(text=text)])
                    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content, run_config=rc):
                        payload = _event_to_json(event)
                        await q.put(f"data: {payload}\n\n".encode("utf-8"))
                        if run.get("cancel"):
                            break
                finally:
                    stop.set()

            async def keepalive():
                try:
                    while not stop.is_set():
                        await asyncio.sleep(15)
                        await q.put(b": keepalive\n\n")
                except asyncio.CancelledError:  # pragma: no cover
                    pass

            t1 = asyncio.create_task(produce_events())
            t2 = asyncio.create_task(keepalive())
            try:
                while not stop.is_set() or not q.empty():
                    try:
                        item = await asyncio.wait_for(q.get(), timeout=1.0)
                        yield item
                    except asyncio.TimeoutError:
                        continue
            finally:
                t2.cancel()
                try:
                    await t2
                except Exception:
                    pass
                try:
                    await t1
                except Exception:
                    pass
                # Cleanup tool registries if present
                try:
                    tr = run.get("tool_reg")
                    if tr:
                        tr.close_all()
                except Exception:
                    pass

        return StreamingResponse(_gen(), media_type="text/event-stream")

    @app.post("/runs/{run_id}/cancel")
    def cancel_run(run_id: str):
        run = runs.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")
        run["cancel"] = True
        return {"ok": True}

    def _load_cfg(req: Optional[ValidateRequest | RunRequest] = None, *, config_path: Optional[str] = None, config_inline: Optional[str] = None) -> AppConfig:
        if req and getattr(req, "config_path", None):
            return load_config_file(Path(getattr(req, "config_path")))
        if req and getattr(req, "config_inline", None):
            raw = getattr(req, "config_inline")
            data = yaml.safe_load(raw) or {}
            return AppConfig.model_validate(data)
        if config_path:
            return load_config_file(Path(config_path))
        if config_inline:
            raw = config_inline
            data = yaml.safe_load(raw) or {}
            return AppConfig.model_validate(data)
        raise HTTPException(status_code=400, detail="config_path or config_inline required")

    def _gen_id() -> str:
        import uuid

        return uuid.uuid4().hex

    def _event_to_json(event: Any) -> str:
        import json

        d: Dict[str, Any] = {
            "id": getattr(event, "id", None),
            "author": getattr(event, "author", None),
            "partial": bool(getattr(event, "partial", False)),
            "timestamp": getattr(event, "timestamp", None),
        }
        content = getattr(event, "content", None)
        if content is not None and getattr(content, "parts", None) is not None:
            # Serialize parts shallowly
            parts_out = []
            for p in content.parts:
                obj = {}
                if getattr(p, "text", None) is not None:
                    obj["text"] = p.text
                if getattr(p, "function_call", None) is not None:
                    obj["function_call"] = getattr(p, "function_call")._asdict() if hasattr(getattr(p, "function_call"), "_asdict") else str(getattr(p, "function_call"))
                if getattr(p, "function_response", None) is not None:
                    obj["function_response"] = getattr(p, "function_response")._asdict() if hasattr(getattr(p, "function_response"), "_asdict") else str(getattr(p, "function_response"))
                parts_out.append(obj)
            d["content"] = {"parts": parts_out}
        return json.dumps(d)

    return app
