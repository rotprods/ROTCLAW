#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/scripts/ancestry_check.py"
python3 "$ROOT/scripts/config_static_check.py"
command -v openclaw >/dev/null || { echo 'openclaw missing' >&2; exit 2; }
openclaw config validate
openclaw doctor --lint
openclaw policy check --severity-min error
openclaw sandbox explain
openclaw models list --provider rot-router
bash "$ROOT/context/RUNTIME_PREFLIGHT.sh"
echo 'CONTROL_PLANE_AND_RUNTIME_CLI_GATE_PASS'
echo 'NOTE: real provider inference, sandbox escape/adversarial tests and production soak remain separate live qualification gates.'
