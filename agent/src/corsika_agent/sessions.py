"""Persistent, human-driven OpenCode chat workspaces for the pure CORSIKA Agent.

Every session owns an isolated workspace directory. The only guidance injected
into a workspace is the ``corsika7`` skill (``SKILL.md`` plus the two reference
documents), copied from the bundled ``prompts/corsika7`` tree into
``.opencode/skills/corsika7`` where OpenCode discovers it automatically.
"""

from __future__ import annotations

import errno
import json
import os
import pty
import re
import signal
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .models import (
    AgentError,
    STUDIO_MODELS,
    _model_environment,
    normalize_studio_model,
)

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")
_WRITE_LOCK = threading.RLock()
_ACTIVE_LOCK = threading.RLock()
_ACTIVE_PROCESSES: Dict[str, subprocess.Popen] = {}
_SKIP_NAMES = {".git", ".opencode", "__pycache__", ".DS_Store"}
_MAX_TEXT_BYTES = 2 * 1024 * 1024
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_WEB_DIR = Path(__file__).resolve().parent / "web"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identifier() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"chat-{stamp}-{uuid.uuid4().hex[:8]}"


def _safe_id(value: str) -> str:
    if not _ID.fullmatch(value):
        raise AgentError("Invalid workspace identifier")
    return value


def chats_root(root: Path) -> Path:
    return root.resolve() / "workspaces" / "studio" / "chats"


def _chat_dir(root: Path, session_id: str) -> Path:
    return chats_root(root) / _safe_id(session_id)


def _state_path(root: Path, session_id: str) -> Path:
    return _chat_dir(root, session_id) / "session.json"


def _workspace(root: Path, state: Dict[str, Any]) -> Path:
    candidate = (root.resolve() / str(state["workspace"])).resolve()
    expected = (_chat_dir(root, str(state["session_id"])) / "workspace").resolve()
    if candidate != expected or not candidate.is_dir():
        raise AgentError("Workspace directory is invalid")
    return candidate


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with _WRITE_LOCK:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        path.chmod(0o600)


