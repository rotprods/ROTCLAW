---
name: gauntlet-loop
description: Run iterative adversarial QA loops over an artifact or system until measurable defects stop decreasing or target evidence is reached.
user-invocable: true
---
# Gauntlet Loop

Each loop: inspect → score by vertical → identify top defects → implement fixes → regression test → rescore. Use explicit dimensions relevant to the artifact: correctness, security, UX, performance, maintainability, observability and recovery. Never inflate scores. Stop on target attainment, diminishing returns, or a concrete blocker; record residual gaps and unqualified runtime domains.
