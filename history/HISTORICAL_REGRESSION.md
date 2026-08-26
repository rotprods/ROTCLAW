# ROTCLAW — Historical Regression & Evidence Ledger

Captured: 2026-08-26

## Purpose
Reconstruct the OpenClaw/ROTCLAW project from original intent through current published state while separating execution evidence from historical claims.

## Source authority
1. Executed test evidence and hashes.
2. GitHub published state.
3. Persisted historical snapshots.
4. Current ephemeral worker state.
5. Conversation intent and design decisions.
6. Unsupported historical claims.

## Evolution
### v1 — operational overlay
The earliest recoverable overlay contained the operating surface that later snapshots partially omitted: OpenClaw config, install/verify scripts, security policy + threat model, workspace AGENTS/SOUL/IDENTITY/USER/TOOLS/MEMORY, policy config, and the initial skills (`define-goal`, `gauntlet-loop`, `graph-engineering`, `model-router`, `vibecarrusel`).

### persistence investigation
Repeated workers showed that execution environments are reconstructible while artifacts can be rehydrated. Durable state therefore belongs in Git/Library/graph/memory rather than in a particular process or worker filesystem.

### v2 — consciousness/context projection
Added ACTA_DE_CONSCIENCIA, MEMORY seed, SYSTEM_GRAPH, SUBAGENTS and runtime preflight. Historical regression later showed that this projection did not carry forward the complete v1 operational surface. It must therefore be classified as CONTEXT_ONLY rather than a full replacement.

### v3 — QA/Gauntlet
Added graph schema, QA/adversarial scripts, context compiler, benchmarks and checksums.

### v4 — 50-loop hardening
A 50-loop regression exposed and fixed real defects, including context byte-budget accounting and a self-referential recovery manifest. Final artifact-level evidence included clean reruns, adversarial graph mutation detection, deterministic canonical hashing and cold-restore verification. Live OpenClaw/provider/tool/sandbox qualification remained a separate domain.

### v5 — published ROTCLAW control plane
Published router, model-routing profiles, provider template, Makefile/CI, top-level governance files, graph/context/recovery assets and QA evidence to `rotprods/ROTCLAW`.

## Primary historical defect
The transition from v1 to v2 was a **snapshot substitution**: a partial context projection received a newer version label and later lineages inherited it without automatically reabsorbing all v1 operational components.

This did not destroy v1 because the snapshot remained recoverable, but it created silent ancestry loss in later bundles.

## Permanent rules
- Every release declares `FULL`, `OVERLAY`, `CONTEXT_ONLY`, or `EVIDENCE_ONLY`.
- A newer partial artifact cannot supersede the previous FULL artifact.
- FULL promotion requires ancestry-preservation checks.
- Removed/replaced components require an explicit migration/tombstone record.
- Runtime capabilities expire and must be re-probed.
- Static QA cannot be promoted to live provider/tool/sandbox evidence.
- Public-safe exports never become the private/full canonical brain automatically.
- Canonical recovery excludes self-referential QA outputs.

## Current target
Build a FULL/COMPOSITE successor that restores the recoverable v1 operating surface into the current hardened ROTCLAW lineage, validates configuration against the pinned OpenClaw upstream version, and executes live authority qualification on a compatible host.
