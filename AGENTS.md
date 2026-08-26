# AGENTS.md — ROTCLAW operating contract

## Cold-start brain load
Before material work, read in order:
1. `brain/MEMORY_SEED.md`
2. `brain/SOURCE_REGISTRY.json`
3. `brain/ANCESTRY_GATE.md`
4. `history/HISTORICAL_REGRESSION.md`
5. `context/SYSTEM_GRAPH.json`

Never infer that a newer snapshot supersedes an older FULL release without passing the ancestry gate.

## Default workflow
1. DEFINE GOAL — success criteria, constraints, authority, risk.
2. OBSERVE — inspect repo/runtime before proposing changes.
3. GRAPH — identify affected nodes, dependencies and write scopes.
4. PLAN — smallest reversible execution path.
5. EXECUTE — branch/task scoped.
6. VERIFY — tests, lint, security, diff review, runtime smoke where possible.
7. RECONCILE — compare claims to evidence; downgrade unsupported claims.
8. HANDOFF — state, evidence, hashes, next exact action.

## Mutation classes
- A0 read-only: autonomous.
- A1 reversible local/branch writes: autonomous inside explicit scope.
- A2 external/persistent changes: require clear task authorization.
- A3 destructive, credential, production or permission changes: explicit confirmation and rollback plan.

## Release integrity
Every release must declare `FULL`, `OVERLAY`, `CONTEXT_ONLY`, or `EVIDENCE_ONLY`. FULL/CANONICAL promotion requires component-level ancestry reconciliation. Silent component disappearance is a release-blocking failure.

## Git policy
Delegated changes target a dedicated branch. No force-push, no direct production deployment, no secret creation in repository content.
