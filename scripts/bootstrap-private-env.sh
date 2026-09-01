#!/usr/bin/env bash
set -euo pipefail
umask 077
STATE="$HOME/.openclaw"
ENV_FILE="$STATE/.env"
mkdir -p "$STATE"

if [[ -z "${OLLAMA_API_KEY:-}" ]]; then
  echo 'Set OLLAMA_API_KEY in the shell first; refusing to persist a literal provider key from source.' >&2
  exit 2
fi
if [[ "$OLLAMA_API_KEY" == *$'\n'* || "$OLLAMA_API_KEY" == *$'\r'* ]]; then
  echo 'OLLAMA_API_KEY contains a newline; refusing unsafe env serialization.' >&2
  exit 2
fi

ROUTER_TOKEN="${ROT_ROUTER_TOKEN:-}"
if [[ -z "$ROUTER_TOKEN" && -f "$ENV_FILE" ]]; then
  ROUTER_TOKEN="$(awk -F= '$1=="ROT_ROUTER_TOKEN"{print substr($0,index($0,"=")+1); exit}' "$ENV_FILE" || true)"
fi
if [[ -z "$ROUTER_TOKEN" ]]; then
  ROUTER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
fi
if [[ "$ROUTER_TOKEN" == *$'\n'* || "$ROUTER_TOKEN" == *$'\r'* ]]; then
  echo 'ROT_ROUTER_TOKEN contains a newline; refusing unsafe env serialization.' >&2
  exit 2
fi

TMP="$(mktemp "$STATE/.env.tmp.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
{
  printf 'OLLAMA_API_KEY=%s\n' "$OLLAMA_API_KEY"
  printf 'ROT_ROUTER_TOKEN=%s\n' "$ROUTER_TOKEN"
  printf 'ROT_ROUTER_HOST=%s\n' "${ROT_ROUTER_HOST:-127.0.0.1}"
  printf 'ROT_ROUTER_PORT=%s\n' "${ROT_ROUTER_PORT:-8787}"
  printf 'ROT_UPSTREAM_BASE_URL=%s\n' "${ROT_UPSTREAM_BASE_URL:-https://ollama.com/v1}"
} > "$TMP"
chmod 600 "$TMP"
mv "$TMP" "$ENV_FILE"
trap - EXIT
chmod 600 "$ENV_FILE"
printf 'Private OpenClaw env written atomically: %s (0600)\n' "$ENV_FILE"
