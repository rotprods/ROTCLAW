#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/ancestry_check.py"
command -v openclaw >/dev/null || { echo 'openclaw missing' >&2; exit 2; }
openclaw config validate
openclaw doctor --lint
openclaw models list --provider rot-router || true
bash "$ROOT/context/RUNTIME_PREFLIGHT.sh"
echo 'STATIC_AND_RUNTIME_CLI_GATE_PASS'
echo 'NOTE: provider inference, sandbox isolation and production soak require explicit live qualification on the target host.'
