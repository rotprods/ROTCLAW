#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha_obj(obj):
    return hashlib.sha256(canon(obj)).hexdigest()

def load(path):
    return json.loads(Path(path).read_text())

def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+"\n")
    os.replace(tmp,path)

def fail(msg, code=1):
    print("FRONTIER_RESULT_BLOCKED", msg, sep="\n", file=sys.stderr); raise SystemExit(code)

def envelope(args):
    mission=load(args.mission); handoff=load(args.handoff)
    mid=mission.get("mission_id")
    if not mid or handoff.get("mission_id") != mid: fail("mission_id_mismatch")
    env={
      "schema":"rotclaw.frontier-result.v1",
      "mission_id":mid,
      "mission_sha256":sha_obj(mission),
      "handoff_sha256":sha_obj(handoff),
      "source_commit":args.source_commit,
      "producer":"ROTCLAW_MISSION_BRIDGE",
      "status":"SUCCEEDED" if handoff.get("returncode")==0 else "FAILED",
      "created_at":datetime.now(timezone.utc).isoformat(),
      "handoff":handoff,
    }
    env["envelope_sha256"]=sha_obj({k:v for k,v in env.items() if k!="envelope_sha256"})
    atomic_json(Path(args.out),env)
    print("FRONTIER_ENVELOPE_PASS", env["envelope_sha256"])

def ingest(args):
    mission=load(args.mission); env=load(args.envelope)
    if env.get("schema")!="rotclaw.frontier-result.v1": fail("unsupported_schema")
    mid=mission.get("mission_id")
    if env.get("mission_id") != mid: fail("mission_id_mismatch")
    if env.get("mission_sha256") != sha_obj(mission): fail("mission_hash_mismatch")
    handoff=env.get("handoff")
    if not isinstance(handoff,dict): fail("handoff_missing")
    if handoff.get("mission_id") != mid: fail("handoff_mission_id_mismatch")
    if env.get("handoff_sha256") != sha_obj(handoff): fail("handoff_hash_mismatch")
    expect=sha_obj({k:v for k,v in env.items() if k!="envelope_sha256"})
    if env.get("envelope_sha256") != expect: fail("envelope_hash_mismatch")
    root=Path(args.state_root)
    consumed=root/"consumed"/(env["envelope_sha256"]+".json")
    if consumed.exists(): fail("replay_detected",2)
    accepted={
      "schema":"rotclaw.accepted-frontier-result.v1",
      "mission_id":mid,
      "accepted_at":datetime.now(timezone.utc).isoformat(),
      "source_commit":env.get("source_commit"),
      "status":env.get("status"),
      "envelope_sha256":env["envelope_sha256"],
      "handoff":handoff,
      "authority":"DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION"
    }
    atomic_json(root/"accepted"/(mid+".json"),accepted)
    atomic_json(consumed,{"mission_id":mid,"envelope_sha256":env["envelope_sha256"],"consumed_at":accepted["accepted_at"]})
    print("FRONTIER_INGEST_PASS", mid)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    e=sub.add_parser("envelope"); e.add_argument("--mission",required=True); e.add_argument("--handoff",required=True); e.add_argument("--source-commit",required=True); e.add_argument("--out",required=True); e.set_defaults(fn=envelope)
    i=sub.add_parser("ingest"); i.add_argument("--mission",required=True); i.add_argument("--envelope",required=True); i.add_argument("--state-root",required=True); i.set_defaults(fn=ingest)
    a=ap.parse_args(); a.fn(a)
if __name__=="__main__": main()
