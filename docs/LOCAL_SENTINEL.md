# ROTCLAW Local Sentinel

The Local Sentinel is the resident L0 control loop for the offline ROTCLAW runtime.

## Responsibilities

- heartbeat and runtime state
- local Ollama health monitoring and self-heal
- persistent mission queue (`inbox -> processing -> outbox/failed`)
- interrupted-lease replay after Sentinel restart
- bounded local Qwen3 execution for low-risk tasks
- deterministic escalation of broad/sensitive tasks into a frontier handoff queue

## Mission schema

```json
{
  "schema": "rotclaw.local-mission.v1",
  "id": "mission-id",
  "type": "health|classify|summarize|route|dispatch|local_agent",
  "prompt": "..."
}
```

The daemon is fail-closed on unknown schemas, unknown mission types, and oversized prompts.

## Routing policy

`LOCAL` is appropriate for bounded, low-risk work such as health checks, classification, extraction, concise summarization and small transformations.

`FRONTIER` is mandatory for complex or sensitive work such as production/deployment, merges/PR authority, broad refactors, credentials/secrets, security decisions, destructive operations, database migrations, architecture, network changes, payments/legal, or uncertain/high-complexity work.

A frontier decision creates a `rotclaw.frontier-handoff.v1` JSON artifact instead of letting the small local model execute the work.

## Evidence executed on the ChatGPT worker

- Sentinel heartbeat: PASS
- Ollama self-heal after deliberate process kill: PASS
- Qwen3 classify mission: PASS (~1.9 s observed)
- Qwen3 summarize mission: PASS (~1.5 s observed)
- deterministic LOCAL routing: PASS
- deterministic FRONTIER routing + queued handoff: PASS
- OpenClaw local-agent mission: PASS (`SENTINEL_AGENT_OK`, return code 0)
- interrupted processing lease replay after Sentinel restart: PASS

## Authority boundary

The local 0.6B model is an L0 sentinel, not a production authority. It must not autonomously merge, deploy, handle secrets, perform broad refactors, or make high-impact security/business decisions. Those tasks are escalated.

## Runtime dependency

The Sentinel expects the offline runtime described by `docs/LOCAL_OFFLINE_RUNTIME.md`, including:

- Ollama on `127.0.0.1:11434`
- `qwen3:0.6b-q4_K_M`
- OpenClaw portable runtime
- `ROTCLAW_LOCAL_HOME` (default `/mnt/data/rotclaw-local`)
