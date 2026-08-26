# ROTCLAW Ancestry Preservation Gate

A release may be promoted to FULL/CANONICAL only if:

1. It identifies the previous FULL release and exact source hash.
2. Every previous component is one of: `PRESERVED`, `MIGRATED`, `REPLACED`, `INTENTIONALLY_REMOVED`.
3. `REPLACED`/`INTENTIONALLY_REMOVED` components include rationale, migration path, security impact and recovery reference.
4. Critical surfaces cannot disappear silently: configuration, bootstrap/install, security/threat model, agent workspace, memory contract, skills, schemas, tests, recovery and provenance.
5. A machine-readable component manifest is diffed in CI.
6. A public-safe export is a projection and can never automatically become the private/full canonical source.
7. Failed ancestry checks block release promotion.

Historical regression prevented by this gate: a context-only successor silently dropping operational components from an earlier full overlay.
