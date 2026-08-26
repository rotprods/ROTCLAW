#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={"qa/GAUNTLET_50_LEDGER.json","qa/FINAL_SCORECARD.json","qa/RECOVERY_MANIFEST.json","benchmarks/GAUNTLET50_STRESS.json","SHA256SUMS.txt"}
rows=[]
for p in sorted(ROOT.rglob("*")):
    if p.is_file():
        rel=str(p.relative_to(ROOT))
        if rel in EXCLUDE: continue
        rows.append({"path":rel,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":p.stat().st_size})
manifest={"schema":"rot.recovery-manifest.v1","files":rows}
blob=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode(); manifest["root_hash"]=hashlib.sha256(blob).hexdigest()
(ROOT/"qa/RECOVERY_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(manifest["root_hash"])
