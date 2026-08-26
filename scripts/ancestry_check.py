#!/usr/bin/env python3
from pathlib import Path
import json, sys
R = Path(__file__).resolve().parents[1]
m = json.loads((R / 'RELEASE_MANIFEST.json').read_text())
missing = [p for p in m['required_components'] if not (R / p).is_file()]
errors = []
if m.get('release_type') != 'FULL_COMPOSITE': errors.append('release_type')
if missing: errors.append('missing:' + ','.join(missing))
if errors:
    print('ANCESTRY_FAIL')
    print('\n'.join(errors))
    sys.exit(1)
print(f"ANCESTRY_PASS {len(m['required_components'])} required components present")
