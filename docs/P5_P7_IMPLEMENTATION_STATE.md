# P5–P7 Implementation State

## Git state
- release: v6 FULL_COMPOSITE RC
- branch: `reconstruct/v6-full-composite`
- main remains unchanged

## P5 — Brain Architecture v2
Implemented:
- four memory planes: Public Brain / Private Brain / Runtime Context / Historical Memory
- smallest-sufficient context policy
- epistemic filtering
- privacy/scope contract
- cold-start integration in `AGENTS.md`

## P6 — Three-plane promotion protocol
Implemented:
- GitHub = executable authority
- Drive = operating/control authority
- Library = recovery/history authority
- explicit forward promotion flow
- fail-closed `scripts/promotion_check.py`
- release manifest ancestry requirements

## P7 — Live Authority Qualification Harness
Implemented:
- `schemas/live-qualification.schema.json`
- `scripts/live_qualification.py`
- CONTRACT_ONLY mode for CI
- LIVE mode for real host qualification
- explicit opt-in for cost-bearing model inference
- dimensions for OpenClaw, router, provider catalog, model routing, tool policy, sandbox, Git isolation, restart/recovery, concurrency and soak
- CI invariant that CONTRACT_ONLY must not produce live PASS claims

## Evidence
GitHub Actions run `33005844523` passed on head `2b01aee7def968c1dd2d1a9db8e12ffe4a3637b3`, including promotion gate and live-claim hygiene. Subsequent documentation-only commits require their own CI before final checkpoint promotion.

## Persistent replicas
Drive folder `ROTCLAW_CANONICAL` contains native Brain Architecture v2 and Live Authority Qualification Protocol docs. Library contains `/ROTCLAW/releases/v6/ROTCLAW_V6_P5_P7_CHECKPOINT.json` plus SHA-256.

## Qualification boundary
Live provider inference, real OpenClaw tool enforcement, sandbox isolation, restart/concurrency and production soak remain `NOT_YET_VERIFIED` until executed on a compatible persistent host.
