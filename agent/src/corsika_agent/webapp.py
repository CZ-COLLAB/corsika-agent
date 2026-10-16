"""Local web GUI for the pure CORSIKA Agent: OpenCode chat + file workspace.

Only loopback listening is supported unless ``MUON_WEB_ALLOW_REMOTE=1`` is set.
Model credentials are injected exclusively through environment variables.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from . import __version__
from .models import AgentError, available_backends, normalize_studio_model
from .sessions import (
    archive_session,
    create_session,
    list_files,
    list_sessions,
    load_session,
    read_file,
    recover_interrupted_sessions,
    rename_session,
    runtime_status,
    send_message,
    shutdown_active_sessions,
    stop_session,
    upload_file,
    write_file,
)

try:
    from fastapi import FastAPI, File, Header, HTTPException, UploadFile
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("corsika-agent requires Python >=3.10 and the [web] extra") from exc


ROOT = Path(os.environ.get("MUON_WORKSPACE_ROOT", os.getcwd())).resolve()
WEB_DIR = Path(__file__).with_name("web")
app = FastAPI(
    title="CORSIKA Agent",
    version=__version__,
    docs_url="/api/docs",
    redoc_url=None,
)
app.mount("/vendor", StaticFiles(directory=WEB_DIR / "vendor"), name="vendor")
recover_interrupted_sessions(ROOT)


@app.on_event("shutdown")
def _shutdown_workspace_agents() -> None:
    shutdown_active_sessions()


def _error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/status")
def status() -> Dict[str, Any]:
    corsika_root = Path(
        os.environ.get("MUON_CORSIKA7_ROOT", os.path.expanduser("~/corsika-78010"))
    )
    return {
        "version": __version__,
        "workspace": str(ROOT),
        "deepseek_configured": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "model_backends": available_backends(),
        "corsika_root": str(corsika_root),
        "corsika_ready": corsika_root.is_dir(),
        "runtime": runtime_status(),
    }


@app.get("/api/workspaces")
def workspace_sessions() -> Dict[str, Any]:
    return {
        "sessions": list_sessions(ROOT),
        "runtime": runtime_status(),
        "models": available_backends(),
    }


@app.post("/api/workspaces")
def workspace_session_create(body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return create_session(
            ROOT,
            title=str(body.get("title") or "") or None,
            model=str(body.get("model", "deepseek-flash")),
        )
    except Exception as exc:
        raise _error(exc) from exc


@app.get("/api/workspaces/{session_id}")
def workspace_session_get(session_id: str) -> Dict[str, Any]:
    try:
        return load_session(ROOT, session_id)
    except Exception as exc:
        raise _error(exc) from exc


@app.patch("/api/workspaces/{session_id}")
def workspace_session_rename(session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return rename_session(ROOT, session_id, str(body.get("title") or ""))
    except Exception as exc:
        raise _error(exc) from exc


@app.delete("/api/workspaces/{session_id}")
def workspace_session_delete(session_id: str) -> Dict[str, Any]:
    try:
        return archive_session(ROOT, session_id)
    except Exception as exc:
        raise _error(exc) from exc


@app.post("/api/workspaces/{session_id}/chat")
def workspace_session_chat(session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return send_message(ROOT, session_id, str(body["message"]))
    except Exception as exc:
        raise _error(exc) from exc


@app.post("/api/workspaces/{session_id}/stop")
def workspace_session_stop(session_id: str) -> Dict[str, Any]:
    try:
        return stop_session(ROOT, session_id)
    except Exception as exc:
        raise _error(exc) from exc


@app.get("/api/workspaces/{session_id}/files")
def workspace_files(session_id: str) -> Dict[str, Any]:
    try:
        return {"files": list_files(ROOT, session_id)}
    except Exception as exc:
        raise _error(exc) from exc


@app.get("/api/workspaces/{session_id}/file")
def workspace_file_get(session_id: str, path: str) -> Dict[str, Any]:
    try:
        return read_file(ROOT, session_id, path)
    except Exception as exc:
        raise _error(exc) from exc


@app.put("/api/workspaces/{session_id}/file")
def workspace_file_put(session_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return write_file(
            ROOT, session_id, str(body["path"]), str(body.get("content", ""))
        )
    except Exception as exc:
        raise _error(exc) from exc


@app.post("/api/workspaces/{session_id}/files")
async def workspace_file_upload(
    session_id: str, file: UploadFile = File(...), directory: str = "uploads"
) -> Dict[str, Any]:
    try:
        content = await file.read()
        return upload_file(
            ROOT, session_id, file.filename or "upload.bin", content, directory
        )
    except Exception as exc:
        raise _error(exc) from exc


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("corsika-agent requires the [web] extra") from exc
    host = os.environ.get("MUON_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("MUON_WEB_PORT", "8765"))
    if host not in {"127.0.0.1", "localhost", "::1"} and os.environ.get(
        "MUON_WEB_ALLOW_REMOTE"
    ) != "1":
        raise RuntimeError("The GUI has no authentication; remote listening requires explicitly setting MUON_WEB_ALLOW_REMOTE=1")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
