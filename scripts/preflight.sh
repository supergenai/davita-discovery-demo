#!/usr/bin/env bash
# Part 2, Step 1 — PREFLIGHT. Read-only version checks. Installs nothing.
set -uo pipefail

fail=0
check() { # name  min-desc  actual
  printf '%-10s %s\n' "$1" "${3:-MISSING}"
  [ -z "${3:-}" ] && fail=1
}

echo "=== OpenWorker discovery demo — preflight ==="
check "python3" ">=3.10" "$(python3 --version 2>/dev/null)"
check "node"    ">=20"   "$(node --version 2>/dev/null)"
check "uvx"     "current" "$(command -v uvx 2>/dev/null && uvx --version 2>/dev/null)"
check "git"     "any"    "$(git --version 2>/dev/null)"
check "rustup"  "opt"    "$(rustup --version 2>/dev/null)"

echo
if [ -f "$(dirname "$0")/../.env" ]; then
  echo ".env      present (not printing contents)"
else
  echo ".env      MISSING — copy .env.example to .env and fill it in"
  fail=1
fi

echo
[ "$fail" -eq 0 ] && echo "PREFLIGHT OK" || { echo "PREFLIGHT FAILED — install missing tools before continuing"; exit 1; }
