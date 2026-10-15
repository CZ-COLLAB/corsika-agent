# CORSIKA Agent

A pure CORSIKA 7 research Agent: **opencode + four CORSIKA prompt documents + a web chat interface**.

Relationship to the old muon-studio: it keeps the "Workspace & Chat" frontend and opencode
session management, and removes all agent framework parts — the Task factory, research
Agent, independent review, evaluation, MCP, etc. — leaving only the CORSIKA 7
prompt documents, `SKILL.md`, `usage-guide.md`, `code-architecture.md`, and
`planetary-migration.md`, as the
Agent's entire domain knowledge. The backend does not bundle any CORSIKA tool code —
compiling, running, and analysis are all done by the Agent itself, guided by the prompts.

## Components

```
corsika-agent/
├── prompts/corsika7/            # The prompt documents (the only source of domain knowledge)
│   ├── SKILL.md
│   └── references/
│       ├── usage-guide.md       # Configuration / running / debugging / analysis guide
│       ├── code-architecture.md # Source-code architecture and extension guide
│       └── planetary-migration.md # Migrating the simulation to other planets (Mars/Venus)
├── src/corsika_agent/           # Web backend
│   ├── models.py                # Model configuration (keys injected via environment variables)
│   ├── sessions.py              # Session management + opencode launch
│   ├── webapp.py                # FastAPI service
│   └── web/index.html           # Chat + file workspace frontend
├── scripts/
│   ├── install.sh               # One-command install
│   └── run-server.sh            # Start the web server
└── SETUP.md                     # Configuration guide for AI Agents
```

## How it works

1. Each Chat Session has its own workspace directory
   `workspaces/studio/chats/<chat-id>/workspace/`.
2. When a session is created, the prompt documents are copied into the workspace
   at `.opencode/skills/corsika7/`; OpenCode discovers this skill automatically on
   startup. Whenever a task involves CORSIKA, the Agent loads the skill and fully reads
   `usage-guide.md` / `code-architecture.md` (plus `planetary-migration.md` for
   non-Earth atmospheres) as instructed.
3. The workspace also contains a minimal `AGENTS.md` (identity + interaction
   conventions), injected into the opencode configuration via
   `OPENCODE_CONFIG_CONTENT`.
4. User sends a message → one Agent turn is started with
   `opencode run --pure --dir <workspace> --model deepseek/...`, and the JSON event
   stream is parsed into chat messages and tool traces; the turn can be stopped at any
   time, and messages and files are all preserved.

## Quick start (server)

```bash
git clone this repository (or unpack the archive) into the target directory
cd corsika-agent
export DEEPSEEK_API_KEY="your key"          # Required; only via environment variables
export MUON_CORSIKA7_ROOT=/path/to/corsika-78010   # Location of the CORSIKA distribution
./scripts/install.sh
./scripts/run-server.sh
# Open http://127.0.0.1:8765 in a browser
```

See `SETUP.md` for details (including the full deployment guide for AI Agents).

## Environment variables

| Variable | Description | Default |
|------|------|------|
| `DEEPSEEK_API_KEY` | Model API key (required) | — |
| `DEEPSEEK_BASE_URL` | API endpoint | `https://api.deepseek.com` |
| `MUON_CORSIKA7_ROOT` | CORSIKA distribution directory | `/eos/home-z/zhuoch/corsika-78010` |
| `MUON_WORKSPACE_ROOT` | Session data root directory | Current directory |
| `MUON_WEB_HOST` / `MUON_WEB_PORT` | Listen address/port | `127.0.0.1` / `8765` |
| `MUON_WEB_ALLOW_REMOTE` | Allow remote listening (no auth; use with care) | Unset |
| `MUON_OPENCODE_TIMEOUT_SECONDS` | Timeout per turn | `1800` |
| `MUON_OPENCODE_RUN_AS_USER` | Run opencode as a dedicated user (requires sudo rules) | Unset |
| `MUON_AGENT_GROUP` | Isolated agent group (shared workspaces) | Unset |

The key never enters the web page, workspaces, chat history, or command-line arguments.
