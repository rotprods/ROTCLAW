# Security policy

## Threat model
Primary risks: prompt/tool injection, secret exfiltration, malicious dependencies, over-broad GitHub permissions, unsafe shell execution, context poisoning, stale runtime assumptions and false completion claims.

## Controls
- Loopback-only local router by default.
- Secrets only through environment/secret stores; `.env` is ignored.
- Static secret scanning and deterministic artifact hashes.
- Epistemic state (`OBSERVED/CANONICAL/INFERRED/PLANNED/BLOCKED`) on system graph entities.
- Branch/task/repo scoped engineering and review-before-merge.
- Runtime facts expire and must be re-probed.

## Reporting
Open a private security report rather than publishing credentials or exploitable production details in an issue.
