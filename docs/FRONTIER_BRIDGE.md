# ROTCLAW Frontier Bridge

The Local Sentinel is intentionally unable to execute broad/sensitive work. Such tasks become `rotclaw.frontier-handoff.v1` records under `sentinel/frontier/`.

`frontier_bridge.py` converts a handoff into the existing bounded `rotclaw.mission.v1` contract. Conversion is fail-closed: an explicit repository, base branch and one or more allowed paths are required. The resulting mission is still subject to `mission_gate.py` and the GitHub Actions Mission Bridge.

## Authority chain

`Local Sentinel -> frontier handoff -> frontier_bridge.py -> mission.v1 -> mission_gate.py -> GitHub Actions Mission Bridge -> OpenClaw frontier model -> evidence/handoff`

The bridge does not grant production, merge, secrets or protected-branch authority. Generated missions default to A1 and read/edit/test only.

## Offline sandbox behavior

The ChatGPT sandbox may have no outbound network. In that case it only produces the handoff/mission artifact. A control-plane agent with GitHub connector access, or a persistent Node01 host with egress, publishes the mission into `delegation/inbox/`. The GitHub workflow then executes it on an Internet-capable runner.

## Example

```bash
python scripts/frontier_bridge.py sentinel/frontier/<id>.json \
  --repository rotprods/ROTCLAW \
  --base-branch main \
  --allow 'docs/**'
```

Before publication, run `python scripts/mission_gate.py <mission.json>`.

## Provider note

The current Mission Bridge workflow uses the remote ROT router and therefore requires the repository Actions secret `OLLAMA_API_KEY`. Until that secret exists, remote missions fail closed at `Require provider secret`. Local Sentinel operation remains fully offline and unaffected.
