#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$HOME/.openclaw/.env"
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE; run scripts/bootstrap-private-env.sh first." >&2; exit 2; }
[[ "$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%Lp' "$ENV_FILE")" == "600" ]] || echo "WARN: expected $ENV_FILE mode 600" >&2
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
: "${ROT_ROUTER_TOKEN:?ROT_ROUTER_TOKEN missing}"
: "${OLLAMA_API_KEY:?OLLAMA_API_KEY missing}"
exec python3 "$ROOT/router/model_router.py"
