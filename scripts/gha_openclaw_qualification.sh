#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-qa/gha-host}"
mkdir -p "$OUT_DIR"
OPENCLAW_VERSION="${OPENCLAW_VERSION:-2026.8.1}"

redact() {
  sed -E \
    -e 's/(Bearer )[A-Za-z0-9._~+\/-]+/\1[REDACTED]/g' \
    -e 's/(api[_-]?key[" ]*[:=][" ]*)[^", ]+/\1[REDACTED]/Ig' \
    -e 's/(token[" ]*[:=][" ]*)[^", ]+/\1[REDACTED]/Ig'
}

record() {
  local name="$1"; shift
  set +e
  "$@" >"$OUT_DIR/${name}.stdout" 2>"$OUT_DIR/${name}.stderr"
  local rc=$?
  set -e
  printf '%s\n' "$rc" >"$OUT_DIR/${name}.rc"
  redact <"$OUT_DIR/${name}.stdout" >"$OUT_DIR/${name}.stdout.redacted" || true
  redact <"$OUT_DIR/${name}.stderr" >"$OUT_DIR/${name}.stderr.redacted" || true
  rm -f "$OUT_DIR/${name}.stdout" "$OUT_DIR/${name}.stderr"
  return 0
}

node --version | tee "$OUT_DIR/node-version.txt"
npm --version | tee "$OUT_DIR/npm-version.txt"
docker --version | tee "$OUT_DIR/docker-version.txt"

npm install -g "openclaw@${OPENCLAW_VERSION}" --allow-scripts=openclaw
record openclaw_version openclaw --version
record openclaw_help openclaw --help
record config_schema openclaw config schema --json

# Validate ROTCLAW's actual public-safe config against the exact upstream CLI.
export ROT_ROUTER_TOKEN="qualification-dummy-token-not-a-secret"
export OPENCLAW_CONFIG_PATH="$PWD/config/openclaw.example.json"
record config_validate openclaw config validate --json
record sandbox_help openclaw sandbox --help
record sandbox_explain openclaw sandbox explain --json
record sandbox_list openclaw sandbox list --json

python3 - "$OUT_DIR" "$OPENCLAW_VERSION" <<'PY'
import json, pathlib, sys, subprocess
out=pathlib.Path(sys.argv[1]); ver=sys.argv[2]
def rc(name):
    try: return int((out/f"{name}.rc").read_text().strip())
    except: return 999

def tail(name):
    p=out/f"{name}.stdout.redacted"
    return p.read_text(errors='replace')[-1200:] if p.exists() else ''
checks={
  'upstream_openclaw_install': rc('openclaw_version')==0,
  'cli_surface': rc('openclaw_help')==0,
  'config_schema_generation': rc('config_schema')==0,
  'rotclaw_config_validation': rc('config_validate')==0,
  'sandbox_cli_surface': rc('sandbox_help')==0,
  'sandbox_explain_runtime': rc('sandbox_explain')==0,
  'sandbox_docker_visibility': rc('sandbox_list')==0,
}
doc={
 'schema':'rotclaw.gha-host-qualification.v1',
 'openclaw_target_version':ver,
 'checks':checks,
 'pass_count':sum(checks.values()),
 'total':len(checks),
 'qualified_dimensions':[
   k for k,v in checks.items() if v
 ],
 'non_claims':[
   'real provider inference','real agent sandbox escape resistance','tool policy enforcement under model execution',
   'restart recovery','multi-agent concurrency','production soak','persistent-host durability'
 ],
 'config_validate_evidence_tail':tail('config_validate'),
 'sandbox_explain_evidence_tail':tail('sandbox_explain'),
}
(out/'QUALIFICATION.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc,indent=2))
# Upstream install + CLI + our config must pass. Sandbox runtime may remain separately diagnostic.
required=['upstream_openclaw_install','cli_surface','config_schema_generation','rotclaw_config_validation','sandbox_cli_surface']
if not all(checks[k] for k in required): sys.exit(1)
PY
