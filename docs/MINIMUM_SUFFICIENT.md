# /MINIMUM-SUFFICIENT — ROTCLAW Lean Execution Policy

## Purpose

Finish the current goal with the minimum sufficient change.

**Think systemically. Change minimally. Test proportionally to risk.**

A large understanding does not require a large diff. Minimal implementation does not mean minimal assurance.

## Position in the stack

```text
/GRAPH-REFACTOR-V2 or strong planning
        ↓
risk classification
        ↓
/MINIMUM-SUFFICIENT
        ↓
bounded rotclaw.mission.v2
        ↓
Builder
        ↓
post-execution budget reconciliation
        ↓
risk-proportional assurance
        ↓
Reviewer / PR
```

`/GRAPH-REFACTOR-V2` may discover large system implications. `/MINIMUM-SUFFICIENT` prevents that understanding from automatically becoming a large implementation.

## Required pre-execution plan

Every `rotclaw.mission.v2` declares:

- goal;
- non-goals;
- acceptance criteria;
- surfaces that stay untouched;
- change type;
- material risk triggers;
- complexity budget;
- test plan.

## Modes

### LEAN

Default when no systemic risk trigger applies.

Policy defaults:

- single agent first;
- smallest justified file set;
- no new dependency;
- no new config layer/service/state store;
- at most one new abstraction;
- existing relevant tests first;
- at most two justified new tests;
- LIGHT model for mechanical work;
- MEDIUM model for localized logic.

### SYSTEMIC

Automatically required when the mission touches any of:

`authority`, `security`, `secrets`, `pii`, `money`, `persistence`, `migration`, `concurrency`, `event_ordering`, `idempotency`, `side_effects`, `recovery`, `external_provider`, `public_api`, `schema`, `multi_agent_coordination`.

SYSTEMIC does **not** authorize a larger implementation. It only permits assurance breadth to follow the risk and selects a STRONG reasoning tier by default.

## Test law

A new test must protect at least one of:

1. an explicit acceptance criterion;
2. a changed invariant;
3. a historical regression;
4. a material failure mode introduced or exposed by the change.

It must also state why existing tests would miss the regression.

LEAN defaults to at most one main-path and one critical-failure-path test. SYSTEMIC may exceed that only when multiple independent invariants materially require it.

## Complexity budget

Before adding anything, ask whether the goal can be met by:

1. deleting something;
2. simplifying the current owner;
3. correcting the existing primitive;
4. extending an existing primitive.

Only then add a new primitive.

Each of these consumes explicit complexity budget:

- extra file;
- abstraction;
- dependency;
- config layer;
- runtime service;
- state store;
- compatibility path.

## Post-execution budget reconciliation

Planning constraints are not enough. Before a `mission.v2` artifact may be promoted, the trusted harness can run:

```bash
python scripts/mission_gate.py <mission.json> --check-worktree --check-budget
```

`budget_reconcile.py` observes the real worktree and fails closed when execution exceeds the declared budget. The current measurable dimensions are:

- changed file count;
- new test definitions;
- changed dependency manifests;
- new config-layer files;
- new service/daemon/worker files;
- new state/store/database files;
- newly-added class/interface/protocol/trait abstractions.

For zero-budget dimensions, any observed occurrence blocks promotion. The reconciler is deliberately conservative: it detects measurable budget drift; it does not pretend heuristics can infer architectural intent.

Example:

```text
declared max_files = 2
observed files      = 2
→ PASS

declared max_files = 1
observed files      = 2
→ BUDGET_DRIFT / BLOCKED
```

The artifact may report `PASS`; only the trusted reconciler can attest that observed execution stayed within the declared plan.

## Model allocation

Use the cheapest model with demonstrated capability for the risk class:

- mechanical → LIGHT;
- localized logic → MEDIUM;
- systemic/authority/security/concurrency → STRONG.

Model size never raises mission authority.

## Compatibility

Historical `rotclaw.mission.v1` remains accepted so previous evidence stays replayable. New planning should emit `rotclaw.mission.v2`; `mission_gate.py` automatically invokes the minimum-sufficient gate for v2.

## Non-goals

This policy does not replace:

- security review;
- authority boundaries;
- recovery tests;
- `/GRAPH-REFACTOR-V2` architecture reasoning;
- mission path/action gates;
- independent review for high-risk changes.
