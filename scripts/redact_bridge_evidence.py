#!/usr/bin/env python3
import os, sys
from pathlib import Path

if len(sys.argv)<2:
    raise SystemExit('usage: redact_bridge_evidence.py <path> [path...]')
secrets=[os.environ.get('OLLAMA_API_KEY',''),os.environ.get('ROT_ROUTER_TOKEN','')]
secrets=[s for s in secrets if s]
for raw in sys.argv[1:]:
    p=Path(raw)
    files=[p] if p.is_file() else list(p.rglob('*')) if p.is_dir() else []
    for f in files:
        if not f.is_file() or f.stat().st_size>10_000_000: continue
        try: text=f.read_text(errors='strict')
        except Exception: continue
        changed=text
        for secret in secrets:
            changed=changed.replace(secret,'[REDACTED]')
        if changed!=text: f.write_text(changed)
for raw in sys.argv[1:]:
    p=Path(raw)
    files=[p] if p.is_file() else list(p.rglob('*')) if p.is_dir() else []
    for f in files:
        if not f.is_file() or f.stat().st_size>10_000_000: continue
        try: text=f.read_text(errors='strict')
        except Exception: continue
        for secret in secrets:
            if secret in text: raise SystemExit(f'secret remained in evidence: {f}')
print('BRIDGE_EVIDENCE_REDACTION_PASS')