def _read_object(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentError(f"Cannot read workspace state: {path}") from exc
    if not isinstance(value, dict):
        raise AgentError("Workspace state must be a JSON object")
    return value


def _messages(directory: Path) -> list[Dict[str, Any]]:
    path = directory / "messages.json"
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _write_messages(directory: Path, messages: Sequence[Dict[str, Any]]) -> None:
    _atomic_json(directory / "messages.json", list(messages))


def _message_counts(messages: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "message_count": len(messages),
        "conversation_count": sum(
            1 for item in messages if item.get("role") in {"user", "assistant"}
        ),
        "tool_count": sum(1 for item in messages if item.get("role") == "tool"),
    }


def _append_message(
    directory: Path,
    role: str,
    content: str,
    *,
    kind: str = "text",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    with _WRITE_LOCK:
        messages = _messages(directory)
        item: Dict[str, Any] = {
            "id": f"msg-{uuid.uuid4().hex[:12]}",
            "at": _now(),
            "role": role,
            "kind": kind,
            "content": content,
        }
        if metadata:
            item["metadata"] = metadata
        messages.append(item)
        _write_messages(directory, messages)


def _append_event(directory: Path, kind: str, content: str) -> None:
    event = {"at": _now(), "kind": kind, "content": content.rstrip("\n")}
    with _WRITE_LOCK:
        with (directory / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        (directory / "events.jsonl").chmod(0o600)


def _default_title(root: Path) -> str:
    return f"New Chat ({len(list_sessions(root)) + 1})"


# ---------------------------------------------------------------------------
# Skill prompt installation
# ---------------------------------------------------------------------------

def _install_skill_prompts(workspace: Path) -> None:
    """Copy the bundled prompt skills into the workspace skill tree.

    Skills live under ``_PROMPTS_DIR``, one directory per skill (each with a
    ``SKILL.md``). They are copied into ``.opencode/skills/<name>`` where
    OpenCode discovers them automatically.
    """
    if not _PROMPTS_DIR.is_dir():
        raise AgentError(f"prompts directory is missing: {_PROMPTS_DIR}")
    skill_root = workspace / ".opencode" / "skills"
    skill_root.mkdir(parents=True, exist_ok=True)
    for source in sorted(_PROMPTS_DIR.iterdir()):
        if not source.is_dir():
            continue
        if not (source / "SKILL.md").is_file():
            continue
        target = skill_root / source.name
        if target.is_dir():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        for path in target.rglob("*"):
            if path.is_file():
                path.chmod(0o644)


def _agents_document(workspace: Path) -> str:
    """Minimal identity document: everything CORSIKA-specific lives in the skill."""
    corsika_root = Path(
        os.environ.get("MUON_CORSIKA7_ROOT", "")
    ).expanduser().resolve()
    lines = [
        "# CORSIKA 7 Agent",
        "",
        "You are a CORSIKA 7 Agent working directly with researchers: understand the",
        "problem, inspect or modify source/config, run simulations, inspect outputs, and",
        "report clear results.",
        "",
        "## For every CORSIKA-related task",
        "",
        "1. Use the `skill` tool to load the `corsika7` skill, and fully read",
        "   `.opencode/skills/corsika7/references/usage-guide.md` as instructed by",
        "   SKILL.md; when the task involves source architecture, new options, physics",
        "   processes, or modifying and rebuilding the source, also fully read",
        "   `code-architecture.md`. If the task involves other planets (non-Earth",
        "   atmosphere/surface muon flux/migration capability on Mars, Venus, etc.),",
        "   fully read `references/planetary-migration.md` and follow all of its",
        "   parameters (atmosphere/magnetic field/gravity/radius/composition/observation",
        "   level/primary spectrum) and authoritative sources.",
        "2. The reference documents are not an oracle; when they conflict with the",
        "   installed binary, `include/config.h`, run logs, or samples, the actual",
        "   installation wins.",
        "3. Run a smoke test with 1 shower first, then scale up the statistics.",
        "4. Save everything: steering cards, seeds, logs, DAT, analysis scripts, and",
        "   plots.",
        "",
    ]
    if corsika_root.is_dir():
        lines += [
            f"## CORSIKA installation location",
            "",
            f"The installed CORSIKA distribution is at `{corsika_root}` (can be overridden",
            "with `MUON_CORSIKA7_ROOT`). Read and write access to that directory is",
            "allowed by default (the skill explicitly supports modifying source + `make`",
            "rebuild workflows).",
            "",
        ]
    lines += [
        "## Interaction conventions",
        "",
        "- Keep chat concise; put cards, code, commands, logs, and results into workspace",
        "  files.",
        "- Read and write files only in the current workspace; do not search for",
        "  credentials or data outside the workspace.",
        "- For large jobs (many showers), prefer the batch system provided by the server;",
        "  do not run serially on the login node. If the server is configured with",
        "  HTCondor, submit using the ready-made templates in `~/corsika_job/`.",
    ]
    return "\n".join(lines) + "\n"


def _grant_agent_workspace_access(workspace: Path) -> None:
    """Share a chat workspace with an optional isolated agent group."""
    import grp
    import stat as stat_module

    group = os.environ.get("MUON_AGENT_GROUP")
    if not group:
        return
    group_id = grp.getgrnam(group).gr_gid
    for path in [workspace, *workspace.rglob("*")]:
        if path.is_symlink():
            continue
        try:
            stat_result = path.stat()
            if stat_result.st_gid != group_id:
                shutil.chown(path, group=group)
                stat_result = path.stat()
            mode = stat_result.st_mode
            if path.is_dir():
                path.chmod(mode | stat_module.S_IRGRP | stat_module.S_IWGRP
                           | stat_module.S_IXGRP | stat_module.S_ISGID)
            else:
                path.chmod(mode | stat_module.S_IRGRP | stat_module.S_IWGRP)
        except PermissionError:
            raise AgentError(f"Cannot grant isolated agent access to {path}")
        except OSError as exc:
            raise AgentError(f"Cannot grant isolated agent access to {path}") from exc


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

def create_session(
    root: Path,
    *,
    title: Optional[str] = None,
    model: str = "deepseek-flash",
) -> Dict[str, Any]:
    model = normalize_studio_model(model)
    if model not in STUDIO_MODELS:
        raise AgentError("Unsupported model")
    if not shutil.which("opencode"):
        raise AgentError("OpenCode is not installed")

    session_id = _identifier()
    directory = _chat_dir(root, session_id)
    workspace = directory / "workspace"
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o711)
    workspace.mkdir()
    _install_skill_prompts(workspace)
    (workspace / "AGENTS.md").write_text(
        _agents_document(workspace), encoding="utf-8"
    )
    (workspace / "README.md").write_text(
        "# Persistent workspace\n\n"
        "Files and model changes in this folder are visible and editable in the studio.\n",
        encoding="utf-8",
    )
    _grant_agent_workspace_access(workspace)
    state: Dict[str, Any] = {
        "schema_version": "1.0",
        "session_id": session_id,
        "title": (title or "").strip()[:120] or _default_title(root),
        "mode": "blank",
        "runtime": "opencode",
        "model": model,
        "opencode_session_id": None,
        "status": "idle",
        "created_at": _now(),
        "updated_at": _now(),
        "workspace": str(workspace.relative_to(root.resolve())),
        "error": None,
    }
    _atomic_json(directory / "session.json", state)
    _write_messages(directory, [])
    _append_event(directory, "session", "Blank workspace created; OpenCode has not been started")
    return load_session(root, session_id)


def load_session(root: Path, session_id: str) -> Dict[str, Any]:
    directory = _chat_dir(root, session_id)
    state = _read_object(directory / "session.json")
    value = dict(state)
    value["messages"] = _messages(directory)
    value.update(_message_counts(value["messages"]))
    return value


def rename_session(root: Path, session_id: str, title: str) -> Dict[str, Any]:
    title = title.strip()
    if not title:
        raise AgentError("Chat name cannot be empty")
    if len(title) > 120:
        raise AgentError("Chat name must be no longer than 120 characters")
    path = _state_path(root, session_id)
    state = _read_object(path)
    if state.get("archived_at"):
        raise AgentError("Archived Chat cannot be renamed")
    state["title"] = title
    state["updated_at"] = _now()
    _atomic_json(path, state)
    _append_event(_chat_dir(root, session_id), "rename", f"Human renamed Chat to: {title}")
    return load_session(root, session_id)


def archive_session(root: Path, session_id: str) -> Dict[str, Any]:
    path = _state_path(root, session_id)
    state = _read_object(path)
    if state.get("status") in {"queued", "running", "stopping"}:
        raise AgentError("Wait for OpenCode to finish before deleting this Chat")
    if not state.get("archived_at"):
        state["archived_at"] = _now()
        state["updated_at"] = _now()
        _atomic_json(path, state)
        _append_event(_chat_dir(root, session_id), "archive", "Human removed Chat from history")
    return {"session_id": session_id, "archived": True}


def list_sessions(root: Path, limit: int = 50) -> list[Dict[str, Any]]:
    directory = chats_root(root)
    if not directory.is_dir():
        return []
    result: list[Dict[str, Any]] = []
    for path in directory.glob("*/session.json"):
        try:
            value = _read_object(path)
        except AgentError:
            continue
        if value.get("archived_at"):
            continue
        value.update(_message_counts(_messages(path.parent)))
        result.append(value)
    result.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return result[:limit]


def recover_interrupted_sessions(root: Path) -> int:
    """Make sessions usable again after the web process was restarted."""
    _terminate_orphan_workspace_agents(root)
    recovered = 0
    directory = chats_root(root)
    if not directory.is_dir():
        return recovered
    for state_path in directory.glob("*/session.json"):
        try:
            state = _read_object(state_path)
        except AgentError:
            continue
        if state.get("status") not in {"queued", "running", "stopping"}:
            continue
        state.pop("stop_requested", None)
        state["status"] = "idle"
        state["error"] = None
        state["updated_at"] = _now()
        _atomic_json(state_path, state)
        _append_message(
            state_path.parent,
            "system",
            "The server restart interrupted the previous Agent turn; the conversation and files already written are preserved, so you can continue directly.",
        )
        _append_event(state_path.parent, "recovered", "Recovered session after server restart")
        recovered += 1
    return recovered


# ---------------------------------------------------------------------------
# Workspace files
# ---------------------------------------------------------------------------

def _workspace_path(
    root: Path, state: Dict[str, Any], relative: str, *, must_exist: bool = True
) -> Path:
    relative_path = Path(relative)
    if not relative or relative_path.is_absolute() or ".." in relative_path.parts:
        raise AgentError("File path must stay inside the workspace")
    workspace = _workspace(root, state)
    candidate = (workspace / relative_path).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise AgentError("File path escapes the workspace") from exc
    if any(part in _SKIP_NAMES for part in relative_path.parts):
        raise AgentError("Reserved workspace path")
    if must_exist and not candidate.exists():
        raise AgentError("Workspace file does not exist")
    return candidate


def list_files(root: Path, session_id: str) -> list[Dict[str, Any]]:
    state = load_session(root, session_id)
    workspace = _workspace(root, state)
    result: list[Dict[str, Any]] = []
    for path in sorted(workspace.rglob("*"), key=lambda item: str(item).lower()):
        relative = path.relative_to(workspace)
        if any(part in _SKIP_NAMES for part in relative.parts) or path.is_symlink():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        result.append(
            {
                "path": str(relative),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size if path.is_file() else None,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )
        if len(result) >= 2000:
            break
    return result


def read_file(root: Path, session_id: str, relative: str) -> Dict[str, Any]:
    state = load_session(root, session_id)
    path = _workspace_path(root, state, relative)
    if not path.is_file():
        raise AgentError("Path is not a file")
    if path.stat().st_size > _MAX_TEXT_BYTES:
        raise AgentError("File is too large for the editor")
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise AgentError("Binary files cannot be opened in the text editor")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AgentError("File is not UTF-8 text") from exc
    return {"path": relative, "content": content, "size": len(raw)}


def write_file(root: Path, session_id: str, relative: str, content: str) -> Dict[str, Any]:
    if len(content.encode("utf-8")) > _MAX_TEXT_BYTES:
        raise AgentError("File is too large for the editor")
    state = load_session(root, session_id)
    path = _workspace_path(root, state, relative, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _grant_agent_workspace_access(path.parent)
    state["updated_at"] = _now()
    _atomic_json(_state_path(root, session_id), state)
    _append_event(_chat_dir(root, session_id), "file", f"Human saved {relative}")
    return read_file(root, session_id, relative)


def upload_file(
    root: Path, session_id: str, filename: str, content: bytes, directory: str = "uploads"
) -> Dict[str, Any]:
    if len(content) > _MAX_UPLOAD_BYTES:
        raise AgentError("Upload must be no larger than 100 MB")
    safe_name = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "-", Path(filename).name)[:160]
    if not safe_name:
        safe_name = "upload.bin"
    relative = str(Path(directory or "uploads") / safe_name)
    state = load_session(root, session_id)
    path = _workspace_path(root, state, relative, must_exist=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path = path.with_name(f"{path.stem}-{uuid.uuid4().hex[:6]}{path.suffix}")
        relative = str(path.relative_to(_workspace(root, state)))
    path.write_bytes(content)
    _grant_agent_workspace_access(path.parent)
    state["updated_at"] = _now()
    _atomic_json(_state_path(root, session_id), state)
    _append_event(_chat_dir(root, session_id), "upload", f"Human uploaded {relative}")
    return {"path": relative, "name": path.name, "size": len(content)}


# ---------------------------------------------------------------------------
# OpenCode execution
# ---------------------------------------------------------------------------

def _corsika_root() -> Path:
    return Path(os.environ.get("MUON_CORSIKA7_ROOT", os.path.expanduser("~/corsika-78010")))


def _opencode_environment(model: str, workspace: Path) -> Dict[str, str]:
    model = normalize_studio_model(model)
    environment = _model_environment(model)
    api_key = environment.get("OPENAI_API_KEY")
    if not api_key:
        raise AgentError("Model API key is not configured")
    environment["MUON_OPENCODE_API_KEY"] = api_key
    corsika_root = _corsika_root()
    fluka_data = next(
        (
            path
            for path in (
                corsika_root / "fluka4-5.1" / "data",
                corsika_root / "fluka" / "data",
            )
            if path.is_dir()
        ),
        None,
    )
    if fluka_data is not None:
        environment.setdefault("FLUKADATA", str(fluka_data))
        environment.setdefault("FLUPRO", str(fluka_data.parent))
    base_url = environment.get("OPENAI_BASE_URL", "https://api.deepseek.com")
    corsika_text = str(corsika_root)
    config = {
        "$schema": "https://opencode.ai/config.json",
        "instructions": [str(workspace / "AGENTS.md")],
        "provider": {
            "deepseek": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "DeepSeek",
                "options": {
                    "baseURL": base_url,
                    "apiKey": "{env:MUON_OPENCODE_API_KEY}",
                },
                "models": {
                    name: {"name": label} for name, label in STUDIO_MODELS.items()
                },
            }
        },
        "permission": {
            "external_directory": {
                "*": "deny",
                f"{corsika_text}/**": "allow",
            },
            "task": "allow",
            "skill": "allow",
            "edit": {
                "*": "allow",
                f"{corsika_text}/**": "allow",
            },
            "bash": {
                "*": "allow",
                "singularity *": "deny",
                "/usr/bin/singularity *": "deny",
                "sudo *": "deny",
                "su *": "deny",
                "ssh *": "deny",
                "scp *": "deny",
                "pip *": "deny",
                "pip3 *": "deny",
                "python* -m pip *": "deny",
                "apt *": "deny",
                "apt-get *": "deny",
            },
        },
    }
    environment["OPENCODE_CONFIG_CONTENT"] = json.dumps(config, ensure_ascii=False)
    environment["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    environment["OPENCODE_DISABLE_PRUNE"] = "true"
    environment["MUON_WORKSPACE_ROOT"] = str(workspace)
    environment["MUON_CORSIKA7_ROOT"] = corsika_text
    environment["SHELL"] = "/bin/bash"
    return environment


def _tool_event_content(part: Dict[str, Any]) -> str:
    tool = str(part.get("tool") or "tool")
    state = part.get("state") if isinstance(part.get("state"), dict) else {}
    title = str(state.get("title") or tool)
    status = str(state.get("status") or "")
    input_value = state.get("input")
    output = state.get("output")
    sections = [f"{tool} · {status}\n{title}"]
    if input_value not in (None, {}, ""):
        sections.append(json.dumps(input_value, ensure_ascii=False, indent=2)[:6000])
    if output not in (None, ""):
        sections.append(str(output)[:8000])
    return "\n\n".join(sections)


def _kill_process_group(group: int, sig: signal.Signals) -> None:
    """Signal an Agent-owned group, using the narrow sudo rule when users differ."""
    if group <= 1 or group == os.getpgrp():
        return
    try:
        os.killpg(group, sig)
    except ProcessLookupError:
        return
    except PermissionError:
        pass

    sudo = shutil.which("sudo")
    kill = Path("/usr/bin/kill")
    run_as_users = [os.environ.get("MUON_OPENCODE_RUN_AS_USER", "")]
    run_as_users.extend(
        item.strip()
        for item in os.environ.get("MUON_SIMULATION_RUN_AS_USERS", "").split(",")
    )
    run_as_users = list(dict.fromkeys(item for item in run_as_users if item))
    if not run_as_users or not sudo or not kill.is_file():
        return
    for run_as in run_as_users:
        try:
            subprocess.run(
                [
                    sudo,
                    "-n",
                    "-u",
                    run_as,
                    "--",
                    str(kill),
                    f"-{int(sig)}",
                    "--",
                    f"-{group}",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass


def _descendant_process_groups(root_pid: int) -> set[int]:
    proc = Path("/proc")
    if not proc.is_dir():
        return set()
    children: dict[int, list[int]] = {}
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            pid = int(entry.name)
            status = (entry / "status").read_text(encoding="utf-8", errors="replace")
            ppid_line = next(line for line in status.splitlines() if line.startswith("PPid:"))
            ppid = int(ppid_line.split()[1])
        except (OSError, ValueError, ProcessLookupError, StopIteration):
            continue
        children.setdefault(ppid, []).append(pid)
    pending = [root_pid]
    seen: set[int] = set()
    groups: set[int] = set()
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        try:
            group = os.getpgid(pid)
        except (OSError, ProcessLookupError):
            group = None
        if group is not None and group != os.getpgrp():
            groups.add(group)
        pending.extend(children.get(pid, []))
    return groups


def _signal_process_group(process: subprocess.Popen, sig: signal.Signals) -> None:
    if process.poll() is not None:
        return
    _kill_process_group(process.pid, sig)


def _force_kill_after(
    process: subprocess.Popen,
    workspace: Path,
    process_groups: set[int],
    delay_seconds: float = 5.0,
) -> None:
    def worker() -> None:
        time.sleep(delay_seconds)
        process_groups.update(_descendant_process_groups(process.pid))
        for group in process_groups:
            _kill_process_group(group, signal.SIGKILL)

    threading.Thread(target=worker, name=f"kill-opencode-{process.pid}", daemon=True).start()


def _finish_stopped(directory: Path, state_path: Path) -> None:
    state = _read_object(state_path)
    _append_message(
        directory,
        "system",
        "You stopped this Agent turn. The conversation history and files already written to the workspace are preserved; you can continue sending messages.",
    )
    _append_event(directory, "stop", "Human stopped the active OpenCode turn")
    state.pop("stop_requested", None)
    state["status"] = "idle"
    state["error"] = None
    state["updated_at"] = _now()
    _atomic_json(state_path, state)


def _run_message(root: Path, session_id: str, message: str) -> None:
    directory = _chat_dir(root, session_id)
    state_path = directory / "session.json"
    state = _read_object(state_path)
    workspace = _workspace(root, state)
    executable = shutil.which("opencode")
    if not executable:
        state["status"] = "error"
        state["error"] = "OpenCode is not installed"
        _atomic_json(state_path, state)
        return
    command = [
        executable,
        "run",
        "--pure",
        "--dir",
        str(workspace),
        "--model",
        f"deepseek/{normalize_studio_model(str(state['model']))}",
        "--format",
        "json",
        "--auto",
    ]
    if state.get("opencode_session_id"):
        command.extend(["--session", str(state["opencode_session_id"])])
    else:
        command.extend(["--title", str(state["title"])])
    command.append(message)
    run_as = os.environ.get("MUON_OPENCODE_RUN_AS_USER")
    if run_as:
        sudo = shutil.which("sudo")
        if not sudo:
            raise AgentError("sudo is required for isolated OpenCode execution")
        preserved = ",".join(
            [
                "MUON_OPENCODE_API_KEY",
                "OPENCODE_CONFIG_CONTENT",
                "OPENCODE_DISABLE_AUTOUPDATE",
                "OPENCODE_DISABLE_PRUNE",
                "MUON_WORKSPACE_ROOT",
                "MUON_CORSIKA7_ROOT",
            ]
        )
        wrapper = Path(os.environ.get("MUON_OPENCODE_WRAPPER", "/usr/local/bin/muon-opencode"))
        if not wrapper.is_file():
            raise AgentError("The isolated OpenCode wrapper is not installed")
        command[0] = str(wrapper)
        command = [
            sudo,
            "-n",
            "-H",
            "-u",
            run_as,
            f"--preserve-env={preserved}",
            "--",
            *command,
        ]
    with _WRITE_LOCK:
        state = _read_object(state_path)
        if state.get("stop_requested"):
            _finish_stopped(directory, state_path)
            return
        state["status"] = "running"
        state["error"] = None
        state["updated_at"] = _now()
        _atomic_json(state_path, state)
    _append_event(directory, "runtime", "OpenCode turn started")
    raw_log = directory / "opencode-events.jsonl"
    try:
        master_fd, slave_fd = pty.openpty()
        try:
            process = subprocess.Popen(
                command,
                cwd=workspace,
                env=_opencode_environment(str(state["model"]), workspace),
                stdin=subprocess.DEVNULL,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
                start_new_session=True,
            )
        finally:
            os.close(slave_fd)
        with _ACTIVE_LOCK:
            _ACTIVE_PROCESSES[session_id] = process
        if _read_object(state_path).get("stop_requested"):
            process_groups = {process.pid}
            process_groups.update(_descendant_process_groups(process.pid))
            _signal_process_group(process, signal.SIGTERM)
            _force_kill_after(process, workspace, process_groups, delay_seconds=0.5)
        runtime_error: Optional[str] = None
        final_text_parts: list[str] = []
        watchdog = threading.Timer(
            float(os.environ.get("MUON_OPENCODE_TIMEOUT_SECONDS", "1800")),
            lambda: _signal_process_group(process, signal.SIGKILL),
        )
        watchdog.daemon = True
        watchdog.start()
        try:
            with os.fdopen(master_fd, "r", encoding="utf-8", errors="replace") as stream, raw_log.open("a", encoding="utf-8") as handle:
                try:
                    for line in stream:
                        handle.write(line)
                        handle.flush()
                        stripped = line.strip().replace("\r", "")
                        if not stripped:
                            continue
                        try:
                            event = json.loads(stripped)
                        except json.JSONDecodeError:
                            _append_event(directory, "runtime-output", stripped[:4000])
                            continue
                        if not isinstance(event, dict):
                            continue
                        if event.get("sessionID"):
                            state["opencode_session_id"] = str(event["sessionID"])
                            latest = _read_object(state_path)
                            latest["opencode_session_id"] = state["opencode_session_id"]
                            latest["updated_at"] = _now()
                            _atomic_json(state_path, latest)
                        part = event.get("part") if isinstance(event.get("part"), dict) else {}
                        event_type = event.get("type")
                        if event_type == "text" and isinstance(part.get("text"), str):
                            text = part["text"].strip()
                            if text:
                                final_text_parts.append(text)
                        elif event_type == "tool_use":
                            final_text_parts.clear()
                            _append_message(
                                directory,
                                "tool",
                                _tool_event_content(part),
                                kind=str(part.get("tool") or "tool"),
                            )
                        elif event_type == "error":
                            _append_event(directory, "error", json.dumps(event, ensure_ascii=False)[:6000])
                            error = event.get("error") if isinstance(event.get("error"), dict) else {}
                            data = error.get("data") if isinstance(error.get("data"), dict) else {}
                            runtime_error = str(data.get("message") or error.get("name") or "OpenCode error")
                            _signal_process_group(process, signal.SIGTERM)
                            break
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise exc
        finally:
            if process.poll() is None:
                _signal_process_group(process, signal.SIGTERM)
        raw_log.chmod(0o600)
        return_code = process.wait()
        watchdog.cancel()
        final_text = "\n\n".join(final_text_parts).strip()
        if final_text:
            _append_message(directory, "assistant", final_text)
        state = _read_object(state_path)
        if state.get("stop_requested"):
            _finish_stopped(directory, state_path)
        else:
            state["status"] = "idle" if return_code == 0 and not runtime_error else "error"
            state["error"] = (
                None
                if return_code == 0 and not runtime_error
                else runtime_error or f"OpenCode exited with code {return_code}"
            )
            state["updated_at"] = _now()
            _atomic_json(state_path, state)
            _append_event(directory, "runtime", f"OpenCode turn exited with code {return_code}")
    except Exception as exc:
        state = _read_object(state_path)
        if state.get("stop_requested"):
            _finish_stopped(directory, state_path)
        else:
            state["status"] = "error"
            state["error"] = str(exc)
            state["updated_at"] = _now()
            _atomic_json(state_path, state)
            _append_event(directory, "error", str(exc))
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE_PROCESSES.pop(session_id, None)


def send_message(root: Path, session_id: str, message: str) -> Dict[str, Any]:
    message = message.strip()
    if not message:
        raise AgentError("Message cannot be empty")
    state = load_session(root, session_id)
    if state.get("status") in {"queued", "running", "stopping"}:
        raise AgentError("OpenCode is still working on the previous turn")
    directory = _chat_dir(root, session_id)
    _append_message(directory, "user", message)
    stored = _read_object(directory / "session.json")
    stored["status"] = "queued"
    stored["updated_at"] = _now()
    stored["error"] = None
    _atomic_json(directory / "session.json", stored)
    threading.Thread(
        target=_run_message,
        args=(root.resolve(), session_id, message),
        name=f"opencode-{session_id}",
        daemon=True,
    ).start()
    return load_session(root, session_id)


def stop_session(root: Path, session_id: str) -> Dict[str, Any]:
    state_path = _state_path(root, session_id)
    directory = _chat_dir(root, session_id)
    with _WRITE_LOCK:
        state = _read_object(state_path)
        if state.get("status") not in {"queued", "running", "stopping"}:
            return load_session(root, session_id)
        state["stop_requested"] = True
        state["status"] = "stopping"
        state["error"] = None
        state["updated_at"] = _now()
        _atomic_json(state_path, state)
    _append_event(directory, "stop-requested", "Human requested OpenCode stop")
    with _ACTIVE_LOCK:
        process = _ACTIVE_PROCESSES.get(session_id)
    if process is not None:
        process_groups = _descendant_process_groups(process.pid)
        process_groups.add(process.pid)
        _signal_process_group(process, signal.SIGTERM)
        _force_kill_after(process, _workspace(root, state), process_groups)
    return load_session(root, session_id)


def shutdown_active_sessions() -> None:
    with _ACTIVE_LOCK:
        processes = list(_ACTIVE_PROCESSES.values())
    for process in processes:
        _signal_process_group(process, signal.SIGTERM)


def runtime_status() -> Dict[str, Any]:
    executable = shutil.which("opencode")
    version = None
    if executable:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            version = result.stdout.strip() or result.stderr.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            version = None
    return {
        "id": "opencode",
        "available": bool(executable),
        "path": executable,
        "version": version,
    }


def _workspace_agent_process_groups(root: Path) -> set[int]:
    """Find detached OpenCode groups that still target one of our workspaces."""
    import pwd

    proc = Path("/proc")
    chats = str(chats_root(root).resolve()) + os.sep
    if not proc.is_dir():
        return set()
    groups: set[int] = set()
    anchors: set[int] = set()
    run_as = os.environ.get("MUON_OPENCODE_RUN_AS_USER")
    try:
        run_uid = pwd.getpwnam(run_as).pw_uid if run_as else None
    except KeyError:
        run_uid = None
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
            pid = int(entry.name)
            group = os.getpgid(pid)
            status = (entry / "status").read_text(encoding="utf-8", errors="replace")
            uid_line = next(line for line in status.splitlines() if line.startswith("Uid:"))
            real_uid = int(uid_line.split()[1])
        except (OSError, ValueError, ProcessLookupError, StopIteration):
            continue
        if run_uid is not None and real_uid != run_uid:
            continue
        try:
            cwd = (entry / "cwd").resolve(strict=True)
            cwd_in_chats = cwd.is_relative_to(Path(chats))
        except OSError:
            cwd_in_chats = False
        command_in_workspace = (
            chats in command and "/workspace" in command and "opencode" in command
        )
        if (cwd_in_chats or command_in_workspace) and group != os.getpgrp():
            groups.add(group)
            anchors.add(pid)
    for pid in anchors:
        groups.update(_descendant_process_groups(pid))
    return groups


def _terminate_orphan_workspace_agents(root: Path) -> int:
    groups = _workspace_agent_process_groups(root)
    for group in groups:
        _kill_process_group(group, signal.SIGTERM)
    if groups:
        time.sleep(0.5)
    for group in groups:
        _kill_process_group(group, signal.SIGKILL)
    return len(groups)
