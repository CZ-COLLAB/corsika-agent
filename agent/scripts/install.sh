#!/usr/bin/env bash
# Install the CORSIKA Agent into a fresh Python venv and verify prerequisites.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3.12}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python3
fi
echo "==> Using $PYTHON ($($PYTHON --version 2>&1))"

if ! command -v opencode >/dev/null 2>&1; then
  echo "!! opencode not found. Install it first (see SETUP.md):"
  echo "   curl -fsSL https://opencode.ai/install | bash"
  exit 1
fi
echo "==> opencode: $(command -v opencode)"

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
./.venv/bin/python -m pip install --upgrade pip >/dev/null
./.venv/bin/python -m pip install -e ".[web]" "$@"

echo
echo "==> Install complete. To start:"
echo "   export DEEPSEEK_API_KEY=...            # required"
echo "   export MUON_CORSIKA7_ROOT=/path/to/corsika-78010   # CORSIKA distribution"
echo "   ./scripts/run-server.sh"
echo "   Open http://127.0.0.1:8765 in a browser"
