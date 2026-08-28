#!/usr/bin/env python3
import json, os, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    b=Path(td); env={**os.environ,'ROTCLAW_LOCAL_HOME':str(b)}
    for d in ['sentinel/frontier-export','sentinel/relay-wire/out','sentinel/relay-wire/in','sentinel/results']:
        (b/d).mkdir(parents=True,exist_ok=True)
    mission={'schema':'rotclaw.mission.v1','mission_id':'relay-test-001','goal':'x','risk_class':'A1','repository':'rotprods/ROTCLAW','base_branch':'main','work_branch':'agent/relay-test-001','allowed_paths':['docs/x.md'],'denied_paths':['.github/**'],'allowed_actions':['read','edit','test'],'acceptance':['x']}
    mp=b/'sentinel/frontier-export/relay-test-001.json'; mp.write_text(json.dumps(mission))
    handoff={'schema':'rotclaw.mission-handoff.v1','mission_id':'relay-test-001','returncode':0,'stdout':'OK','stderr':''}
    hp=b/'handoff.json'; hp.write_text(json.dumps(handoff))
    ep=b/'sentinel/relay-wire/in/relay-test-001.frontier-result.json'
    subprocess.run(['python3',str(ROOT/'scripts/frontier_result.py'),'envelope','--mission',str(mp),'--handoff',str(hp),'--source-commit','test','--out',str(ep)],check=True,env=env)
    cfg={'transport':'filesystem','poll_seconds':1,'filesystem':{'outgoing_dir':str(b/'sentinel/relay-wire/out'),'incoming_dir':str(b/'sentinel/relay-wire/in')}}
    cp=b/'relay.json'; cp.write_text(json.dumps(cfg))
    subprocess.run(['python3',str(ROOT/'scripts/relay_daemon.py'),'--config',str(cp),'--once'],check=True,env=env)
    assert (b/'sentinel/relay-wire/out/relay-test-001.json').exists()
    assert (b/'sentinel/relay/incoming/relay-test-001.frontier-result.json').exists()
    subprocess.run(['python3',str(ROOT/'scripts/result_consumer.py'),'--once'],check=True,env=env)
    acc=json.loads((b/'sentinel/results/accepted/relay-test-001.json').read_text())
    assert acc['authority']=='DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION'
    bad_mid='relay-test-error'
    bad_mission=dict(mission); bad_mission['mission_id']=bad_mid; bad_mission['work_branch']='agent/'+bad_mid
    bad_mp=b/'sentinel/frontier-export'/(bad_mid+'.json'); bad_mp.write_text(json.dumps(bad_mission))
    bad_env=b/'sentinel/relay/incoming'/(bad_mid+'.frontier-result.json'); bad_env.write_text('{}')
    subprocess.run(['python3',str(ROOT/'scripts/result_consumer.py'),'--once'],check=True,env=env)
    quarantine=b/'sentinel/relay/incoming'/(bad_mid+'.frontier-result.json.error')
    diagnostics=b/'sentinel/relay/incoming'/(bad_mid+'.frontier-result.json.error.log')
    assert not bad_env.exists()
    assert quarantine.exists() and diagnostics.exists()
    snapshot=(quarantine.read_bytes(),diagnostics.read_bytes())
    subprocess.run(['python3',str(ROOT/'scripts/result_consumer.py'),'--once'],check=True,env=env)
    assert snapshot==(quarantine.read_bytes(),diagnostics.read_bytes())
    print('RELAY_RESULT_CONSUMER_PASS')
