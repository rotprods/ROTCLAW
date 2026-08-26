# AGENTS.md — ROTCLAW operating contract

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

## Git policy
Delegated changes target a dedicated branch. No force-push, no direct production deployment, no secret creation in repository content.
