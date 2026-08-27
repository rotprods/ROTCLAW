#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_SPEC="${OPENCLAW_SPEC:-2026.8.1-beta.3}"
STATE_ROOT="${ROTCLAW_STATE_ROOT:-$HOME/.local/share/rotclaw-node01}"
CONFIG_ROOT="${ROTCLAW_CONFIG_ROOT:-$HOME/.config/rotclaw}"
ENV_FILE="$CONFIG_ROOT/node01.env"

mkdir -p "$STATE_ROOT" "$CONFIG_ROOT"
chmod 700 "$STATE_ROOT" "$CONFIG_ROOT"

need(){ command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 2; }; }
need git
need python3
need node
need npm
need docker

python3 - <<'PY'
import subprocess,sys
v=subprocess.check_output(['node','--version'],text=True).strip().lstrip('v')
parts=tuple(int(x) for x in v.split('.')[:3])
if parts < (22,22,3):
    raise SystemExit(f'Node >=22.22.3 required; observed {v}')
print('node_version_ok',v)
PY

docker info >/dev/null
npm install -g "openclaw@$OPENCLAW_SPEC"
openclaw --version

if ! docker image inspect openclaw-sandbox:bookworm-slim >/dev/null 2>&1; then
  docker build -t openclaw-sandbox:bookworm-slim -f qualification/Dockerfile.openclaw-sandbox .
fi

if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  cat > "$ENV_FILE" <<'EOF'
# ROTCLAW Node 01 private environment. Never commit this file.
OLLAMA_API_KEY=
ROT_ROUTER_TOKEN=
ROT_UPSTREAM_BASE_URL=https://ollama.com/v1
ROT_MODEL_DEEPSEEK=deepseek-v4-flash
ROT_MODEL_KIMI=kimi-k2.6
ROT_MODEL_GLM=glm-5.2
ROT_MODEL_MINIMAX=minimax-m3
EOF
  chmod 600 "$ENV_FILE"
  echo "created $ENV_FILE; populate secrets locally before start"
fi

install -m 600 config/openclaw.example.json "$CONFIG_ROOT/openclaw.json"
mkdir -p "$STATE_ROOT/workspace"

cat > "$STATE_ROOT/start-router.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
set -a
source "$ENV_FILE"
set +a
cd "$PWD"
exec python3 router/model_router.py
EOF
chmod 700 "$STATE_ROOT/start-router.sh"

cat > "$STATE_ROOT/verify-node01.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
set -a
source "$ENV_FILE"
set +a
export OPENCLAW_CONFIG_PATH="$CONFIG_ROOT/openclaw.json"
openclaw --version
openclaw config validate --json
openclaw sandbox explain --json
curl -fsS http://127.0.0.1:8787/healthz
EOF
chmod 700 "$STATE_ROOT/verify-node01.sh"

cat <<EOF
ROTCLAW Node 01 bootstrap complete.
State:  $STATE_ROOT
Config: $CONFIG_ROOT/openclaw.json
Secrets:$ENV_FILE
Next:
  1. populate OLLAMA_API_KEY and ROT_ROUTER_TOKEN in $ENV_FILE
  2. run $STATE_ROOT/start-router.sh
  3. run $STATE_ROOT/verify-node01.sh
  4. run scripts/real_provider_qualification.sh qa/node01-real
EOF
