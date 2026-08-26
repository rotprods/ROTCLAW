# Gauntlet report

The artifact/context/recovery layer reached its defined 10/10 gates after iterative remediation. Two defects were caught during the gauntlet rather than hidden: context-budget overflow after adding the integrity envelope, and a self-referential recovery manifest that broke determinism. Both were fixed and rerun.

Evidence preserved in this repository includes the 50-loop summary, stress benchmark outputs, adversarial results, final scorecard and recovery manifest. Live OpenClaw/provider/tool/sandbox/production dimensions remain unqualified until executed in the target host.
