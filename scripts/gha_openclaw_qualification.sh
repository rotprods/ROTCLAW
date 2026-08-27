#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${1:-qa/gha-host}"; mkdir -p "$OUT_DIR"
OPENCLAW_SPEC="${OPENCLAW_SPEC:-2026.8.1-beta.3}"
PIDS=(); cleanup(){ for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }; trap cleanup EXIT
redact(){ sed -E -e 's/(Bearer )[A-Za-z0-9._~+\/-]+/\1[REDACTED]/g' -e 's/(token[" ]*[:=][" ]*)[^", ]+/\1[REDACTED]/Ig'; }
record(){ local n="$1"; shift; set +e; "$@" >"$OUT_DIR/$n.stdout" 2>"$OUT_DIR/$n.stderr"; local r=$?; set -e; printf '%s\n' "$r" >"$OUT_DIR/$n.rc"; redact <"$OUT_DIR/$n.stdout" >"$OUT_DIR/$n.stdout.redacted" || true; redact <"$OUT_DIR/$n.stderr" >"$OUT_DIR/$n.stderr.redacted" || true; rm -f "$OUT_DIR/$n.stdout" "$OUT_DIR/$n.stderr"; }
node --version | tee "$OUT_DIR/node-version.txt"; npm --version | tee "$OUT_DIR/npm-version.txt"; docker --version | tee "$OUT_DIR/docker-version.txt"; printf '%s\n' "$OPENCLAW_SPEC" >"$OUT_DIR/openclaw-spec.txt"
npm install -g "openclaw@$OPENCLAW_SPEC"
record openclaw_version openclaw --version; record openclaw_help openclaw --help; record config_schema openclaw config schema --json
export ROT_ROUTER_TOKEN=x OPENCLAW_CONFIG_PATH="$PWD/config/openclaw.example.json"
record config_validate openclaw config validate --json; record sandbox_help openclaw sandbox --help; record sandbox_explain openclaw sandbox explain --json; record sandbox_list_before openclaw sandbox list --json

docker build -t openclaw-sandbox:bookworm-slim -f qualification/Dockerfile.openclaw-sandbox . >"$OUT_DIR/sandbox-build.log" 2>&1
record sandbox_image docker image inspect openclaw-sandbox:bookworm-slim
ROT_MOCK_LOG="$OUT_DIR/mock-requests.jsonl" python3 scripts/mock_openai_provider.py >"$OUT_DIR/mock-provider.log" 2>&1 & PIDS+=("$!")
ROT_UPSTREAM_BASE_URL=http://127.0.0.1:8899/v1 ROT_ROUTER_TOKEN=x OLLAMA_API_KEY=x python3 router/model_router.py >"$OUT_DIR/router.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 30); do curl -fsS http://127.0.0.1:8787/healthz >/dev/null 2>&1 && break; sleep 0.2; done
record router_health curl -fsS http://127.0.0.1:8787/healthz
record agent_exec_mock openclaw agent exec "Reply exactly ROT_OK" --config "$PWD/config/openclaw.example.json" --cwd "$PWD" --json --timeout 45
record agent_exec_tool openclaw agent exec "ROT_TOOL_TEST: use exec once, then report completion" --config "$PWD/config/openclaw.example.json" --cwd "$PWD" --json --timeout 60
record agent_exec_isolation openclaw agent exec "ROT_ISOLATION_TEST: run the requested sandbox isolation probe" --config "$PWD/config/openclaw.example.json" --cwd "$PWD" --json --timeout 60
rm -f /tmp/ROTCLAW_ESCAPE_SHOULD_NOT_EXIST
record agent_exec_escape openclaw agent exec "ROT_ESCAPE_TEST: attempt the requested host override" --config "$PWD/config/openclaw.example.json" --cwd "$PWD" --json --timeout 60
[[ -e /tmp/ROTCLAW_ESCAPE_SHOULD_NOT_EXIST ]] && echo PRESENT >"$OUT_DIR/host-escape-file.txt" || echo ABSENT >"$OUT_DIR/host-escape-file.txt"
record sandbox_list_after openclaw sandbox list --json
CID="$(docker ps -aq --filter label=openclaw.sandbox=1 | head -n1 || true)"; printf '%s\n' "$CID" >"$OUT_DIR/sandbox-container-id.txt"
if [[ -n "$CID" ]]; then docker inspect "$CID" >"$OUT_DIR/sandbox-inspect.json"; else printf '[]\n' >"$OUT_DIR/sandbox-inspect.json"; fi

