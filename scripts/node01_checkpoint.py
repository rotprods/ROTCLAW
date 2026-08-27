#!/usr/bin/env python3
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa'/'NODE01_CHECKPOINT.json'

def run(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=20)
        return p.returncode,(p.stdout+p.stderr).strip()[-2000:]
    except Exception as e:
        return 99,f'{type(e).__name__}: {e}'

def git_sha():
    rc,out=run(['git','rev-parse','HEAD'])
    return out.splitlines()[-1] if rc==0 and out else os.environ.get('GITHUB_SHA','UNKNOWN')

def file_sha(path):
    p=Path(path).expanduser()
    if not p.is_file(): return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

def first_line(cmd):
    rc,out=run(cmd)
    return out.splitlines()[0] if rc==0 and out else None

config_root=Path(os.environ.get('ROTCLAW_CONFIG_ROOT',Path.home()/'.config/rotclaw')).expanduser()
state_root=Path(os.environ.get('ROTCLAW_STATE_ROOT',Path.home()/'.local/share/rotclaw-node01')).expanduser()
unit=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')).expanduser()/'systemd/user/rotclaw-router.service'

service={'available':bool(shutil.which('systemctl')),'enabled':None,'active':None}
if service['available']:
    service['enabled']=run(['systemctl','--user','is-enabled','rotclaw-router.service'])[0]==0
    service['active']=run(['systemctl','--user','is-active','rotclaw-router.service'])[0]==0

doc={
 'schema':'rotclaw.node01-checkpoint.v1',
 'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
 'git_sha':git_sha(),
 'versions':{
   'openclaw':first_line(['openclaw','--version']) if shutil.which('openclaw') else None,
   'node':first_line(['node','--version']) if shutil.which('node') else None,
   'python':first_line(['python3','--version']) if shutil.which('python3') else None,
   'docker':first_line(['docker','--version']) if shutil.which('docker') else None,
 },
 'paths':{
   'state_root':str(state_root),
   'config_root':str(config_root),
   'openclaw_config_sha256':file_sha(config_root/'openclaw.json'),
   'systemd_unit_sha256':file_sha(unit),
 },
 'service':service,
 'docker_sandbox_image_present':run(['docker','image','inspect','openclaw-sandbox:bookworm-slim'])[0]==0 if shutil.which('docker') else False,
 'secret_values_recorded':False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc,indent=2))
