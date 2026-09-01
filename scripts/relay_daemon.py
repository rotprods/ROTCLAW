#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, os, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(os.environ.get('ROTCLAW_LOCAL_HOME','/mnt/data/rotclaw-local'))
S=BASE/'sentinel'

def now(): return datetime.now(timezone.utc).isoformat()
def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
    os.replace(t,p)
def load(p): return json.loads(Path(p).read_text())
def fail(msg): raise RuntimeError(msg)

class FilesystemTransport:
    def __init__(self,cfg):
        self.out=Path(cfg['outgoing_dir']); self.inc=Path(cfg['incoming_dir'])
        self.out.mkdir(parents=True,exist_ok=True); self.inc.mkdir(parents=True,exist_ok=True)
    def publish(self,mission,path):
        dst=self.out/path.name
        if dst.exists(): return {'status':'ALREADY_PUBLISHED','ref':str(dst)}
        shutil.copy2(path,dst); return {'status':'PUBLISHED','ref':str(dst)}
    def collect(self,mission_id):
        hits=sorted(self.inc.glob(f'*{mission_id}*.frontier-result.json'))
        return hits[-1] if hits else None

class GitHubCLITransport:
    def __init__(self,cfg):
        self.repo=cfg['repo']; self.branch=cfg['branch']; self.artifacts=Path(cfg['artifact_dir'])
        self.artifacts.mkdir(parents=True,exist_ok=True)
        if not shutil.which('gh'): fail('gh_not_installed')
        if not os.environ.get('GH_TOKEN'): fail('GH_TOKEN_required')
    def _run(self,args,check=True):
        p=subprocess.run(['gh',*args],capture_output=True,text=True,timeout=120)
        if check and p.returncode: fail('gh_failed:'+p.stderr[-1000:])
        return p
    def publish(self,mission,path):
        target=f'delegation/inbox/{path.name}'
        encoded=base64.b64encode(path.read_bytes()).decode()
        existing=self._run(['api',f'repos/{self.repo}/contents/{target}','-f',f'ref={self.branch}'],check=False)
        args=['api','--method','PUT',f'repos/{self.repo}/contents/{target}','-f',f'message=relay: enqueue {mission["mission_id"]}','-f',f'content={encoded}','-f',f'branch={self.branch}']
        if existing.returncode==0:
            sha=json.loads(existing.stdout).get('sha')
            if sha: args += ['-f',f'sha={sha}']
        p=self._run(args)
        return {'status':'PUBLISHED','ref':target,'response':json.loads(p.stdout)}
    def collect(self,mission_id):
        p=self._run(['api',f'repos/{self.repo}/actions/artifacts','-f','per_page=100'])
        data=json.loads(p.stdout)
        for a in sorted(data.get('artifacts',[]),key=lambda x:x.get('created_at',''),reverse=True):
            name=a.get('name','')
            if 'rotclaw' not in name: continue
            dest=self.artifacts/str(a['id'])
            if not dest.exists():
                dest.mkdir(parents=True,exist_ok=True)
                run_id=str((a.get('workflow_run') or {}).get('id') or '')
                if run_id:
                    self._run(['run','download',run_id,'-n',name,'-D',str(dest)],check=False)
            hits=list(dest.rglob(f'{mission_id}.frontier-result.json'))
            if hits: return hits[0]
        return None

def transport(cfg):
    if cfg['transport']=='filesystem': return FilesystemTransport(cfg['filesystem'])
    if cfg['transport']=='github_cli': return GitHubCLITransport(cfg['github_cli'])
    fail('unsupported_transport')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--once',action='store_true'); args=ap.parse_args()
    cfg=load(args.config); t=transport(cfg)
    exp=S/'frontier-export'; published=S/'relay'/'published'; incoming=S/'relay'/'incoming'; state=S/'state'/'relay-state.json'
    for d in [exp,published,incoming,state.parent]: d.mkdir(parents=True,exist_ok=True)
    while True:
        last={'schema':'rotclaw.relay-state.v1','timestamp':now(),'transport':cfg['transport'],'published':0,'collected':0}
        for p in sorted(exp.glob('*.json')):
            m=load(p); mid=m.get('mission_id')
            if m.get('schema')!='rotclaw.mission.v1' or not mid: continue
            marker=published/(mid+'.json')
            if not marker.exists():
                r=t.publish(m,p); atomic_json(marker,{'mission_id':mid,'published_at':now(),'transport_result':r,'mission_path':str(p)})
                last['published']+=1
            result=t.collect(mid)
            if result:
                dst=incoming/(mid+'.frontier-result.json')
                if not dst.exists(): shutil.copy2(result,dst); last['collected']+=1
        atomic_json(state,last)
        if args.once: break
        time.sleep(float(cfg.get('poll_seconds',15)))

if __name__=='__main__': main()
