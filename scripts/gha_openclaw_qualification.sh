#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${1:-qa/gha-host}"
mkdir -p "$OUT_DIR"
OPENCLAW_SPEC="${OPENCLAW_SPEC:-2026.8.1-beta.3}"
PIDS=()
cleanup(){ for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT

redact() {
  sed -E -e 's/(Bearer )[A-Za-z0-9._~+\/-]+/\1[REDACTED]/g' -e 's/(token[" ]*[:=][" ]*)[^", ]+/\1[REDACTED]/Ig'
}
record() {
  local name="$1"; shift
  set +e; "$@" >"$OUT_DIR/${name}.stdout" 2>"$OUT_DIR/${name}.stderr"; local rc=$?; set -e
  printf '%s\n' "$rc" >"$OUT_DIR/${name}.rc"
  redact <"$OUT_DIR/${name}.stdout" >"$OUT_DIR/${name}.stdout.redacted" || true
  redact <"$OUT_DIR/${name}.stderr" >"$OUT_DIR/${name}.stderr.redacted" || true
  rm -f "$OUT_DIR/${name}.stdout" "$OUT_DIR/${name}.stderr"
}
node --version | tee "$OUT_DIR/node-version.txt"
npm --version | tee "$OUT_DIR/npm-version.txt"
docker --version | tee "$OUT_DIR/docker-version.txt"
printf '%s\n' "$OPENCLAW_SPEC" > "$OUT_DIR/openclaw-spec.txt"

npm install -g "openclaw@${OPENCLAW_SPEC}"
record openclaw_version openclaw --version
record openclaw_help openclaw --help
record config_schema openclaw config schema --json
export ROT_ROUTER_TOKEN=x
export OPENCLAW_CONFIG_PATH="$PWD/config/openclaw.example.json"
record config_validate openclaw config validate --json
record sandbox_help openclaw sandbox --help
record sandbox_explain openclaw sandbox explain --json
record sandbox_list_before openclaw sandbox list --json

# Reproduce the upstream default sandbox image contract pinned in qualification/.
docker build -t openclaw-sandbox:bookworm-slim -f qualification/Dockerfile.openclaw-sandbox . >"$OUT_DIR/sandbox-build.log" 2>&1
record sandbox_image docker image inspect openclaw-sandbox:bookworm-slim

# Zero-cost protocol integration: OpenClaw -> ROT router -> local mock provider.
python3 scripts/mock_openai_provider.py >"$OUT_DIR/mock-provider.log" 2>&1 & PIDS+=("$!")
ROT_UPSTREAM_BASE_URL=http://127.0.0.1:8899/v1 ROT_ROUTER_TOKEN=x OLLAMA_API_KEY=x python3 router/model_router.py >"$OUT_DIR/router.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 30); do curl -fsS http://127.0.0.1:8787/healthz >/dev/null 2>&1 && break; sleep 0.2; done
record router_health curl -fsS http://127.0.0.1:8787/healthz
record agent_exec_mock openclaw agent exec "Reply exactly ROT_OK" --config "$PWD/config/openclaw.example.json" --cwd "$PWD" --json --timeout 45
record sandbox_list_after openclaw sandbox list --json

python3 - "$OUT_DIR" "$OPENCLAW_SPEC" <<'PY'
import json,pathlib,sys
out=pathlib.Path(sys.argv[1]); spec=sys.argv[2]
def rc(n):
    try:return int((out/f'{n}.rc').read_text().strip())
    except:return 999
def txt(n):
    p=out/f'{n}.stdout.redacted'; return p.read_text(errors='replace') if p.exists() else ''
def agent_doc():
    try:return json.loads(txt('agent_exec_mock'))
    except:return {}
a=agent_doc()
checks={
 'upstream_openclaw_install':rc('openclaw_version')==0,
 'cli_surface':rc('openclaw_help')==0,
 'config_schema_generation':rc('config_schema')==0,
 'rotclaw_config_validation':rc('config_validate')==0,
 'sandbox_cli_surface':rc('sandbox_help')==0,
 'sandbox_explain_runtime':rc('sandbox_explain')==0,
 'sandbox_image_build':rc('sandbox_image')==0,
 'rot_router_health':rc('router_health')==0,
 'agent_exec_router_mock_e2e':rc('agent_exec_mock')==0 and a.get('ok') is True and 'ROT_OK' in str(a.get('final','')),
 'sandbox_runtime_visible_after_agent':rc('sandbox_list_after')==0 and len(txt('sandbox_list_after').strip())>2,
}
ver=txt('openclaw_version').strip().splitlines()[-1] if txt('openclaw_version').strip() else 'UNKNOWN'
doc={'schema':'rotclaw.gha-host-qualification.v3','openclaw_package_spec':spec,'openclaw_observed_version':ver,'checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'non_claims':['real provider inference','sandbox escape resistance under agent tool execution','runtime tool-policy enforcement under adversarial model execution','restart recovery','multi-agent concurrency','production soak','persistent-host durability'],'config_validate_evidence_tail':txt('config_validate')[-1200:],'agent_exec_evidence_tail':txt('agent_exec_mock')[-1600:],'sandbox_after_evidence_tail':txt('sandbox_list_after')[-1600:]}
(out/'QUALIFICATION.json').write_text(json.dumps(doc,indent=2)+'\n'); print(json.dumps(doc,indent=2))
required=['upstream_openclaw_install','cli_surface','config_schema_generation','rotclaw_config_validation','sandbox_cli_surface','sandbox_image_build','rot_router_health','agent_exec_router_mock_e2e']
if not all(checks[k] for k in required):sys.exit(1)
PY
