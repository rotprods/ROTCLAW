#!/usr/bin/env python3
import argparse, datetime as dt, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMS = ["openclaw_cli","router_health","provider_catalog","model_routing","tool_policy_runtime","sandbox_isolation","git_branch_isolation","restart_recovery","concurrency","production_soak"]
SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*)[^\s,;\"']+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
]

def sanitize(value, limit=700):
    text=str(value).replace("\x00","")
    for pat in SECRET_PATTERNS:
        text=pat.sub(lambda m: (m.group(1) if m.lastindex else "")+"[REDACTED]", text)
    return text[-limit:]

def result(state, evidence, latency=None):
    return {"state": state, "evidence": sanitize(evidence), "latency_ms": latency}

def run(cmd, timeout=20):
    t=time.perf_counter()
    try:
        p=subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, sanitize((p.stdout+p.stderr).strip(),1200), round((time.perf_counter()-t)*1000,3)
    except Exception as e:
        return 99, sanitize(f"{type(e).__name__}: {e}"), round((time.perf_counter()-t)*1000,3)

def http_get(url, token=None, timeout=5):
    headers={}
    if token: headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    t=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read(65536).decode("utf-8","replace")
            return r.status, sanitize(body), round((time.perf_counter()-t)*1000,3)
    except Exception as e:
        return 0, sanitize(f"{type(e).__name__}: {e}"), round((time.perf_counter()-t)*1000,3)

def git_sha():
    rc,out,_=run(["git","rev-parse","HEAD"],5)
    return out.splitlines()[-1] if rc==0 and out else os.environ.get("GITHUB_SHA","UNKNOWN")

def contract_only():
    d={k:result("NOT_RUN","Contract mode: live assertion intentionally not executed.") for k in DIMS}
    required=[ROOT/"config/openclaw.example.json",ROOT/"router/model_router.py",ROOT/"scripts/verify-live.sh",ROOT/"security/THREAT_MODEL.md"]
    ok=all(p.is_file() for p in required)
    d["openclaw_cli"]=result("BLOCKED" if ok else "FAIL","Live CLI unavailable/not invoked; required contracts present." if ok else "Missing live contract files.")
    return d

def live():
    d={k:result("NOT_RUN","not executed") for k in DIMS}
    oc=shutil.which("openclaw")
    if oc:
        rc,out,ms=run([oc,"--version"],10); d["openclaw_cli"]=result("PASS" if rc==0 else "FAIL",out or "openclaw returned no output",ms)
    else: d["openclaw_cli"]=result("BLOCKED","openclaw binary not found")

    router=os.environ.get("ROT_ROUTER_BASE_URL","http://127.0.0.1:8787").rstrip("/")
    token=os.environ.get("ROT_ROUTER_TOKEN")
    status,body,ms=http_get(router+"/healthz",token); d["router_health"]=result("PASS" if 200<=status<300 else "FAIL",body,ms)
    status,body,ms=http_get(router+"/v1/models",token); d["provider_catalog"]=result("PASS" if 200<=status<300 else "FAIL",body,ms)

    if os.environ.get("ROT_LIVE_MODEL_TESTS")=="1":
        aliases=[x.strip() for x in os.environ.get("ROT_MODEL_ALIASES","glm-5.2,minimax-m3,kimi-k2.6,deepseek-v4-flash").split(",") if x.strip()]
        failures=[]; timings=[]
        for model in aliases:
            payload=json.dumps({"model":model,"messages":[{"role":"user","content":"Reply exactly: ROT_OK"}],"max_tokens":8}).encode()
            headers={"Content-Type":"application/json"}
            if token: headers["Authorization"]="Bearer "+token
            req=urllib.request.Request(router+"/v1/chat/completions",data=payload,headers=headers,method="POST")
            t=time.perf_counter()
            try:
                with urllib.request.urlopen(req,timeout=60) as r:
                    txt=r.read(131072).decode("utf-8","replace"); timings.append((time.perf_counter()-t)*1000)
                    if r.status<200 or r.status>=300: failures.append(model+":http"+str(r.status))
                    elif "ROT_OK" not in txt: failures.append(model+":unexpected-response")
            except Exception as e: failures.append(model+":"+type(e).__name__)
        evidence="aliases="+",".join(aliases)
        if failures: evidence += "; failures="+",".join(failures)
        d["model_routing"]=result("PASS" if not failures else "FAIL",evidence,round(max(timings),3) if timings else None)
    else: d["model_routing"]=result("BLOCKED","Set ROT_LIVE_MODEL_TESTS=1 to execute cost-bearing model inference.")

    d["tool_policy_runtime"]=result("BLOCKED","Requires instrumented OpenClaw tool-policy fixture.")
    d["sandbox_isolation"]=result("BLOCKED","Requires actual sandbox/container isolation fixture.")
    branch=os.environ.get("ROT_EXPECTED_BRANCH")
    if branch:
        rc,out,ms=run(["git","branch","--show-current"],5); d["git_branch_isolation"]=result("PASS" if rc==0 and out.strip()==branch else "FAIL",f"expected={branch}; observed={out.strip()}",ms)
    else: d["git_branch_isolation"]=result("BLOCKED","ROT_EXPECTED_BRANCH not supplied.")
    d["restart_recovery"]=result("BLOCKED","Requires managed stop/start fixture plus persisted checkpoint.")
    d["concurrency"]=result("BLOCKED","Requires live multi-agent/provider load fixture.")
    d["production_soak"]=result("BLOCKED","Requires explicit soak duration and stable host.")
    return d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--live",action="store_true"); ap.add_argument("--out",default="qa/LIVE_QUALIFICATION.json"); args=ap.parse_args()
    dims=live() if args.live else contract_only()
    states=[x["state"] for x in dims.values()]
    overall="QUALIFIED" if states and all(s=="PASS" for s in states) else ("PARTIALLY_QUALIFIED" if "PASS" in states and "FAIL" not in states else "NOT_QUALIFIED")
    doc={"schema":"rotclaw.live-qualification.v1","captured_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"git_sha":git_sha(),"mode":"LIVE" if args.live else "CONTRACT_ONLY","dimensions":dims,"overall_state":overall}
    out=ROOT/args.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps(doc,indent=2))
    if args.live and any(v["state"]=="FAIL" for v in dims.values()): sys.exit(1)

if __name__=="__main__": main()
