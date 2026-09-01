# ROTCLAW Delegation Policy

## Objective
Allow agents to complete bounded engineering missions without granting ambient authority over all repositories, branches, secrets, or production systems.

## Default authority
A delegated worker may read broadly enough to understand its mission but may write only inside the mission's explicit repository, branch, paths and actions.

## Risk classes
- A0 — read/analysis only.
- A1 — reversible branch-local edits/tests/commits.
- A2 — external persistent changes such as branch push or PR creation; only when explicitly listed in `allowed_actions`.
- A3 — destructive operations, credentials, permissions, production deployment, force push, direct protected-branch writes. Never autonomous under this policy.

## Hard prohibitions
- no force push
- no direct write to `main`, `master`, release/protected or production branches
- no secret creation or copying into source, logs or evidence
- no mutation outside `allowed_paths`
- denied paths override allowed paths
- no auto-merge
- no production deployment
- no credential/permission mutation
- no claim of tests or live behavior without evidence

## Mission lifecycle
MISSION → CONTEXT COMPILE → SCOPE GATE → BRANCH/WORKTREE → EXECUTE → TEST → SECURITY/DIFF REVIEW → HANDOFF → optional branch push/PR if authorized.

## Handoff minimum
Mission ID, repository, base/work branch, starting SHA, ending SHA, changed paths, commands/tests actually executed, failures/limitations, evidence pointers, and explicit unverified claims.
