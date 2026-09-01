#!/usr/bin/env python3
from __future__ import annotations
import json, os, signal, subprocess, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(os.environ.get("ROTCLAW_LOCAL_HOME", "/mnt/data/rotclaw-local"))
S = BASE / "sentinel"
CFG = json.loads((S / "config.json").read_text())
STOP = False

def now(): return datetime.now(timezone.utc).isoformat()
def atomic_json(path: Path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
def heartbeat(extra=None):
    state = {
      "schema":"rotclaw.sentinel-state.v1", "timestamp":now(), "pid":os.getpid(),
      "status":"RUNNING" if not STOP else "STOPPING",
      "ollama_ok": ollama_ok(), "frontier_enabled": bool(CFG.get("frontier_enabled")),
      "queue_depth": len(list((S/"inbox").glob("*.json"))),
      "processing_depth": len(list((S/"processing").glob("*.json"))),
    }
    if extra: state.update(extra)
    atomic_json(S/"state"/"sentinel-state.json", state)

def ollama_ok():
    try:
        with urlopen(CFG["local_endpoint"] + "/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception: return False

def ollama_chat(prompt: str) -> str:
    body = json.dumps({"model": CFG["local_model"], "messages":[{"role":"user","content":prompt}], "stream":False, "think":False, "options":{"num_ctx":4096}}).encode()
    req = Request(CFG["local_endpoint"]+"/api/chat", data=body, headers={"Content-Type":"application/json"})
    with urlopen(req, timeout=CFG["max_mission_seconds"]) as r:
        data=json.load(r)
    return data.get("message",{}).get("content","")

def run_openclaw(prompt: str) -> dict:
    cmd=[str(BASE/"bin"/"run-agent.sh"), prompt]
    cp=subprocess.run(cmd, cwd=CFG["workspace"], text=True, capture_output=True, timeout=CFG["max_mission_seconds"], start_new_session=True)
    try: payload=json.loads(cp.stdout)
    except Exception: payload={"stdout":cp.stdout[-8000:]}
    if cp.returncode != 0:
        raise RuntimeError(f"openclaw exited {cp.returncode}: {cp.stderr[-1200:]}")
    return {"returncode":cp.returncode,"result":payload,"stderr":cp.stderr[-4000:]}

def route_task(prompt: str) -> dict:
    text=prompt.lower()
    frontier_terms=("deploy","production","merge","pull request","refactor","security","credential","secret","delete","database","migration","architecture","multi-file","github","network","payment","legal")
    local_terms=("summarize","classify","extract","format","health","status","short","brief","rename label","json")
    if any(t in text for t in frontier_terms) or len(prompt) > 1800:
        return {"route":"FRONTIER","reason":"complex_or_sensitive"}
    if any(t in text for t in local_terms) or len(prompt) <= 800:
        return {"route":"LOCAL","reason":"bounded_low_risk"}
    return {"route":"FRONTIER","reason":"uncertain_complexity"}

def ensure_ollama():
    if ollama_ok(): return True
    if not CFG.get("self_heal_ollama"): return False
    try:
        subprocess.run([str(BASE/"bin"/"start.sh")], timeout=15, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception: return False
    return ollama_ok()

def validate(m):
    if not isinstance(m,dict): raise ValueError("mission must be object")
    if m.get("schema") != "rotclaw.local-mission.v1": raise ValueError("invalid schema")
    t=m.get("type")
    if t not in CFG["allowed_mission_types"]: raise ValueError("mission type denied")
    p=m.get("prompt","")
    if not isinstance(p,str) or len(p)>CFG["max_prompt_chars"]: raise ValueError("prompt invalid/too large")
    return t,p

def execute(m):
    t,p=validate(m)
    started=time.time()
    if t=="health": out={"ollama_ok":ollama_ok(),"sentinel_pid":os.getpid()}
    elif t=="classify": out={"text":ollama_chat("Classify this task in one short label and one sentence. Do not use tools.\n\n"+p)}
    elif t=="summarize": out={"text":ollama_chat("Summarize concisely. Do not invent facts.\n\n"+p)}
    elif t=="route": out=route_task(p)
    elif t=="dispatch":
        decision=route_task(p)
        if decision["route"] == "LOCAL": out={"decision":decision,"execution":run_openclaw(p)}
        else:
            handoff={"schema":"rotclaw.frontier-handoff.v1","id":m.get("id"),"created_at":now(),"prompt":p,"reason":decision["reason"],"status":"QUEUED"}
            atomic_json(S/"frontier"/(str(m.get("id") or uuid.uuid4())+".json"), handoff)
            out={"decision":decision,"handoff":"QUEUED"}
    elif t=="local_agent": out=run_openclaw(p)
    else: raise ValueError("unsupported")
    return {"schema":"rotclaw.local-mission-result.v1","mission_id":m.get("id"),"type":t,"status":"SUCCEEDED","started_at":now(),"duration_ms":int((time.time()-started)*1000),"output":out}

def process_one(path:Path):
    dst=S/"processing"/path.name
    os.replace(path,dst)
    try:
        m=json.loads(dst.read_text())
        atomic_json(S/"outbox"/path.name,execute(m))
    except Exception as e:
        atomic_json(S/"failed"/path.name,{"schema":"rotclaw.local-mission-result.v1","status":"FAILED","error":type(e).__name__+": "+str(e),"timestamp":now()})
    finally:
        try: dst.unlink()
        except FileNotFoundError: pass

def sig(*_):
    global STOP; STOP=True
signal.signal(signal.SIGTERM,sig); signal.signal(signal.SIGINT,sig)

for d in ["inbox","processing","outbox","failed","frontier","logs","state"]: (S/d).mkdir(parents=True,exist_ok=True)
for lease in sorted((S/"processing").glob("*.json")):
    target=S/"inbox"/lease.name
    if not target.exists(): os.replace(lease,target)
heartbeat({"event":"STARTED"})
last_hb=0
while not STOP:
    t=time.time()
    if t-last_hb >= CFG["heartbeat_seconds"]:
        ensure_ollama(); heartbeat(); last_hb=t
    files=sorted((S/"inbox").glob("*.json"))
    if files: process_one(files[0]); heartbeat({"event":"MISSION_COMPLETED"}); continue
    time.sleep(CFG["poll_interval_seconds"])
heartbeat({"event":"STOPPED"})
