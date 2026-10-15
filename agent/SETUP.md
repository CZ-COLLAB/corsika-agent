# CORSIKA Agent Configuration Guide (for AI Agents)

This document is written for **AI Agents that need to deploy this project on a new
server or personal computer**. It spells out "where, what to install, what to configure,
how to verify, and common failures" in full. Please follow it in order and do not skip
the verification steps. What you are installing is a **pure CORSIKA 7 research Agent**:
opencode + three CORSIKA prompt documents + a web chat interface.

---

## 1. What this is

| Component | Role | Notes |
|------|------|------|
| `prompts/corsika7/` | The three prompt documents | The Agent's only CORSIKA domain knowledge; copied into the workspace `.opencode/skills/corsika7/` per session |
| `src/corsika_agent/` | Python web backend | Manages sessions and workspace files; starts the Agent with `opencode run --pure` |
| `web/index.html` | Frontend | Chat + file tree + editor, nothing else |
| opencode | Agent runtime | Must already be installed, version ≥ 1.x |

This project **does not bundle** CORSIKA tool code (it does not render cards, parse DAT,
or run simulations). The Agent compiles, runs, and analyzes CORSIKA inside the workspace
itself, guided entirely by the three prompt documents.

---

## 2. Prerequisite checks (do these on every machine)

```bash
# 1. Python ≥ 3.10
python3 --version

# 2. opencode installed (on the PATH)
which opencode && opencode --version
# If not installed:
curl -fsSL https://opencode.ai/install | bash
# After installing, log in again or add ~/.opencode/bin to the PATH

# 3. Location of the CORSIKA distribution (source + compiled run/ directory)
ls <corsika distribution path>            # e.g. ~/corsika-78010
ls <corsika distribution path>/run        # should show the corsika executable
```

> You need to provide the CORSIKA distribution (source) yourself; it is not bundled
> with this project (licensing reasons).
> Having only the binaries without source also works: the Agent can still run
> simulations, it just cannot modify and rebuild the source.

---

## 3. Installing the project

```bash
cd <unpacked corsika-agent directory>

# Method A: automatic script (recommended)
./scripts/install.sh

# Method B: manual (equivalent)
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[web]"
```

The install script checks opencode and Python and exits with a clear message if either
is missing.

---

## 4. Configuration (environment variables)

All keys are injected exclusively through environment variables — **never write keys
into any file, command-line argument, or the web page**.

```bash
# Required: model API key (DeepSeek example)
export DEEPSEEK_API_KEY="sk-xxxx"

# Optional: custom API endpoint (proxy, local vLLM/SGLang, or any OpenAI-compatible service)
export DEEPSEEK_BASE_URL="https://api.deepseek.com"

# Required (if not in the default location): CORSIKA distribution directory
export MUON_CORSIKA7_ROOT="$HOME/corsika-78010"

# Optional: session data root directory (defaults to the current directory)
export MUON_WORKSPACE_ROOT="$PWD"

# Optional: port (default 8765), timeout (default 1800 seconds per turn)
export MUON_WEB_PORT=8765
export MUON_OPENCODE_TIMEOUT_SECONDS=1800
```

See `README.md` for the full table of common variables.

---

## 5. Starting up and verification

```bash
./scripts/run-server.sh          # equivalent to .venv/bin/corsika-agent
```

Then **you must verify**:

```bash
# ① Service is up
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
# Expected: opencode available=true, deepseek_configured=true, corsika_ready=true

# ② Create a session (should return a session_id)
curl -s -X POST http://127.0.0.1:8765/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{"title":"smoke"}' | python3 -m json.tool

# ③ Check that the prompts made it into the workspace
ls workspaces/studio/chats/*/workspace/.opencode/skills/corsika7/
# Expected: SKILL.md and references/{usage-guide.md,code-architecture.md} are all there

# ④ Send a message and wait for the Agent to reply (small task, e.g. "read
#    usage-guide.md and summarize how to write a steering card for a 1-proton shower")
curl -s -X POST http://127.0.0.1:8765/api/workspaces/<session_id>/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"..."}' | python3 -m json.tool
# Poll GET /api/workspaces/<session_id> until status=idle; messages should contain the keywords
```

