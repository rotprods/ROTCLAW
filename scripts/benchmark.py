#!/usr/bin/env python3
import json,time,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/'context/SYSTEM_GRAPH.json').read_text())
queries=['openclaw runtime','model router','runtime host','system graph','private memory','github executable truth','ollama upstream','rotclaw control plane']
def compile(q):
    terms=set(q.lower().replace(':',' ').replace('_',' ').split())
    def score(n):
        blob=' '.join(str(v) for v in n.values()).lower().replace('_',' ')
        return sum(1 for t in terms if t in blob)
    rank=sorted(g['nodes'],key=lambda n:(-score(n),n['id']))
    chosen=[n for n in rank if score(n)>0][:8] or rank[:4]
    ids={n['id'] for n in chosen}
    edges=[e for e in g['edges'] if e['from'] in ids or e['to'] in ids][:16]
    return json.dumps({'query':q,'nodes':chosen,'edges':edges,'epistemic_note':g['epistemic_note']},sort_keys=True,separators=(',',':')).encode()
lat=[]; deterministic=True; sizes=[]
for q in queries:
    outs=[]
    for _ in range(10000):
        s=time.perf_counter_ns(); o=compile(q); lat.append((time.perf_counter_ns()-s)/1e6); outs.append(hashlib.sha256(o).digest()); sizes.append(len(o))
    deterministic &= len(set(outs))==1
lat.sort(); res={'iterations':len(lat),'queries':len(queries),'deterministic':deterministic,'context_compile_ms_p50':statistics.median(lat),'context_compile_ms_p95':lat[int(len(lat)*.95)-1],'context_compile_ms_p99':lat[int(len(lat)*.99)-1],'output_bytes_p50':statistics.median(sizes)}
(ROOT/'benchmarks/BENCHMARK_RESULT.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
