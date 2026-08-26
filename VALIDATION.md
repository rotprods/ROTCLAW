# Validation status

## Qualified artifact layer
The repository validates graph structure, epistemic state, context boundaries, static secret hygiene, deterministic hashing, adversarial graph mutations, recovery manifests and runtime preflight syntax/execution.

## Live qualification boundary
A green repository CI does **not** prove live OpenClaw schema acceptance, Ollama provider authentication, model-ID availability, model quality, Docker/sandbox isolation, tool-policy enforcement or production reliability. Those gates must run on the target host with the exact OpenClaw version and rotated credentials.

## Required production promotion gates
1. Exact OpenClaw version + config schema acceptance.
2. Provider discovery and smoke inference for every routed model.
3. Tool allow/deny adversarial tests.
4. Filesystem/network sandbox isolation tests.
5. Git branch/repo scope enforcement.
6. Restart/recovery and concurrency tests.
7. Sustained soak with timeout/retry/circuit-breaker failure injection.
8. Secret-exfiltration and prompt-injection suite.
