#!/usr/bin/env bash
# One-time environment check for the CORSIKA Agent on lxplus.
set -uo pipefail
fail=0

echo "==> 1/4 opencode"
if command -v opencode >/dev/null 2>&1 || [ -x "$HOME/.opencode/bin/opencode" ]; then
  echo "    OK: $(opencode --version 2>/dev/null || "$HOME/.opencode/bin/opencode" --version)"
else
  echo "    MISSING. Install with:  curl -fsSL https://opencode.ai/install | bash"
  echo "    (then log out and back in so ~/.opencode/bin is on PATH)"
  fail=1
fi

echo "==> 2/4 CERN AI Gateway reachable"
code=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" https://aigw.cern.ch/v1/models)
if [ "$code" = "401" ] || [ "$code" = "200" ]; then
  echo "    OK (HTTP $code)"
else
  echo "    FAILED (HTTP $code) — check network/VPN"
  fail=1
fi

echo "==> 3/4 API key set"
if [ -n "${CERN_AI_API_KEY:-}" ]; then
  echo "    OK (CERN_AI_API_KEY is set)"
else
  echo "    MISSING. Add to ~/.bashrc:  export CERN_AI_API_KEY=\"...\""
  fail=1
fi

echo "==> 4/4 CORSIKA distribution readable"
CORSIKA_ROOT="${CORSIKA_ROOT:-/eos/user/z/zhuoch/corsika-78010}"
bin=$(ls "$CORSIKA_ROOT"/run/corsika78010Linux_* 2>/dev/null | head -1)
if [ -n "$bin" ]; then
  echo "    OK: found $(basename "$bin") in $CORSIKA_ROOT/run/"
else
  echo "    NOT ACCESSIBLE at $CORSIKA_ROOT — ask Zhuo for read access, or set:"
  echo "    export CORSIKA_ROOT=/path/to/your/own/corsika-78010"
  fail=1
fi

echo
if [ "$fail" = "0" ]; then
  echo "==> All checks passed. Try:  $(dirname "$0")/corsika-cli smoke \"list the compiled CORSIKA binaries\""
else
  echo "==> Some checks failed — fix the MISSING items above."
fi
exit "$fail"
