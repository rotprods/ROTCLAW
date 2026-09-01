# ROTCLAW local/offline runtime

Verified stack for running OpenClaw with no external API dependency.

## Verified components

- Ollama `0.32.14`, CPU-only extracted runtime.
- Qwen3 `0.6b-q4_K_M` local model.
- OpenClaw `2026.8.1-beta.3 (5831b80)`.
- Node `22.22.3` bundled with the portable OpenClaw runtime.
- Native Ollama provider URL: `http://127.0.0.1:11434` (no `/v1`).

## Evidence

The runtime was reconstructed from SHA-verified GitHub Actions artifacts and executed in the ChatGPT sandbox. Verified operations:

1. Ollama `/api/tags` discovers `qwen3:0.6b-q4_K_M`.
2. Ollama local generation returned exactly `LOCAL_ROT_OK`.
3. GPU backends were removed from the extracted runtime; CPU-only runtime restarted and returned exactly `CPU_PRUNE_OK`.
4. `openclaw config validate --json` returned `valid: true` with zero warnings.
5. `openclaw infer model run --local` returned exactly `OPENCLAW_LOCAL_OK`.
6. `openclaw agent exec` completed a normal local model turn.
7. With a mission-local tool policy containing only `exec`, OpenClaw executed one real tool call, zero tool failures, and wrote the requested workspace proof file.
8. The same infer + tool-call checks passed again after CPU backend pruning.

## Resource footprint

Observed recovery artifacts after pruning:

- Ollama CPU runtime: about 23 MB compressed / 67 MB extracted.
- Qwen3 model store: about 473 MB compressed / 499 MB extracted.
- OpenClaw + Node portable runtime: about 154 MB compressed / 683 MB extracted.

The original Ollama release archive remains the provenance source, but CUDA and Vulkan directories are not required on this CPU worker.

## Canonical OpenClaw config

Use `config/openclaw.local-ollama.json`.

The important provider settings are:

```json
{
  "baseUrl": "http://127.0.0.1:11434",
  "apiKey": "ollama-local",
  "api": "ollama"
}
```

Do **not** append `/v1`; OpenClaw should use Ollama's native API for reliable tool calling.

## Authority posture

Qwen3 0.6B is an L0/local-sentinel model, not the frontier autonomous agent. Recommended duties: health checks, routing, classification, small summaries, deterministic transforms, bounded command execution and fallback/offline operation.

Do not make broad host write/exec permissions part of the default repository config. Grant tool authority per mission or per host policy. The successful tool-call test used a single-tool `exec` policy with the working directory constrained by `openclaw agent exec --cwd`.

## Persistent recovery

ChatGPT Library stores the recovery set under:

`/ROTCLAW/runtime/local/v1/`

including the Ollama CPU runtime, Qwen3 model store, OpenClaw portable runtime and `LOCAL_RUNTIME_MANIFEST.json`.
