#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p "$HOME/.openclaw"
ENV_FILE="$HOME/.openclaw/.env"
if [[ -z "${OLLAMA_API_KEY:-}" ]]; then
  echo 'Set OLLAMA_API_KEY in your shell first; refusing to persist a literal key from source.' >&2
  exit 2
fi
printf 'OLLAMA_API_KEY=%s\n' "$OLLAMA_API_KEY" > "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo "Wrote $ENV_FILE with mode 600"
