# ROTCLAW Component Ancestry Matrix

| Component | v1 FULL overlay | v2 context | v3 context+QA | v5 published | Required v6 |
|---|---:|---:|---:|---:|---:|
| OpenClaw config baseline | ✅ | ❌ | ❌ | ⚠️ provider template only | ✅ restore + current-schema validation |
| Install/bootstrap scripts | ✅ | ❌ | ❌ | ❌ | ✅ |
| Live verification script | ✅ | ❌ | ❌ | QA only | ✅ modernize |
| Security policy | ✅ | ❌ | ❌ | ✅ simplified | ✅ reconcile |
| Threat model | ✅ | ❌ | ❌ | ❌ | ✅ restore + expand |
| Workspace AGENTS | ✅ | ❌ | ❌ | ✅ top-level reduced | ✅ reconcile |
| SOUL | ✅ | ❌ | ❌ | ✅ reduced | ✅ reconcile |
| IDENTITY | ✅ | ❌ | ❌ | ❌ | ✅ |
| USER | ✅ | ❌ | ❌ | ❌ public repo intentionally | ✅ private layer |
| TOOLS governance | ✅ | ❌ | ❌ | partial via AGENTS/SECURITY | ✅ |
| MEMORY contract | ✅ | ✅ context memory | ✅ | ✅ public-safe | ✅ private+public split |
| Policy config | ✅ | ❌ | ❌ | ❌ | ✅ validate against current upstream |
| define-goal skill | ✅ | ❌ | ❌ | ❌ | ✅ |
| gauntlet-loop skill | ✅ | ❌ | ❌ | ❌ | ✅ |
| graph-engineering skill | ✅ | ❌ | ❌ | ❌ | ✅ |
| model-router skill | ✅ | ❌ | ❌ | router code only | ✅ skill + router |
| vibecarrusel skill | ✅ | ❌ | ❌ | ❌ | optional/private skill pack |
| Acta de consciencia | ❌ | ✅ | ✅ | ✅ | ✅ |
| System graph | ❌ | ✅ | ✅ | ✅ | ✅ |
| Subagent topology | ❌ | ✅ | ✅ | ✅ | ✅ |
| Runtime preflight | ❌ | ✅ | ✅ | ✅ | ✅ |
| QA/adversarial suite | ❌ | ❌ | ✅ | ✅ | ✅ |
| Context compiler | ❌ | ❌ | ✅ | ✅ | ✅ |
| Recovery manifest | ❌ | ❌ | later | ✅ | ✅ |
| Model router implementation | ❌ semantic skill only | ❌ | ❌ | ✅ | ✅ |
| CI workflow | ❌ | ❌ | ❌ | ✅ | ✅ |
| Historical source registry | ❌ | ❌ | ❌ | ✅ now | ✅ |
| Ancestry gate | ❌ | ❌ | ❌ | ✅ now | ✅ mandatory |

Legend: ✅ present; ❌ absent; ⚠️ present but not equivalent.
