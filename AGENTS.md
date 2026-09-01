# AGENTS.md — ROTCLAW operating contract

## Cold-start brain load
Before material work, read in order:
1. `brain/MEMORY_SEED.md`
2. `brain/BRAIN_ARCHITECTURE_V2.md`
3. `brain/SOURCE_REGISTRY.json`
4. `brain/ANCESTRY_GATE.md`
5. `history/HISTORICAL_REGRESSION.md`
6. `docs/PROMOTION_PROTOCOL.md`
7. `delegation/POLICY.md`
8. `context/SYSTEM_GRAPH.json`

Never infer that a newer snapshot supersedes an older FULL release without passing the ancestry gate.

## Context minimization
Compile the smallest sufficient context pack. Public brain is always eligible; private brain is task-scoped and authorization-scoped; runtime facts must be freshly probed; historical memory is loaded only when ancestry/provenance is relevant. Never inject unrelated private projects or secret material.

## Default workflow
1. DEFINE GOAL — success criteria, constraints, authority, risk.
2. OBSERVE — inspect repo/runtime before proposing changes.
3. GRAPH — identify affected nodes, dependencies and write scopes.
4. PLAN — smallest reversible execution path.
5. EXECUTE — branch/task scoped.
6. VERIFY — tests, lint, security, diff review, runtime smoke where possible.
7. RECONCILE — compare claims to evidence; downgrade unsupported claims.
8. HANDOFF — state, evidence, hashes, next exact action.

## Delegated missions
Autonomous repository work must have a `rotclaw.mission.v1` contract and pass `scripts/mission_gate.py` before mutation. The mission defines repository, base/work branch, allowed/denied paths, allowed actions, acceptance criteria, risk class and whether live access is required. A3 is never autonomous. Denied paths override allowed paths. No auto-merge.

## Mutation classes
- A0 read-only: autonomous.
- A1 reversible local/branch writes: autonomous inside explicit scope.
- A2 external/persistent changes: only when the mission explicitly authorizes the external action.
- A3 destructive, credential, production or permission changes: explicit human authorization and rollback plan; never autonomous under the mission gate.

## Release integrity
Every release must declare `FULL`, `FULL_COMPOSITE`, `OVERLAY`, `CONTEXT_ONLY`, or `EVIDENCE_ONLY`. FULL/CANONICAL promotion requires component-level ancestry reconciliation. Silent component disappearance is a release-blocking failure.

## Live-claim discipline
Static QA cannot qualify live provider inference, OpenClaw tool enforcement, sandbox isolation, restart recovery, concurrency, or production reliability. Use `scripts/live_qualification.py --live`; blocked/not-run dimensions remain unqualified. Never convert absence of evidence into PASS.

## Three-plane authority
GitHub = executable truth. Drive = operating/control truth. Library = recovery/history truth. A runtime worker is never authoritative. CANONICAL promotion requires cross-plane agreement plus cold-restore evidence.

## Git policy
Delegated changes target a dedicated branch. No force-push, no direct protected-branch write, no direct production deployment, no secret creation in repository content, and no auto-merge.
