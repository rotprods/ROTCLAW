#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${1:-qa/real-provider}"
mkdir -p "$OUT_DIR"
: "${OLLAMA_API_KEY:?OLLAMA_API_KEY is required}"
: "${ROT_ROUTER_TOKEN:=qualification-local-token}"
: "${ROT_UPSTREAM_BASE_URL:=https://ollama.com/v1}"

PIDS=()
cleanup(){ for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT

ROT_ROUTER_HOST=127.0.0.1 ROT_ROUTER_PORT=8787 python3 router/model_router.py >"$OUT_DIR/router.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 50); do curl -fsS http://127.0.0.1:8787/healthz >/dev/null 2>&1 && break; sleep 0.2; done
curl -fsS http://127.0.0.1:8787/healthz > "$OUT_DIR/router-health.json"

export OPENCLAW_CONFIG_PATH="$PWD/config/openclaw.example.json"
MODELS=(deepseek-v4-flash kimi-k2.6 glm-5.2 minimax-m3)
for model in "${MODELS[@]}"; do
  set +e
  openclaw agent exec "Reply exactly ROT_REAL_OK" \
    --config "$PWD/config/openclaw.example.json" \
    --cwd "$PWD" \
    --model "rot-router/$model" \
    --json --timeout 120 \
    >"$OUT_DIR/$model.json" 2>"$OUT_DIR/$model.stderr"
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$OUT_DIR/$model.rc"
done

python3 - "$OUT_DIR" <<'PY'
import json,os,pathlib,sys
out=pathlib.Path(sys.argv[1])
models=['deepseek-v4-flash','kimi-k2.6','glm-5.2','minimax-m3']
results={}
for m in models:
    try: rc=int((out/f'{m}.rc').read_text().strip())
    except: rc=999
    try: d=json.loads((out/f'{m}.json').read_text())
    except: d={}
    results[m]={
      'rc':rc,'ok':rc==0 and d.get('ok') is True,
      'provider':d.get('provider'),'model':d.get('model'),
      'final_match':'ROT_REAL_OK' in str(d.get('final','')),
      'tool_calls':(d.get('toolSummary') or {}).get('calls',0),
    }
checks={m:(r['ok'] and r['provider']=='rot-router' and r['model']==m and r['final_match']) for m,r in results.items()}
doc={
 'schema':'rotclaw.real-provider-qualification.v1',
 'provider':'ollama-compatible',
 'upstream_url':os.environ.get('ROT_UPSTREAM_BASE_URL',''),
 'results':results,
 'checks':checks,
 'pass_count':sum(checks.values()),
 'total':len(checks),
 'non_claims':['persistent-host durability','restart recovery','production soak','complete sandbox escape resistance'],
}
(out/'QUALIFICATION.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc,indent=2))

# Fail closed on evidence hygiene: redact exact secret values from every textual artifact.
secrets=[os.environ.get('OLLAMA_API_KEY',''),os.environ.get('ROT_ROUTER_TOKEN','')]
for p in out.rglob('*'):
    if not p.is_file() or p.stat().st_size > 5_000_000: continue
    try: text=p.read_text(errors='strict')
    except Exception: continue
    changed=text
    for secret in secrets:
        if secret: changed=changed.replace(secret,'[REDACTED]')
    if changed != text: p.write_text(changed)
for p in out.rglob('*'):
    if not p.is_file() or p.stat().st_size > 5_000_000: continue
    try: text=p.read_text(errors='strict')
    except Exception: continue
    if any(secret and secret in text for secret in secrets):
        raise SystemExit(f'secret remained in evidence: {p}')

if not all(checks.values()): sys.exit(1)
PY
