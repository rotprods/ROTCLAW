# ROTCLAW Closed Loop Protocol v1

## Objective

Close the authority-preserving loop:

`Local Sentinel → Frontier handoff → bounded mission → Mission Bridge → redacted result → integrity envelope → local ingest → data-only accepted result`.

A returned frontier result never gains tool authority merely by arriving.

## Outbound binding

The Local Sentinel produces `rotclaw.frontier-handoff.v1`. `scripts/frontier_bridge.py` converts it into `rotclaw.mission.v1` only when repository and allowed paths are explicitly supplied. The mission remains subject to `scripts/mission_gate.py`.

## Frontier execution

`.github/workflows/mission-bridge.yml` executes the mission on an ephemeral runner. Provider credentials are isolated in the router process. OpenClaw does not inherit the provider key. Working-tree boundaries and unchanged `HEAD == GITHUB_SHA` are enforced before evidence is accepted.

## Result envelope

After secret redaction, `scripts/frontier_result.py envelope` creates `rotclaw.frontier-result.v1` containing:

- `mission_id`
- canonical SHA-256 of the original mission
- canonical SHA-256 of the redacted mission handoff
- producing source commit
- execution status
- the redacted handoff
- SHA-256 of the complete envelope payload

The envelope is included in the Mission Bridge artifact.

## Local ingest

`frontier_result.py ingest` requires both the original mission and the returned envelope. It rejects:

- unsupported schemas
- mission ID mismatch
- original mission mutation
- handoff mutation
- envelope mutation
- duplicate/replayed envelopes

Accepted results are stored under a state root as:

```text
results/
├── accepted/<mission_id>.json
└── consumed/<envelope_sha256>.json
```

The accepted object is explicitly marked:

`DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION`

No tool call, Git write, deployment, follow-up mission or authority escalation is triggered by ingest.

## Example ingest

```bash
python scripts/frontier_result.py ingest \
  --mission delegation/inbox/<mission>.json \
  --envelope /path/to/<mission>.frontier-result.json \
  --state-root /mnt/data/rotclaw-local/sentinel/results
```

## Replay model

Replay identity is the integrity hash of the full returned envelope. The first accepted ingest writes a consumed marker atomically. A second ingest of the same envelope is rejected with `replay_detected`.

## Next-action policy

Any follow-up action must be created as a new mission with a new mission ID and pass normal routing/authority checks. A frontier result may inform that decision, but it cannot authorize it.

## CI

`scripts/frontier_result_check.py` verifies positive ingest plus fail-closed behavior for replay, mission mutation and returned handoff tampering. The check is mandatory in `.github/workflows/qa.yml`.
