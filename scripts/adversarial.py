#!/usr/bin/env python3
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/"context/SYSTEM_GRAPH.json").read_text())
ALLOWED={"OBSERVED","CANONICAL","INFERRED","PLANNED","BLOCKED"}
def validate(x):
    ids=[n.get("id") for n in x.get("nodes",[])]; s=set(ids)
    return (x.get("schema")=="rot.system-graph.v2" and len(ids)==len(s)
            and all(n.get("epistemic_status") in ALLOWED for n in x.get("nodes",[]))
            and all(e.get("from") in s and e.get("to") in s and e.get("epistemic_status") in ALLOWED for e in x.get("edges",[])))
assert validate(g)
detected=0; total=10000
for i in range(total):
    x=copy.deepcopy(g); m=i%8
    if m==0: x["nodes"].append(copy.deepcopy(x["nodes"][0]))
    elif m==1: x["edges"][0]["to"]="missing"
    elif m==2: x["edges"][0]["from"]="missing"
    elif m==3: x["schema"]="corrupt"
    elif m==4: x["nodes"][0]["epistemic_status"]="INVALID"
    elif m==5: x["edges"][0]["epistemic_status"]="INVALID"
    elif m==6: x["nodes"][1]["id"]=x["nodes"][0]["id"]
    else: x["edges"].append({"from":"ghost","to":"ghost2","relation":"x","epistemic_status":"OBSERVED","provenance_ref":"x"})
    detected += (not validate(x))
res={"mutations":total,"detected":detected,"detection_rate":detected/total,"baseline_valid":validate(g)}
(ROOT/"qa/ADVERSARIAL_RESULT.json").write_text(json.dumps(res,indent=2)+"\n")
print(json.dumps(res,indent=2)); raise SystemExit(0 if detected==total else 1)