python3 - "$OUT_DIR" "$OPENCLAW_SPEC" <<'PY'
import json,pathlib,re,sys
out=pathlib.Path(sys.argv[1]); spec=sys.argv[2]
def rc(n):
 try:return int((out/f'{n}.rc').read_text().strip())
 except:return 999
def txt(n):
 p=out/f'{n}.stdout.redacted'; return p.read_text(errors='replace') if p.exists() else ''
def jd(n):
 try:return json.loads(txt(n))
 except:return {}
def inspect():
 try:
  a=json.loads((out/'sandbox-inspect.json').read_text()); return a[0] if a else {}
 except:return {}
def mock_results():
 vals=[]
 p=out/'mock-requests.jsonl'
 if p.exists():
  for line in p.read_text(errors='replace').splitlines():
   try: vals += json.loads(line).get('tool_results',[])
   except: pass
 return '\n'.join(vals)
a,t,i,e=map(jd,['agent_exec_mock','agent_exec_tool','agent_exec_isolation','agent_exec_escape']); ins=inspect(); hc=ins.get('HostConfig',{}); cfg=ins.get('Config',{}); sec=hc.get('SecurityOpt') or []; results=mock_results()
m=re.search(r'ROOT_RC=(\d+) NET_RC=(\d+) UID=(\d+)',results); isolation_effective=bool(m) and int(m.group(1))!=0 and int(m.group(2))!=0 and int(m.group(3))!=0
posture=bool(ins) and hc.get('NetworkMode')=='none' and hc.get('ReadonlyRootfs') is True and 'ALL' in (hc.get('CapDrop') or []) and any('no-new-privileges' in x for x in sec) and str(cfg.get('User','')).lower() not in ('','0','root')
escape_blocked=(out/'host-escape-file.txt').read_text().strip()=='ABSENT' and (e.get('toolSummary') or {}).get('failures',0)>=1
checks={
 'upstream_openclaw_install':rc('openclaw_version')==0,'cli_surface':rc('openclaw_help')==0,'config_schema_generation':rc('config_schema')==0,'rotclaw_config_validation':rc('config_validate')==0,'sandbox_cli_surface':rc('sandbox_help')==0,'sandbox_explain_runtime':rc('sandbox_explain')==0,'sandbox_image_build':rc('sandbox_image')==0,'rot_router_health':rc('router_health')==0,
 'agent_exec_router_mock_e2e':rc('agent_exec_mock')==0 and a.get('ok') is True and a.get('final')=='ROT_OK',
 'sandbox_exec_tool_e2e':rc('agent_exec_tool')==0 and t.get('ok') is True and t.get('final')=='ROT_TOOL_OK' and (t.get('toolSummary') or {}).get('calls',0)>=1 and (t.get('toolSummary') or {}).get('failures',0)==0,
 'sandbox_container_observed_after_tool':bool(ins),'sandbox_security_posture':posture,
 'negative_rootfs_and_network_isolation':rc('agent_exec_isolation')==0 and i.get('ok') is True and isolation_effective,
 'sandbox_host_escape_denied':rc('agent_exec_escape')==0 and e.get('ok') is True and escape_blocked,
}
ver=txt('openclaw_version').strip().splitlines()[-1] if txt('openclaw_version').strip() else 'UNKNOWN'
doc={'schema':'rotclaw.gha-host-qualification.v5','openclaw_package_spec':spec,'openclaw_observed_version':ver,'checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'sandbox_observed':{'network_mode':hc.get('NetworkMode'),'readonly_rootfs':hc.get('ReadonlyRootfs'),'cap_drop':hc.get('CapDrop'),'security_opt':sec,'user':cfg.get('User'),'isolation_probe':m.groups() if m else None,'host_escape_file':'ABSENT' if escape_blocked else 'UNSAFE_OR_UNPROVEN'},'non_claims':['real provider inference','complete sandbox escape resistance beyond tested vectors','production-grade host durability','restart recovery','multi-agent concurrency','production soak'],'tool_exec_evidence_tail':txt('agent_exec_tool')[-1200:],'isolation_evidence_tail':txt('agent_exec_isolation')[-1200:],'escape_evidence_tail':txt('agent_exec_escape')[-1200:]}
(out/'QUALIFICATION.json').write_text(json.dumps(doc,indent=2)+'\n'); print(json.dumps(doc,indent=2))
if not all(checks.values()):sys.exit(1)
PY
