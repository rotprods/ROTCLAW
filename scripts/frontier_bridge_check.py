#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frontier_bridge',ROOT/'scripts/frontier_bridge.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
h={'schema':'rotclaw.frontier-handoff.v1','id':'frontier-check-001','created_at':'2026-08-28T00:00:00Z','prompt':'Update the bounded documentation file and run tests.','reason':'complex_or_sensitive','status':'QUEUED'}
out=m.convert(h,'rotprods/ROTCLAW','main',['docs/frontier-check.md'])
assert out['schema']=='rotclaw.mission.v1'
assert out['risk_class']=='A1'
assert out['work_branch']=='agent/frontier-check-001'
assert out['allowed_paths']==['docs/frontier-check.md']
assert out['allowed_actions']==['read','edit','test']
assert out['requires_live'] is False
assert '.github/**' in out['denied_paths'] and 'delegation/**' in out['denied_paths']
print('FRONTIER_BRIDGE_PASS')
