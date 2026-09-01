#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "minimum_sufficient.py"


def mission(policy: dict) -> dict:
    return {
        "schema": "rotclaw.mission.v2",
        "mission_id": "minimum-sufficient-contract",
        "goal": "Fix one localized parser bug with the minimum sufficient patch.",
        "risk_class": "A1",
        "repository": "rotprods/ROTCLAW",
        "base_branch": "main",
        "work_branch": "fix/minimum-sufficient-contract",
        "allowed_paths": ["scripts/parser.py", "tests/test_parser.py"],
        "denied_paths": [".github/**", "config/**"],
        "allowed_actions": ["read", "edit", "test"],
        "acceptance": ["Parser accepts the required input", "Existing behavior remains green"],
        "requires_live": False,
        "execution_policy": policy,
    }


def run(payload: dict) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "mission.json"
        path.write_text(json.dumps(payload))
        return subprocess.run(["python3", str(GATE), str(path)], capture_output=True, text=True)


lean = {
    "goal": "Fix one localized parser bug with the minimum sufficient patch.",
    "non_goals": ["No parser redesign", "No new dependency"],
    "acceptance": ["Parser accepts the required input", "Existing behavior remains green"],
    "untouched": ["Public API", "Deployment", "Unrelated modules"],
    "change_type": "localized_logic",
    "risk_triggers": [],
    "mode": "LEAN",
    "model_tier": "MEDIUM",
    "complexity_budget": {
        "max_files": 2,
        "max_new_dependencies": 0,
        "max_new_abstractions": 0,
        "max_new_config_layers": 0,
        "max_new_services": 0,
        "max_new_state_stores": 0
    },
    "test_plan": {
        "existing_tests_first": True,
        "new_tests": [{
            "verifies": "Changed parser behavior",
            "existing_tests_would_miss": True
        }]
    }
}

p = run(mission(lean))
assert p.returncode == 0, p.stdout + p.stderr
assert "MINIMUM_SUFFICIENT_PASS" in p.stdout

systemic = json.loads(json.dumps(lean))
systemic["risk_triggers"] = ["concurrency"]
systemic["mode"] = "SYSTEMIC"
systemic["model_tier"] = "STRONG"
systemic["assurance_scope"] = ["stale writer", "duplicate event", "restart recovery"]
p = run(mission(systemic))
assert p.returncode == 0, p.stdout + p.stderr

bad_mode = json.loads(json.dumps(lean))
bad_mode["risk_triggers"] = ["security"]
p = run(mission(bad_mode))
assert p.returncode != 0
assert "mode_mismatch" in p.stdout

overbuilt = json.loads(json.dumps(lean))
overbuilt["complexity_budget"]["max_new_dependencies"] = 1
p = run(mission(overbuilt))
assert p.returncode != 0
assert "lean_complexity_exceeded" in p.stdout

unjustified_test = json.loads(json.dumps(lean))
unjustified_test["test_plan"]["new_tests"][0]["existing_tests_would_miss"] = False
p = run(mission(unjustified_test))
assert p.returncode != 0
assert "new_test_not_justified" in p.stdout

print("MINIMUM_SUFFICIENT_CONTRACT_PASS")
