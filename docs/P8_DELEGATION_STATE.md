# P8 — Autonomous Delegation Layer

## Implemented control plane
ROTCLAW can now represent bounded engineering missions as `rotclaw.mission.v1` contracts.

A mission explicitly defines:
- repository
- base branch
- dedicated work branch
- allowed paths
- denied paths
- allowed actions
- A0/A1/A2/A3 risk class
- acceptance criteria
- optional live requirement

`script/mission_gate.py` is intentionally fail-closed. A3 cannot execute autonomously; A0/A1 cannot request branch push or PR creation; live missions require explicit runtime opt-in; denied paths override allowed paths.

## CI
The public example mission is validated on every push/PR. This proves the contract/gate machinery, not that a live agent has been granted GitHub write authority.

## Remaining live qualification
To qualify autonomous delegation end-to-end we still need a persistent worker that can:
1. receive a signed/scoped mission,
2. create a bounded branch/worktree,
3. execute only allowed tools/paths,
4. run tests/security review,
5. push/open PR only when A2 explicitly authorizes it,
6. emit a verifiable handoff,
7. demonstrate denial of out-of-scope writes and protected-branch mutations.

No auto-merge or production deployment is part of the autonomous authority model.
