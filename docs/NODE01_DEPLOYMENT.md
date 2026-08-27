# ROTCLAW Node 01 — Persistent Deployment Contract

## Purpose
Node 01 is the first persistent execution authority for ROTCLAW. GitHub Actions remains an ephemeral qualification host and must never be treated as durable production state.

## Required host posture
- Linux host under operator control for the supervised `systemd --user` path
- persistent filesystem
- Node.js >= 22.22.3
- Python 3
- Git
- Docker engine reachable by OpenClaw
- outbound HTTPS for the configured model provider
- loopback-only ROT router and OpenClaw interfaces unless an explicit exposure review approves otherwise

macOS can use the bootstrap and foreground router path, but the supplied persistent supervisor contract is Linux/systemd-specific.

## Bootstrap
From a checked-out `reconstruct/v6-full-composite` tree:

```bash
bash scripts/node01_bootstrap.sh
```

The bootstrap creates:
- `~/.config/rotclaw/openclaw.json`
- `~/.config/rotclaw/node01.env` mode `0600`
- `~/.local/share/rotclaw-node01/start-router.sh`
- `~/.local/share/rotclaw-node01/verify-node01.sh`
- pinned `openclaw-sandbox:bookworm-slim` image

No credential is written into the repository. The generated router launcher fails closed if either `ROT_ROUTER_TOKEN` or `OLLAMA_API_KEY` is empty.

## Secret injection
Populate only on the host:

```bash
OLLAMA_API_KEY=...
ROT_ROUTER_TOKEN=...
```

Optional mapping if provider model IDs differ from ROTCLAW canonical IDs:

```bash
ROT_MODEL_DEEPSEEK=deepseek-v4-flash
ROT_MODEL_KIMI=kimi-k2.6
ROT_MODEL_GLM=glm-5.2
ROT_MODEL_MINIMAX=minimax-m3
```

The public canonical model names stay stable while the router maps them to provider-specific IDs at runtime.

## Persistent supervised router
On Linux with a user systemd session:

```bash
bash scripts/node01_install_service.sh
systemctl --user status rotclaw-router.service
journalctl --user -u rotclaw-router.service
```

The generated user service applies:
- `Restart=on-failure`
- loopback router binding inherited from ROTCLAW defaults
- `NoNewPrivileges=true`
- `PrivateTmp=true`
- `ProtectSystem=strict`
- `ProtectHome=read-only`
- explicit writable state/config paths only
- `RestrictSUIDSGID=true`
- `LockPersonality=true`

This is a deployment contract, not proof of persistent-host durability. Durability becomes evidence only after execution on Node 01.

## Runtime checkpoint
Generate a secret-free machine-readable checkpoint with:

```bash
python scripts/node01_checkpoint.py
```

It writes `qa/NODE01_CHECKPOINT.json` containing Git SHA, observed runtime versions, hashes of the active OpenClaw config and systemd unit, service state, and sandbox-image presence. It explicitly records `secret_values_recorded=false` and never serializes environment values.

## Qualification sequence

Preferred supervised path:

```bash
bash scripts/node01_install_service.sh
~/.local/share/rotclaw-node01/verify-node01.sh
set -a; source ~/.config/rotclaw/node01.env; set +a
bash scripts/real_provider_qualification.sh qa/node01-real
python scripts/node01_checkpoint.py
```

Manual foreground fallback:

```bash
~/.local/share/rotclaw-node01/start-router.sh
```

A Node 01 cannot be promoted merely because OpenClaw starts. Promotion requires evidence for:
1. all four real model routes;
2. real fallback/failover behavior;
3. runtime tool policy;
4. sandbox negative tests;
5. restart/recovery;
6. concurrent delegated missions;
7. bounded soak;
8. Git branch/path isolation;
9. no secret leakage in evidence;
10. recovery checkpoint replicated to GitHub/Drive/Library control planes.

## Authority
Node 01 may execute A0/A1 missions after qualification. A2 actions require explicit mission grants. A3 actions remain non-autonomous. Node 01 never receives implicit permission to merge protected branches, force-push, deploy production, rotate credentials, or widen its own scope.

## GitHub Actions real-provider gate
`.github/workflows/real-provider-qualification.yml` is manual-only and uses the `OLLAMA_API_KEY` Actions secret. Do not pass secrets as workflow inputs. The workflow fails closed if the secret is absent and redacts exact secret values from evidence before artifact publication.

## Current boundary
The ephemeral GitHub host has demonstrated OpenClaw installation/config validation, ROT router E2E, sandbox tool execution, rootfs/network negative tests, capability drop, no-new-privileges, non-root execution, explicit gateway-host override denial, bounded four-way concurrency, injected fallback, and router restart recovery. Persistent-host durability, real-provider inference, persistent OpenClaw daemon recovery, and production soak remain separate claims until Node 01 executes them.
