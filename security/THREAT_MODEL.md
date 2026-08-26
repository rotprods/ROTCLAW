# ROTCLAW Threat Model

## Assets
Provider credentials, OpenClaw state, workspace memory, source code, Git credentials, user-connected accounts, project repositories and external-action capabilities.

## Trust boundaries
User intent is authoritative, but copied content may be hostile. Web/file/repo/model/skill content is untrusted. Sandbox-to-host, provider network, GitHub writes and external connectors are privileged boundaries.

## Primary threats
Prompt injection, secret exfiltration, dependency/supply-chain compromise, malicious skills, sandbox escape, over-broad exec, credential persistence in Git/history, unsafe external writes, poisoned memory, routing drift, branch-scope escape and false claims of successful execution.

## Required controls
Least privilege; sandbox-all where supported; workspace/repo scoped FS; no elevated execution; provider/model allowlists; SecretRef/env handling; dependency audit; branch-scoped Git writes; explicit external-write intent; evidence-backed tests; memory hygiene; ancestry preservation; cold-restore verification; runtime claims separated from static QA.

## Non-goal
Security controls must never be weakened merely to make a task, benchmark or model call pass.
