# ROTCLAW Three-Plane Promotion Protocol

## Authority
- GitHub: executable truth (source, config templates, skills, tests, CI).
- Drive: operating/control truth (state, decisions, graph pointers, handoffs, audit).
- Library: recovery truth (immutable release bundles, checksums, Git bundles, historical evidence).

## Forward promotion
BUILD → STATIC GATES → QA → SECURITY → ANCESTRY → LIVE GATES (when claimed) → RELEASE MANIFEST → DRIVE CHECKPOINT → LIBRARY SNAPSHOT → COLD RESTORE → CROSS-PLANE RECONCILIATION → CANONICAL.

## Required reconciliation tuple
Every plane must agree on:
- repository
- release
- release_type
- git_branch
- git_sha
- CI run/conclusion
- release bundle SHA-256 when a bundle exists
- live qualification state

## Directionality
- GitHub may emit a release checkpoint to Drive/Library.
- Drive may request/source work but never overwrites executable source without PR.
- Library may restore source/state after disaster but never auto-overwrites GitHub.
- Runtime workers are replaceable and are never an authority plane.

## Fail-closed rules
Promotion is blocked if any required tuple field disagrees, ancestry loses a required component, a secret is detected, recovery fails, CI fails, or a live claim lacks live evidence.

## Release classes
- FULL: complete canonical executable surface.
- FULL_COMPOSITE: complete surface reconstructed from multiple authoritative ancestors.
- OVERLAY: intentional partial addition/modification.
- CONTEXT_ONLY: memory/graph/context projection only.
- EVIDENCE_ONLY: QA/audit/benchmark evidence only.

A numerically newer release class never implicitly supersedes a FULL lineage.
