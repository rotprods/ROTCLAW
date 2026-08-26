# OpenClaw integration

This configuration follows current OpenClaw custom-provider semantics: a custom OpenAI-compatible provider lives under `models.providers`, uses an explicit `provider/model` reference, and uses an environment-backed SecretRef for `apiKey`.

## 1. Runtime secrets
Do not put credentials in this repository. On the host running the router/OpenClaw:

```bash
export ROT_ROUTER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export OLLAMA_API_KEY="<rotated-provider-key>"
```

For persistent OpenClaw service operation, put `ROT_ROUTER_TOKEN` in the gateway process environment or trusted global OpenClaw environment/secret provider. The upstream `OLLAMA_API_KEY` is needed only by the local router process.

## 2. Start router
```bash
python3 router/model_router.py
curl http://127.0.0.1:8787/healthz
```

## 3. Apply provider configuration
Merge the contents of `config/openclaw.example.json` into the host's OpenClaw config using OpenClaw's safe config tooling or configuration UI. Do not replace unrelated providers unless that is intentional.

Verify:
```bash
openclaw models list --provider rot-router
openclaw doctor
```

## 4. Qualification
The model IDs in this repository are desired routing IDs. Before production promotion, run provider discovery and one real inference per model. If the upstream exposes different exact IDs, update `config/model-routing.json` and the provider catalog together, then rerun QA.