See section 8 for troubleshooting failed verification.

---

## 6. Deploying to a production server (optional)

- **Running persistently**: use systemd or supervisord to start
  `.venv/bin/corsika-agent`, putting environment variables into the unit file's
  `Environment=` (never into the repository).
- **Reverse proxy + HTTPS**: by default it only listens on `127.0.0.1`. If public
  access is needed, reverse-proxy nginx to `http://127.0.0.1:8765` and enable TLS.
  **Do not** simply set `MUON_WEB_ALLOW_REMOTE=1` and go bare (the service itself has
  no authentication).
- **Isolated agent users** (multi-user server): run opencode as a dedicated user:
  ```bash
  export MUON_OPENCODE_RUN_AS_USER=agent-user     # requires a sudoers allowlist
  export MUON_AGENT_GROUP=agent-group             # shared workspace write permission
  ```
  opencode is then started through the `/usr/local/bin/muon-opencode` wrapper, which
  preserves only allowlisted environment variables; process groups and file permissions
  are managed by sessions.py.
- **Recovery**: after the web process restarts, orphaned opencode processes are
  automatically terminated and running sessions are marked idle; messages and files
  are not lost.

---

## 7. Moving to a personal computer (macOS / Windows / Linux)

1. Copy the whole `corsika-agent/` directory over (or unpack `corsika-agent-*.tar.gz`).
2. Follow sections 2 and 3 to install Python and opencode, then run
   `./scripts/install.sh`.
3. Configure `DEEPSEEK_API_KEY` and `MUON_CORSIKA7_ROOT` as in section 4.
4. Once all checks in section 5 pass, it is ready to use.

Notes:
- On Linux, compiling CORSIKA requires the same toolchain as the server
  (gfortran + gcc); on Apple Silicon use `scripts/build-corsika-macos.sh` (provided by
  the old muon-studio) or compile it yourself; on Windows, WSL2 is recommended.
- All session data lives under `workspaces/`; copy the whole directory to migrate chat
  history.

---

## 8. Common failures and troubleshooting

| Symptom | Cause | Fix |
|------|------|------|
| `api/status` shows `opencode available=false` | opencode is not on the web process's PATH | Install opencode or prepend `~/.opencode/bin` to the PATH in the startup script |
| `deepseek_configured=false` | `DEEPSEEK_API_KEY` not set | Export it and restart the web process |
| Session becomes `error` after sending a message | Invalid API key / network unreachable / wrong model name | Check `opencode-events.jsonl` in the session directory and the `error` field |
| Agent says it cannot find CORSIKA | `MUON_CORSIKA7_ROOT` points to the wrong place | Confirm the directory contains the `run/` executable and restart the web server |
| Agent does not read the prompts | The workspace `.opencode/skills/` was deleted | Recreate the session; or manually copy `prompts/corsika7/` back |
| Changes to `prompts/` have no effect | Prompts are copied when the session is created | Delete and recreate old sessions, or manually sync them into the session workspace |
| Port already in use | 8765 already running | Change `MUON_WEB_PORT` or stop the old process |

---

## 9. Key reminders for a new AI Agent

- **All domain knowledge lives in the skill**: when CORSIKA is involved, load the
  `corsika7` skill and, as required by SKILL.md, fully read `references/usage-guide.md`
  (running/debugging/analysis) and `references/code-architecture.md` (source
  architecture / modifying and rebuilding source) — do not rely on memory.
- **The reference documents are not an oracle**: when they conflict with the installed
  binary, `include/config.h`, run logs, or sample cards, the actual installation wins;
  when a compile-time feature is missing, you may modify the source + `make`.
- **Smoke first, then scale**: verify with 1 shower before large runs; save cards,
  seeds, logs, DAT, and analysis scripts.
- **Keep chat concise**: put cards, code, commands, and logs into workspace files.
- **Permissions**: the bash allowlist forbids `sudo/su/ssh/scp/pip/apt`; editing is
  allowed by default in the workspace and `MUON_CORSIKA7_ROOT`, other external
  directories are read-only.
