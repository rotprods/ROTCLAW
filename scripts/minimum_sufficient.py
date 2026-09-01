#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "minimum-sufficient-policy.json"


def fail(msg: str) -> None:
    print("MINIMUM_SUFFICIENT_BLOCKED")
    print(msg)
    raise SystemExit(1)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_execution_policy(mission: dict, policy: dict) -> dict:
    if mission.get("schema") != "rotclaw.mission.v2":
        fail("minimum_sufficient_requires_rotclaw.mission.v2")

    ep = mission.get("execution_policy")
    if not isinstance(ep, dict):
        fail("missing_execution_policy")

    required = policy["required_plan_fields"]
    missing = [field for field in required if field not in ep]
    if missing:
        fail("missing_plan_fields:" + ",".join(missing))

    if ep["goal"] != mission.get("goal"):
        fail("execution_policy_goal_must_match_mission_goal")
    if ep["acceptance"] != mission.get("acceptance"):
        fail("execution_policy_acceptance_must_match_mission_acceptance")
    if not isinstance(ep["non_goals"], list) or not ep["non_goals"]:
        fail("non_goals_must_be_non_empty_list")
    if not isinstance(ep["untouched"], list) or not ep["untouched"]:
        fail("untouched_must_be_non_empty_list")

    change_type = ep["change_type"]
    if change_type not in policy["model_tiers"]:
        fail("invalid_change_type")

    risk_triggers = ep["risk_triggers"]
    if not isinstance(risk_triggers, list):
        fail("risk_triggers_must_be_list")
    unknown = sorted(set(risk_triggers) - set(policy["systemic_risk_triggers"]))
    if unknown:
        fail("unknown_risk_triggers:" + ",".join(unknown))

    systemic = bool(risk_triggers)
    expected_mode = "SYSTEMIC" if systemic else "LEAN"
    if ep.get("mode") != expected_mode:
        fail(f"mode_mismatch:expected_{expected_mode}")

    expected_model = policy["model_tiers"]["systemic" if systemic else change_type]
    if ep.get("model_tier") != expected_model:
        fail(f"model_tier_mismatch:expected_{expected_model}")

    budget = ep["complexity_budget"]
    if not isinstance(budget, dict):
        fail("complexity_budget_must_be_object")

    if expected_mode == "LEAN":
        for key, limit in policy["lean_limits"].items():
            if key == "max_new_tests":
                continue
            value = budget.get(key)
            if value is None:
                fail("missing_complexity_budget:" + key)
            if not isinstance(value, int) or value < 0:
                fail("invalid_complexity_budget:" + key)
            if value > limit:
                fail(f"lean_complexity_exceeded:{key}:{value}>{limit}")

    test_plan = ep["test_plan"]
    if not isinstance(test_plan, dict):
        fail("test_plan_must_be_object")
    if test_plan.get("existing_tests_first") is not True:
        fail("existing_tests_first_required")
    new_tests = test_plan.get("new_tests")
    if not isinstance(new_tests, list):
        fail("new_tests_must_be_list")

    for test in new_tests:
        if not isinstance(test, dict):
            fail("new_test_entries_must_be_objects")
        if not test.get("verifies"):
            fail("new_test_missing_requirement_or_invariant")
        if test.get("existing_tests_would_miss") is not True:
            fail("new_test_not_justified_against_existing_tests")

    if expected_mode == "LEAN" and len(new_tests) > policy["lean_limits"]["max_new_tests"]:
        fail("lean_test_budget_exceeded")

    if expected_mode == "SYSTEMIC" and not ep.get("assurance_scope"):
        fail("systemic_mode_requires_assurance_scope")

    return {
        "mode": expected_mode,
        "model_tier": expected_model,
        "risk_triggers": risk_triggers,
        "new_test_count": len(new_tests),
        "verdict": "PASS",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mission")
    ap.add_argument("--policy", default=str(POLICY_PATH))
    args = ap.parse_args()

    mission = load(Path(args.mission))
    policy = load(Path(args.policy))
    result = validate_execution_policy(mission, policy)
    print("MINIMUM_SUFFICIENT_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
