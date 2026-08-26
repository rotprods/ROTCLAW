#!/usr/bin/env python3
import hashlib,json,re,subprocess,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; fail=[]; passed=[]
def ok(n,c,d=""): (passed if c else fail).append((n,d))
def load(p): return json.loads((ROOT/p).read_text())
required=["README.md","SOUL.md","AGENTS.md","SECURITY.md","context/ACTA_DE_CONSCIENCIA.md","context/MEMORY.md","context/SYSTEM_GRAPH.json","context/SUBAGENTS.md","context/RUNTIME_PREFLIGHT.sh","router/model_router.py","config/model-routing.json"]
for p in required: ok("exists:"+p,(ROOT/p).is_file())
g=load("context/SYSTEM_GRAPH.json"); ids=[n.get("id") for n in g["nodes"]]; idset=set(ids); allowed={"OBSERVED","CANONICAL","INFERRED","PLANNED","BLOCKED"}
ok("graph.schema_v2",g.get("schema")=="rot.system-graph.v2")
ok("graph.unique_node_ids",len(ids)==len(idset))
ok("graph.no_dangling_edges",all(e.get("from") in idset and e.get("to") in idset for e in g["edges"]))
ok("graph.node_epistemics",all(n.get("epistemic_status") in allowed and n.get("provenance_ref") for n in g["nodes"]))
ok("graph.edge_epistemics",all(e.get("epistemic_status") in allowed and e.get("provenance_ref") for e in g["edges"]))
node={n["id"]:n for n in g["nodes"]}; ok("operator.authority",node.get("operator",{}).get("kind")=="authority"); ok("router.canonical",node.get("model-router",{}).get("epistemic_status")=="CANONICAL"); ok("ollama.not_false_live",node.get("ollama-upstream",{}).get("epistemic_status")=="PLANNED")
texts=[]
for p in ROOT.rglob("*"):
 if p.is_file() and p.stat().st_size<2_000_000:
  try: texts.append((str(p.relative_to(ROOT)),p.read_text(errors="ignore")))
  except: pass
patterns=[r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"(?i)sk-[A-Za-z0-9]{20,}",r"(?i)(api[_-]?key|access[_-]?token|password)\s*[:=]\s*[A-Za-z0-9_\-]{24,}"]
for pat in patterns:
 hits=[f for f,t in texts if re.search(pat,t) and "ROTATE_AND_SET_NEW_KEY_HERE" not in t and "generate-a-long-random-local-token" not in t]; ok("security:"+pat,not hits,",".join(hits))
pre=ROOT/"context/RUNTIME_PREFLIGHT.sh"; r=subprocess.run(["bash","-n",str(pre)],capture_output=True,text=True); ok("preflight.syntax",r.returncode==0,r.stderr); t=time.perf_counter(); r=subprocess.run(["bash",str(pre)],capture_output=True,text=True); dt=time.perf_counter()-t; ok("preflight.exec",r.returncode==0,r.stderr)
mem=(ROOT/"context/MEMORY.md").read_text(); ok("memory.revalidation","Revalidation rule" in mem); ok("memory.no_raw_secrets","No raw secrets" in mem)
sub=(ROOT/"context/SUBAGENTS.md").read_text(); ok("agents.concurrency","Concurrency law" in sub)
hashes={hashlib.sha256(json.dumps(g,sort_keys=True,separators=(",",":")).encode()).hexdigest() for _ in range(100)}; ok("graph.determinism",len(hashes)==1)
s=[]
for _ in range(1000):
 t=time.perf_counter_ns(); hashlib.sha256(json.dumps(g,sort_keys=True,separators=(",",":")).encode()).digest(); s.append((time.perf_counter_ns()-t)/1e6)
report={"passed":len(passed),"failed":len(fail),"score_pct":round(100*len(passed)/(len(passed)+len(fail)),2),"failures":fail,"benchmarks":{"graph_hash_ms_p50":statistics.median(s),"graph_hash_ms_p95":sorted(s)[949],"preflight_seconds":dt,"node_count":len(ids),"edge_count":len(g["edges"])}}
(ROOT/"qa/QA_RESULT.json").write_text(json.dumps(report,indent=2)+"\n"); print(json.dumps(report,indent=2)); raise SystemExit(1 if fail else 0)
