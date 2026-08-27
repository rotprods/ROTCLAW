#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${1:-qa/gha-host}"
mkdir -p "$OUT_DIR"
OPENCLAW_SPEC="${OPENCLAW_SPEC:-2026.8.1-beta.3}"

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

# npm 10.x: upstream instructs older npm clients to omit --allow-scripts.
npm install -g "openclaw@${OPENCLAW_SPEC}"
record openclaw_version openclaw --version
record openclaw_help openclaw --help
record config_schema openclaw config schema --json
export ROT_ROUTER_TOKEN=x
export OPENCLAW_CONFIG_PATH="$PWD/config/openclaw.example.json"
record config_validate openclaw config validate --json
record sandbox_help openclaw sandbox --help
record sandbox_explain openclaw sandbox explain --json
record sandbox_list openclaw sandbox list --json

python3 - "$OUT_DIR" "$OPENCLAW_SPEC" <<'PY'
import json,pathlib,sys
out=pathlib.Path(sys.argv[1]); spec=sys.argv[2]
def rc(n):
    try:return int((out/f'{n}.rc').read_text().strip())
    except:return 999
def txt(n):
    p=out/f'{n}.stdout.redacted'; return p.read_text(errors='replace') if p.exists() else ''
checks={
 'upstream_openclaw_install':rc('openclaw_version')==0,
 'cli_surface':rc('openclaw_help')==0,
 'config_schema_generation':rc('config_schema')==0,
 'rotclaw_config_validation':rc('config_validate')==0,
 'sandbox_cli_surface':rc('sandbox_help')==0,
 'sandbox_explain_runtime':rc('sandbox_explain')==0,
 'sandbox_docker_visibility':rc('sandbox_list')==0,
}
ver=txt('openclaw_version').strip().splitlines()[-1] if txt('openclaw_version').strip() else 'UNKNOWN'
doc={'schema':'rotclaw.gha-host-qualification.v1','openclaw_package_spec':spec,'openclaw_observed_version':ver,'checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'non_claims':['real provider inference','sandbox escape resistance under agent execution','runtime tool-policy enforcement','restart recovery','multi-agent concurrency','production soak','persistent-host durability'],'config_validate_evidence_tail':txt('config_validate')[-1200:],'sandbox_explain_evidence_tail':txt('sandbox_explain')[-1200:]}
(out/'QUALIFICATION.json').write_text(json.dumps(doc,indent=2)+'\n'); print(json.dumps(doc,indent=2))
required=['upstream_openclaw_install','cli_surface','config_schema_generation','rotclaw_config_validation','sandbox_cli_surface']
if not all(checks[k] for k in required):sys.exit(1)
PY
