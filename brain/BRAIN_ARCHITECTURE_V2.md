# ROTCLAW Brain Architecture v2

## Purpose
Prevent context leakage, historical amnesia, and unsupported promotion by separating memory into authority and sensitivity planes.

## Four memory planes

### 1. Public Brain
Repository-safe operating knowledge: architecture, release rules, commands, public project context, schemas, and provenance pointers. Source: GitHub.

### 2. Private Brain
User/project-specific durable knowledge that must not be published. Source: ChatGPT Library and scoped Drive knowledge stores. Injected only when task scope authorizes it.

### 3. Runtime Context
Fresh observations about the current worker: runtime capabilities, branch/SHA, available tools, current task, ephemeral outputs. Runtime facts have TTL and are never treated as durable truth without checkpointing.

### 4. Historical Memory
Append-only lineage: releases, manifests, decisions, regressions, recovery bundles, checksums, and source registry. Source: Library recovery vault plus Git/Drive pointers.

## Context-pack policy
A task receives the smallest sufficient pack. Compilation order:
1. task goal + authorization scope
2. current Git source state
3. public brain
4. project-scoped private brain if authorized
5. fresh runtime observations
6. only relevant historical ancestry/provenance

Default exclusions: unrelated private projects, credentials, financial/identity/intimate data, PLANNED/BLOCKED graph facts, stale runtime facts, and whole-library dumps.

## Epistemic contract
Every durable assertion is OBSERVED, CANONICAL, INFERRED, PLANNED, or BLOCKED. Only OBSERVED/CANONICAL enter default execution context. Inference must not silently promote itself.

## Privacy contract
Secrets never live in GitHub, Drive documents, Library brain text, release manifests, or QA logs. Private brain is separated from public recovery artifacts. Sensitive context is injected task-by-task and not propagated globally.

## Promotion rule
No memory plane can change executable authority by itself. GitHub changes require branch/PR gates; Drive records state/decisions; Library proves ancestry/recovery. A CANONICAL release requires all required planes to agree on release, Git SHA, hashes, and qualification state.
