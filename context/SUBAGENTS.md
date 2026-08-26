# ROTCLAW — Subagent Topology

All subagents operate over one canonical ROTCLAW system graph. They never create an independent source of truth.

## Roles
1. `executive-orchestrator` — route mission/project, compile task graph, choose bounded context and model.
2. `inventory-historian` — enumerate sources/artifacts, coverage, provenance and historical gaps. Read-first.
3. `ingestion-engineer` — hash/normalize/checkpoint source imports; cannot mutate raw originals.
4. `graph-memory-engineer` — entity/relation/temporal memory projection; no low-confidence fact promotion.
5. `project-state-steward` — GOAL/STATE/TASKS/DECISIONS/HANDOFF with expected-revision checks.
6. `git-artifact-steward` — repo/branch/commit/PR lineage; branch-scoped, no direct main mutation by default.
7. `security-privacy-guardian` — secret scan, scope enforcement, least privilege and sensitivity redaction; veto authority on unsafe mutation.
8. `qa-reconciliation` — deterministic tests, replay/hash/duplicate/provenance checks; challenges completion claims.
9. `context-compiler` — smallest sufficient context pack, permission-filtered and provenance-linked.
10. `handoff-recovery` — cold-start acta + next exact action + artifact hashes.

## Concurrency law
- One canonical task lease per write scope unless explicitly sharded.
- Parallel research/read work is allowed.
- Parallel writers require non-overlapping graph/repo scopes or expected-version fencing.
- Any collision becomes an explicit reconciliation event; never last-write-wins silently.

## Runtime law
At each worker start, re-measure CPU/RAM/disk/network/tool versions. Runtime fingerprints are evidence, not permanent hardware promises.

## Qualification boundary
Do not mark a subagent run as OpenClaw-executed until the exact target runtime passes gateway/CLI, provider, sandbox, tool-policy and recovery acceptance gates.
