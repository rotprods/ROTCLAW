#!/usr/bin/env python3
import hashlib,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/"context/SYSTEM_GRAPH.json").read_text())
q=" ".join(sys.argv[1:]).strip(); ql=q.lower()
BUDGET=int(os.environ.get("ROT_CONTEXT_BUDGET_BYTES","4096"))
allowed={"OBSERVED","CANONICAL"}
if os.environ.get("ROT_INCLUDE_INFERRED")=="1": allowed.add("INFERRED")
terms=set(re.findall(r"[a-z0-9][a-z0-9_.:-]*",ql))
def score(n):
    blob=" ".join(str(v) for k,v in n.items() if k!="provenance_ref").lower()
    return sum(3 if t==str(n.get("id","")).lower() else 1 for t in terms if t in blob)
rank=sorted((n for n in g["nodes"] if n.get("epistemic_status") in allowed),key=lambda n:(-score(n),n["id"]))
chosen=[n for n in rank if score(n)>0][:8] or rank[:4]
ids={n["id"] for n in chosen}
edges=[e for e in g["edges"] if e.get("epistemic_status") in allowed and (e["from"] in ids or e["to"] in ids)][:16]
out={"schema":"rot.context-pack.v1","query":q,"budget_bytes":BUDGET,"nodes":chosen,"edges":edges,"epistemic_note":g["epistemic_note"]}
def enc(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
while len(enc(out))+96>BUDGET and out["edges"]: out["edges"].pop()
while len(enc(out))+96>BUDGET and len(out["nodes"])>1: out["nodes"].pop()
out["integrity_sha256"]=hashlib.sha256(enc({k:v for k,v in out.items() if k!="integrity_sha256"})).hexdigest()
while len(enc(out))>BUDGET and out["edges"]: out["edges"].pop()
while len(enc(out))>BUDGET and len(out["nodes"])>1: out["nodes"].pop()
out["integrity_sha256"]=hashlib.sha256(enc({k:v for k,v in out.items() if k!="integrity_sha256"})).hexdigest()
print(enc(out).decode())
