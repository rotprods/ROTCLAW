#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'RELEASE_MANIFEST.json').read_text())
errors=[]
if manifest.get('release_type') not in {'FULL','FULL_COMPOSITE'}:
    errors.append('release_type_not_full')
for p in manifest.get('required_components',[]):
    if not (R/p).is_file(): errors.append('missing:'+p)
# Live qualification is mandatory only when the release claims it.
live_state=manifest.get('live_qualification','NOT_YET_VERIFIED')
qpath=R/'qa/LIVE_QUALIFICATION.json'
if live_state in {'QUALIFIED','PARTIALLY_QUALIFIED'}:
    if not qpath.is_file(): errors.append('missing_live_evidence')
    else:
        q=json.loads(qpath.read_text())
        if q.get('mode')!='LIVE': errors.append('live_evidence_not_live')
        if q.get('overall_state')!=live_state: errors.append('live_state_mismatch')
# Cross-plane tuple can be supplied as a generated checkpoint during promotion.
cp=R/'qa/CROSS_PLANE_CHECKPOINT.json'
if cp.is_file():
    data=json.loads(cp.read_text())
    for key in ('release','release_type','git_sha','ci_conclusion','library_bundle_sha256'):
        if key not in data: errors.append('checkpoint_missing:'+key)
if errors:
    print('PROMOTION_BLOCKED')
    print('\n'.join(errors))
    sys.exit(1)
print('PROMOTION_STATIC_PASS')
print('live_qualification='+live_state)
print('NOTE: CANONICAL promotion still requires external Drive/Library reconciliation and review.')
