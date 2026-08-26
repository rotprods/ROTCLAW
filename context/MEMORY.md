# MEMORY.md — PUBLIC SAFE SEED

Status: SAFE-TO-COMMIT
Scope: GLOBAL_TECHNICAL
Sensitivity: PUBLIC

## Durable technical invariants
- Git is executable truth; persistent stores hold operational state; sandboxes are replaceable compute.
- Runtime hardware/tool versions are observations, not eternal facts. Re-probe on every cold start.
- No raw secrets, private user facts, financial data, identity details or private project knowledge belong in this public repository.
- Private operator context must be injected from a local/private memory layer that is excluded by `.gitignore`.
- Agent work is bounded by repo + task + branch scope and must produce evidence before completion claims.
- Parallel writers require non-overlapping scopes or revision/lease fencing.
- Context compilation loads the smallest sufficient verified neighborhood.

## Revalidation rule
Runtime facts MUST be treated as stale after the configured TTL and re-measured before they authorize behavior.
