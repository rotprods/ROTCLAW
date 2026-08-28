#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(os.environ.get('ROTCLAW_LOCAL_HOME','/mnt/data/rotclaw-local'))
FRONTIER=BASE/'sentinel'/'frontier'
EXPORTED=BASE/'sentinel'/'frontier-exported'
DEFAULT_DENIED=['.github/**','config/**','router/**','scripts/**','.secrets/**','delegation/**']

def fail(msg):
    print('FRONTIER_BRIDGE_BLOCKED',msg,sep='\n'); raise SystemExit(1)

def safe_id(value):
    return re.sub(r'[^A-Za-z0-9._-]+','-',str(value)).strip('-')[:80]

def convert(h, repository, base_branch, allowed_paths):
    if h.get('schema')!='rotclaw.frontier-handoff.v1': fail('unsupported_handoff_schema')
    mid=safe_id(h.get('id') or '')
    if not mid: fail('missing_id')
    prompt=h.get('prompt','')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>12000: fail('invalid_prompt')
    if not allowed_paths: fail('allowed_paths_required')
    return {
      'schema':'rotclaw.mission.v1','mission_id':mid,
      'goal':prompt,'risk_class':'A1','repository':repository,
      'base_branch':base_branch,'work_branch':'agent/'+mid,
      'allowed_paths':allowed_paths,'denied_paths':DEFAULT_DENIED,
      'allowed_actions':['read','edit','test'],
      'acceptance':['Only allowed paths are modified','Required tests pass','Mission handoff is produced'],
      'requires_live':False,'expires_at_utc':None,
      'source':{'type':'local-sentinel','handoff_created_at':h.get('created_at'),'reason':h.get('reason')}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('handoff')
    ap.add_argument('--repository',default='rotprods/ROTCLAW')
    ap.add_argument('--base-branch',default='main')
    ap.add_argument('--allow',action='append',dest='allowed_paths',required=True)
    ap.add_argument('--out')
    args=ap.parse_args()
    p=Path(args.handoff)
    if not p.is_absolute(): p=FRONTIER/p
    if not p.is_file(): fail('handoff_not_found')
    h=json.loads(p.read_text())
    mission=convert(h,args.repository,args.base_branch,args.allowed_paths)
    out=Path(args.out) if args.out else BASE/'sentinel'/'frontier-export'/f"{mission['mission_id']}.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(out.suffix+'.tmp'); tmp.write_text(json.dumps(mission,indent=2,ensure_ascii=False)+'\n'); os.replace(tmp,out)
    print(json.dumps({'status':'EXPORTED','mission_id':mission['mission_id'],'path':str(out)},indent=2))
if __name__=='__main__': main()
