#!/usr/bin/env python3
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mission')
    ap.add_argument('--out',default='delegation/outbox')
    args=ap.parse_args()
    mission_path=(ROOT/args.mission).resolve() if not Path(args.mission).is_absolute() else Path(args.mission)
    mission=json.loads(mission_path.read_text())
    out=(ROOT/args.out); out.mkdir(parents=True,exist_ok=True)
    prompt=f'''You are ROTCLAW executing a bounded delegated mission on an ephemeral CI worker.\n\nMISSION JSON:\n{json.dumps(mission,indent=2)}\n\nHard constraints:\n- Work only inside this repository checkout.\n- Modify only paths matching allowed_paths and never denied_paths.\n- Do not access environment variables, credentials, git credential stores, /proc/*/environ, or network endpoints except through the configured model provider.\n- Never push, merge, deploy, modify protected branches, or alter workflow/secrets/config unless explicitly allowed by the mission and risk class.\n- Prefer deterministic edits and run the smallest sufficient tests.\n- Finish with a concise summary containing changed files, tests run, unresolved risks, and acceptance status.\n- If the mission cannot be completed within its authority, stop and explain rather than widening scope.\n'''
    cmd=['openclaw','agent','exec',prompt,'--config',str(ROOT/'config/openclaw.bridge.json'),'--cwd',str(ROOT),'--model','rot-router/deepseek-v4-flash','--json','--timeout','900']
    started=time.time()
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    result={
      'schema':'rotclaw.mission-handoff.v1',
      'mission_id':mission.get('mission_id'),
      'returncode':p.returncode,
      'duration_seconds':round(time.time()-started,3),
      'stdout':p.stdout,
      'stderr':p.stderr,
    }
    (out/f"{mission.get('mission_id','mission')}.json").write_text(json.dumps(result,indent=2)+'\n')
    if p.returncode!=0:
        print(p.stdout)
        print(p.stderr,file=sys.stderr)
        sys.exit(p.returncode)
    print('MISSION_BRIDGE_EXEC_PASS')

if __name__=='__main__': main()
