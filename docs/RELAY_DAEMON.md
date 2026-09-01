# ROTCLAW Relay Daemon

The Relay Daemon is a transport component, not an authority component.

## Responsibilities

1. Observe validated `rotclaw.mission.v1` files under the Sentinel `frontier-export` queue.
2. Publish each mission through a configured transport.
3. Collect a matching `rotclaw.frontier-result.v1` artifact when available.
4. Deposit the returned envelope into `sentinel/relay/incoming/`.
5. Let `result_consumer.py` invoke `frontier_result.py ingest` for cryptographic binding and replay checks.

The relay never widens `allowed_paths`, `allowed_actions`, `risk_class`, branch authority, secret access or merge authority.

## Transports

### Filesystem

Used for deterministic tests and for two cooperating processes on the same host. Configure `filesystem.outgoing_dir` and `filesystem.incoming_dir`.

### GitHub CLI

Intended for an egress-capable Node01 host. It requires `gh` and a `GH_TOKEN` scoped only to the repository/branch operations the operator intends to permit. The transport publishes the existing bounded mission file and searches workflow artifacts for the matching returned envelope.

Do not put `GH_TOKEN` in repository files, Drive, Library checkpoints or artifacts.

## Consumer authority

`result_consumer.py` only accepts results through the existing closed-loop integrity protocol. Successful results are marked:

`DATA_ONLY_NO_AUTOMATIC_TOOL_EXECUTION`

A result can inform a later decision but cannot autonomously trigger a tool call, Git write, deployment, merge or follow-up mission.

## Example

```bash
export ROTCLAW_LOCAL_HOME=/mnt/data/rotclaw-local
python scripts/relay_daemon.py --config config/relay.example.json --once
python scripts/result_consumer.py --once
```

For a resident Node01 service, run the relay continuously and supervise it independently from the Local Sentinel so a crash in transport cannot stop local health/routing.

## Evidence gate

`scripts/relay_daemon_check.py` uses the filesystem transport to prove:

- a bounded mission is published;
- a matching frontier result is collected;
- the consumer accepts it through the hash/replay protocol;
- accepted authority remains data-only.

This check is mandatory in `.github/workflows/qa.yml`.
