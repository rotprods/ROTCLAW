# ROTCLAW

Hardened personal-agent control layer for OpenClaw: bounded context, system graph, model routing, recovery, QA and security governance.

> **Status:** artifact/context/recovery layer is benchmarked; live OpenClaw/provider/tool/sandbox production qualification is intentionally separate and must be proven in the target host.

## Architecture

```text
OpenClaw / agent runtime
        │
        ▼
ROTCLAW policy + bounded context
        │
        ├── SYSTEM_GRAPH v2
        ├── SOUL / AGENTS / SECURITY
        ├── QA + recovery manifests
        └── local model router 127.0.0.1:8787
                         │
                         ▼
                Ollama-compatible upstream
       GLM 5.2 / MiniMax M3 / Kimi K2.6 / DeepSeek V4 Flash
```

## Quick start

```bash
git clone https://github.com/rotprods/ROTCLAW.git
cd ROTCLAW
cp router/router.env.example .env
# edit .env with rotated provider key + a strong local router token
set -a; source .env; set +a
make qa
make preflight
make router
```

Health check:

```bash
curl http://127.0.0.1:8787/healthz
```

## Model profiles
- `coding`, `fast`, `balanced` → `deepseek-v4-flash`
- `research` → `kimi-k2.6`
- `creative` → `minimax-m3`
- `reasoning` → `glm-5.2`

Model names are routing intent, **not evidence that the provider currently exposes those exact IDs**. Run provider discovery/smoke tests before marking them live.

## Security
The API key previously pasted into chat must be considered compromised and rotated. No real credential belongs in this repository. See [SECURITY.md](SECURITY.md).

## Repository map
- `AGENTS.md`, `SOUL.md` — agent governance.
- `context/` — consciousness seed, memory, subagent topology and system graph.
- `router/` — local loopback model router.
- `config/` — model routing and OpenClaw integration templates.
- `scripts/`, `schemas/` — QA/context/recovery machinery.
- `qa/`, `benchmarks/` — evidence and benchmark outputs.
- `.github/workflows/qa.yml` — CI gates.
