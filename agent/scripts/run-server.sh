#!/usr/bin/env bash
# Start the CORSIKA Agent web server on the loopback interface.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/corsika-agent ]; then
  echo "!! Not installed yet: run ./scripts/install.sh first"
  exit 1
fi

: "${MUON_WORKSPACE_ROOT:=$PWD}"
export MUON_WORKSPACE_ROOT

echo "==> CORSIKA Agent"
echo "    workspace : $MUON_WORKSPACE_ROOT"
echo "    corsika   : ${MUON_CORSIKA7_ROOT:-not set (default /eos/home-z/zhuoch/corsika-78010)}"
echo "    api key   : $([ -n "${DEEPSEEK_API_KEY:-}" ] && echo configured || echo DEEPSEEK_API_KEY not set)"
exec ./.venv/bin/corsika-agent
