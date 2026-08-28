#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/frontier_result.py'

def run(args, expect=0):
    p=subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)
    if p.returncode!=expect:
        raise SystemExit(f'cmd failed rc={p.returncode} expected={expect}\nSTDOUT={p.stdout}\nSTDERR={p.stderr}')
    return p

with tempfile.TemporaryDirectory() as td:
    d=Path(td); mission=d/'mission.json'; handoff=d/'handoff.json'; env=d/'result.json'; state=d/'state'
    m={"schema":"rotclaw.mission.v1","mission_id":"result-check-001","goal":"bounded test","risk_class":"A1","repository":"rotprods/ROTCLAW","base_branch":"main","work_branch":"agent/result-check-001","allowed_paths":["docs/test.md"],"denied_paths":[".github/**"],"allowed_actions":["read","edit","test"],"acceptance":["test"]}
    h={"schema":"rotclaw.mission-handoff.v1","mission_id":"result-check-001","returncode":0,"stdout":"OK","stderr":""}
    mission.write_text(json.dumps(m)); handoff.write_text(json.dumps(h))
    run(["envelope","--mission",str(mission),"--handoff",str(handoff),"--source-commit","deadbeef","--out",str(env)])
    run(["ingest","--mission",str(mission),"--envelope",str(env),"--state-root",str(state)])
    accepted=json.loads((state/'accepted/result-check-001.json').read_text())
    assert accepted['authority']=='DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION'
    run(["ingest","--mission",str(mission),"--envelope",str(env),"--state-root",str(state)],expect=2)
    tampered=json.loads(env.read_text()); tampered['handoff']['stdout']='TAMPERED'; bad=d/'bad.json'; bad.write_text(json.dumps(tampered))
    run(["ingest","--mission",str(mission),"--envelope",str(bad),"--state-root",str(d/'state2')],expect=1)
    m2=dict(m); m2['goal']='changed'; mission.write_text(json.dumps(m2))
    run(["ingest","--mission",str(mission),"--envelope",str(env),"--state-root",str(d/'state3')],expect=1)
print('FRONTIER_RESULT_CONTRACT_PASS')
