#!/usr/bin/env python3
import argparse, fnmatch, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOWED_ACTIONS={"read","edit","test","commit","push_branch","open_pr"}
PROTECTED_BRANCHES={"main","master","production","prod"}
SUPPORTED_SCHEMAS={"rotclaw.mission.v1","rotclaw.mission.v2"}

def fail(msg):
    print("MISSION_BLOCKED",msg,sep="\n"); sys.exit(1)

def match_any(path,patterns):
    return any(fnmatch.fnmatch(path,p) for p in patterns)

def validate(m):
    required=["schema","mission_id","goal","risk_class","repository","base_branch","work_branch","allowed_paths","denied_paths","allowed_actions","acceptance"]
    missing=[k for k in required if k not in m]
    if missing: fail("missing:"+",".join(missing))
    if m["schema"] not in SUPPORTED_SCHEMAS: fail("unsupported_schema")
    if m["risk_class"] not in {"A0","A1","A2","A3"}: fail("invalid_risk_class")
    if m["risk_class"]=="A3": fail("A3_requires_explicit_non_autonomous_authorization")
    if not m["work_branch"].startswith(("agent/","feat/","fix/","reconstruct/","chore/")): fail("unsafe_work_branch_prefix")
    if m["work_branch"] in PROTECTED_BRANCHES or m["base_branch"]==m["work_branch"]: fail("protected_or_same_work_branch")
    if not m["allowed_paths"]: fail("empty_allowed_paths")
    unknown=set(m["allowed_actions"])-ALLOWED_ACTIONS
    if unknown: fail("unknown_actions:"+",".join(sorted(unknown)))
    if m["risk_class"] in {"A0","A1"} and ({"push_branch","open_pr"}&set(m["allowed_actions"])): fail("external_action_exceeds_risk_class")
    if m.get("requires_live") and os.environ.get("ROT_ALLOW_LIVE_MISSION")!="1": fail("live_mission_requires_ROT_ALLOW_LIVE_MISSION=1")
    if m["schema"]=="rotclaw.mission.v2":
        try:
            from minimum_sufficient import validate_execution_policy
            policy=json.loads((ROOT/"config"/"minimum-sufficient-policy.json").read_text())
            validate_execution_policy(m,policy)
        except SystemExit:
            raise
        except Exception as exc:
            fail("minimum_sufficient_gate_error:"+str(exc))

def changed_files(base):
    try:
        p=subprocess.run(["git","diff","--name-only",base+"...HEAD"],cwd=ROOT,capture_output=True,text=True,timeout=10)
        if p.returncode!=0: return []
        return [x.strip() for x in p.stdout.splitlines() if x.strip()]
    except Exception: return []

def worktree_files():
    files=set()
    for cmd in (["git","diff","--name-only","HEAD"],["git","ls-files","--others","--exclude-standard"]):
        try:
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=10)
            if p.returncode==0:
                files.update(x.strip() for x in p.stdout.splitlines() if x.strip())
        except Exception:
            pass
    return sorted(files)

def check_paths(files,m):
    violations=[]
    for f in files:
        if match_any(f,m["denied_paths"]): violations.append(f+":denied")
        elif not match_any(f,m["allowed_paths"]): violations.append(f+":outside_allowed_paths")
    if violations: fail("path_violations:\n"+"\n".join(violations))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mission")
    ap.add_argument("--check-diff",action="store_true")
    ap.add_argument("--check-worktree",action="store_true")
    args=ap.parse_args()
    path=(ROOT/args.mission).resolve() if not Path(args.mission).is_absolute() else Path(args.mission)
    if not path.is_file(): fail("mission_file_not_found")
    m=json.loads(path.read_text()); validate(m)
    if args.check_diff: check_paths(changed_files(m["base_branch"]),m)
    if args.check_worktree: check_paths(worktree_files(),m)
    print("MISSION_PASS")
    print("mission_id="+m["mission_id"])
    print("schema="+m["schema"])
    print("risk_class="+m["risk_class"])
    print("work_branch="+m["work_branch"])
    print("actions="+",".join(m["allowed_actions"]))

if __name__=="__main__": main()
