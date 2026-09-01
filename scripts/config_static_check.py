#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
R=Path(__file__).resolve().parents[1]
errors=[]
def need(ok,msg):
    if not ok: errors.append(msg)

cfg=json.loads((R/'config/openclaw.example.json').read_text())
provider=cfg.get('models',{}).get('providers',{}).get('rot-router',{})
need(provider.get('baseUrl')=='http://127.0.0.1:8787/v1','router baseUrl must be loopback')
ref=provider.get('apiKey',{})
need(ref.get('source')=='env' and ref.get('id')=='ROT_ROUTER_TOKEN','router credential must be env SecretRef')
expected={'deepseek-v4-flash','kimi-k2.6','glm-5.2','minimax-m3'}
need({m.get('id') for m in provider.get('models',[])}==expected,'model set mismatch')
a=cfg.get('agents',{}).get('defaults',{})
need(a.get('modelPolicy',{}).get('allow')==['rot-router/*'],'model allowlist must be rot-router/*')
s=a.get('sandbox',{})
need(s.get('mode')=='all','sandbox mode must be all')
need(s.get('backend')=='docker','sandbox backend must be docker')
need(s.get('scope')=='session','sandbox scope must be session')
need(s.get('workspaceAccess')=='rw','sandbox workspaceAccess must be rw for builder profile')
d=s.get('docker',{})
need(d.get('network')=='none','sandbox network must be none')
need(d.get('readOnlyRoot') is True,'sandbox root must be read-only')
need(d.get('capDrop')==['ALL'],'sandbox must drop ALL capabilities')
t=cfg.get('tools',{})
need(t.get('fs',{}).get('workspaceOnly') is True,'filesystem must be workspaceOnly')
need(t.get('exec',{}).get('host')=='sandbox','exec host must be sandbox')
need(t.get('exec',{}).get('mode')=='ask','exec mode must be ask')
need(t.get('exec',{}).get('strictInlineEval') is True,'strictInlineEval must be true')
need(t.get('elevated',{}).get('enabled') is False,'elevated must be disabled')
need(cfg.get('gateway',{}).get('bind')=='loopback','gateway must bind loopback')
pplug=cfg.get('plugins',{}).get('entries',{}).get('policy',{})
need(pplug.get('enabled') is True and pplug.get('config',{}).get('enabled') is True,'policy plugin must be enabled')
need(pplug.get('config',{}).get('path')=='policy.jsonc','policy path mismatch')
need(pplug.get('config',{}).get('workspaceRepairs') is False,'policy repairs must be disabled')

policy=json.loads((R/'config/policy.jsonc').read_text())
need(policy.get('models',{}).get('providers',{}).get('allow')==['rot-router'],'policy provider allowlist mismatch')
need(policy.get('network',{}).get('privateNetwork',{}).get('allow') is False,'policy private network must be denied')
need(policy.get('gateway',{}).get('exposure',{}).get('allowNonLoopbackBind') is False,'policy must deny non-loopback gateway')
need(policy.get('gateway',{}).get('remote',{}).get('allow') is False,'policy must deny remote gateway')
need(policy.get('tools',{}).get('fs',{}).get('requireWorkspaceOnly') is True,'policy must require workspace-only fs')
need(policy.get('tools',{}).get('elevated',{}).get('allow') is False,'policy must deny elevated')
need(policy.get('sandbox',{}).get('requireMode')==['all'],'policy sandbox mode mismatch')
need(policy.get('sandbox',{}).get('allowBackends')==['docker'],'policy sandbox backend mismatch')

secret_patterns=[re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(r'\bsk-[A-Za-z0-9]{20,}\b')]
for p in R.rglob('*'):
    if p.is_file() and '.git' not in p.parts and p.stat().st_size<1_000_000:
        text=p.read_text(errors='ignore')
        if any(rx.search(text) for rx in secret_patterns): errors.append(f'secret-shaped material: {p.relative_to(R)}')

if errors:
    print('CONFIG_STATIC_FAIL')
    print('\n'.join(errors))
    sys.exit(1)
print('CONFIG_STATIC_PASS')
