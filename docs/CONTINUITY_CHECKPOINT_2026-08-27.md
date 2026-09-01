# ROTCLAW — Continuity Checkpoint — 2026-08-27

**Status:** Release Candidate / DO NOT MERGE  
**Repository:** `rotprods/ROTCLAW`  
**Branch:** `reconstruct/v6-full-composite`  
**Head at checkpoint:** `2ffe259676ff7098ec1e9fcaf5ff2ccfb494e828`  
**PR:** #1 — open, draft, unmerged

## Current architecture

- **GitHub:** executable truth.
- **Google Drive:** control/recovery/knowledge plane.
- **ChatGPT Library:** persistent recovery/history vault.
- **ChatGPT sandbox:** ephemeral control worker; local loopback works, arbitrary outbound DNS/TCP does not.
- **Mission Bridge:** GitHub Actions runner with Internet egress executes bounded OpenClaw missions.

## Mission Bridge

Files:
- `.github/workflows/mission-bridge.yml`
- `config/openclaw.bridge.json`
- `scripts/mission_bridge.py`
- `scripts/redact_bridge_evidence.py`
- `scripts/mission_gate.py`
- `delegation/inbox/*.json`

Security invariants:
- GitHub token is read-only.
- checkout uses `persist-credentials: false`.
- `OLLAMA_API_KEY` is injected only into the ROT router process.
- OpenClaw execution explicitly unsets `OLLAMA_API_KEY`.
- Mission writes are constrained by `allowed_paths` / `denied_paths`.
- `HEAD` must remain equal to `GITHUB_SHA`; agent commits are blocked.
- Evidence is redacted before artifact upload.

## Canary evidence

Mission: `delegation/inbox/bridge-canary-001.json`  
Workflow run: `33075571974`  
Job: `98528754493`

Observed:
- checkout: PASS
- Node setup: PASS
- Python setup: PASS
- mission resolution/gate: PASS
- `Require provider secret`: **FAIL CLOSED**
- OpenClaw/router/provider steps: not started

Root cause: repository Actions secret `OLLAMA_API_KEY` is not configured.

## Prior executed runtime evidence

Component head `33b36ad099c1a5bfd955f9b2e24159250246ea24`:
- OpenClaw `2026.8.1-beta.3`
- host qualification run `33070300421`
- job `98510509241`
- 17/17 checks PASS
- artifact `9645543849`
- SHA-256 `b88215bb3ef4b4998f5714938e7a5d1d428edc8ba6e2c5032123db746a153ac7`

Included real executable evidence: OpenClaw install/config, ROT router, mock-provider E2E, actual exec tool call, sandbox constraints, failover fixture, router restart recovery, concurrency.

## Real provider state

Implemented but **not executed**:
- DeepSeek V4 Flash
- Kimi K2.6
- GLM 5.2
- MiniMax M3
- real-provider invalid-primary → Kimi fallback qualification

Required one-time action:
1. GitHub → ROTCLAW → Settings → Secrets and variables → Actions
2. Add repository secret `OLLAMA_API_KEY`
3. Rerun mission canary
4. Run real-provider qualification
5. Persist evidence in Library/Drive
6. Only then reconsider PR promotion

## Authority rule

Do not infer runtime success from static CI. Do not merge PR #1 until real-provider and persistent Node01 evidence exist.

## Non-claims

- No secret has been written to GitHub by ChatGPT.
- No real-provider inference has been executed through Mission Bridge yet.
- Persistent Node01 durability is not proven.
- Production soak is not proven.
