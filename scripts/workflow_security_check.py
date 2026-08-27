#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
fail=[]

def check(condition,message):
    if not condition: fail.append(message)

real=(ROOT/'.github/workflows/real-provider-qualification.yml').read_text()
host=(ROOT/'.github/workflows/openclaw-host-qualification.yml').read_text()
qa=(ROOT/'.github/workflows/qa.yml').read_text()

# The provider workflow must never run from untrusted PR/push events.
check('workflow_dispatch:' in real,'real-provider workflow missing workflow_dispatch')
check(not re.search(r'^\s{2}(push|pull_request):',real,re.M),'real-provider workflow has automatic push/PR trigger')
check('secrets.OLLAMA_API_KEY' in real,'real-provider workflow does not use secret store')
check('OLLAMA_API_KEY:' not in real.split('env:',1)[0],'API key appears to be a workflow input')
check('api_key' not in '\n'.join(line.lower() for line in real.splitlines() if 'inputs.' in line),'API key exposed through workflow input')

# All third-party Actions references in every workflow must be immutable full SHAs.
for name,text in [('real-provider',real),('host-qualification',host),('qa',qa)]:
    for line in text.splitlines():
        m=re.search(r'uses:\s*([^\s#]+)',line)
        if not m: continue
        ref=m.group(1)
        if '@' not in ref:
            fail.append(f'{name}: action without ref: {ref}')
            continue
        action,rev=ref.rsplit('@',1)
        if not re.fullmatch(r'[0-9a-f]{40}',rev):
            fail.append(f'{name}: mutable/non-SHA action ref: {action}@{rev}')

# Sensitive artifacts must be redacted before publication.
check('secret remained in evidence' in (ROOT/'scripts/real_provider_qualification.sh').read_text(), 'real-provider fail-closed evidence scan missing')
check('replace(secret' in (ROOT/'scripts/real_provider_qualification.sh').read_text(), 'exact-secret redaction missing')

if fail:
    print('WORKFLOW_SECURITY_FAIL')
    print('\n'.join(fail))
    sys.exit(1)
print('WORKFLOW_SECURITY_PASS')
print('manual_only_provider=true action_refs_pinned=true secret_store_only=true')
