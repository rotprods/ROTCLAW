#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${HOME:?HOME required}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="$HOME/.openclaw"
WORKSPACE="$STATE/workspace-rot"
CONFIG="$STATE/openclaw.json"
command -v node >/dev/null || { echo 'node is required' >&2; exit 1; }
command -v npm >/dev/null || { echo 'npm is required' >&2; exit 1; }
command -v openclaw >/dev/null || { echo 'openclaw must be installed explicitly on the host; refusing implicit global install' >&2; exit 2; }
mkdir -p "$STATE" "$WORKSPACE"
if [[ -e "$CONFIG" ]]; then cp "$CONFIG" "$CONFIG.backup.$(date +%Y%m%d%H%M%S)"; fi
cp "$ROOT/config/openclaw.example.json" "$CONFIG"
cp "$ROOT/AGENTS.md" "$WORKSPACE/AGENTS.md"
cp "$ROOT/SOUL.md" "$WORKSPACE/SOUL.md"
cp "$ROOT/workspace/IDENTITY.md" "$WORKSPACE/IDENTITY.md"
cp "$ROOT/workspace/TOOLS.md" "$WORKSPACE/TOOLS.md"
mkdir -p "$WORKSPACE/skills"
cp -R "$ROOT/skills/." "$WORKSPACE/skills/"
chmod 600 "$CONFIG"
chmod -R go-rwx "$WORKSPACE"
python3 "$ROOT/scripts/ancestry_check.py"
openclaw config validate
openclaw doctor --lint
printf 'Installed config: %s\nWorkspace: %s\n' "$CONFIG" "$WORKSPACE"
