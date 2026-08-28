#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path

BASE=Path(os.environ.get('ROTCLAW_LOCAL_HOME','/mnt/data/rotclaw-local'))
S=BASE/'sentinel'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.parse_args()
    incoming=S/'relay'/'incoming'; missions=S/'frontier-export'; results=S/'results'
    incoming.mkdir(parents=True,exist_ok=True); results.mkdir(parents=True,exist_ok=True)
    processed=0
    for env in sorted(incoming.glob('*.frontier-result.json')):
        mid=env.name.removesuffix('.frontier-result.json'); mission=missions/(mid+'.json')
        if not mission.exists():
            continue
        p=subprocess.run(['python3',str(Path(__file__).with_name('frontier_result.py')),'ingest','--mission',str(mission),'--envelope',str(env),'--state-root',str(results)],capture_output=True,text=True)
        if p.returncode==0:
            env.rename(incoming/(env.name+'.consumed')); processed+=1
        elif p.returncode==2:
            env.rename(incoming/(env.name+'.replay'))
        else:
            (incoming/(env.name+'.error')).write_text(p.stderr+p.stdout)
    print(json.dumps({'processed':processed,'authority':'DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION'}))

if __name__=='__main__': main()
