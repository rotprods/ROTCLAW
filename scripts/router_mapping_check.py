#!/usr/bin/env python3
"""Fail-closed check for canonical ROTCLAW model IDs -> runtime upstream IDs."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "router" / "model_router.py"

EXPECTED = {
    "deepseek-v4-flash": "provider/deepseek-test",
    "kimi-k2.6": "provider/kimi-test",
    "glm-5.2": "provider/glm-test",
    "minimax-m3": "provider/minimax-test",
}
ENV = {
    "ROT_MODEL_DEEPSEEK": EXPECTED["deepseek-v4-flash"],
    "ROT_MODEL_KIMI": EXPECTED["kimi-k2.6"],
    "ROT_MODEL_GLM": EXPECTED["glm-5.2"],
    "ROT_MODEL_MINIMAX": EXPECTED["minimax-m3"],
}

old = {k: os.environ.get(k) for k in ENV}
try:
    os.environ.update(ENV)
    spec = importlib.util.spec_from_file_location("rotclaw_router_mapping_test", ROUTER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)

    failures = []
    for canonical, upstream in EXPECTED.items():
        observed = mod.resolve(canonical)
        if observed != upstream:
            failures.append(f"{canonical}: expected {upstream!r}, got {observed!r}")

    profile_expectations = {
        "coding": EXPECTED["deepseek-v4-flash"],
        "fast": EXPECTED["deepseek-v4-flash"],
        "balanced": EXPECTED["deepseek-v4-flash"],
        "research": EXPECTED["kimi-k2.6"],
        "reasoning": EXPECTED["glm-5.2"],
        "creative": EXPECTED["minimax-m3"],
    }
    for profile, upstream in profile_expectations.items():
        observed = mod.resolve(profile)
        if observed != upstream:
            failures.append(f"profile {profile}: expected {upstream!r}, got {observed!r}")

    # Unknown explicit model names must pass through rather than silently remap.
    if mod.resolve("custom-provider-model") != "custom-provider-model":
        failures.append("unknown explicit model did not pass through")

    if failures:
        print("ROUTER_MAPPING_FAIL")
        for failure in failures:
            print(failure)
        raise SystemExit(1)

    print("ROUTER_MAPPING_PASS")
    print(f"canonical_models={len(EXPECTED)} profiles={len(profile_expectations)}")
finally:
    for key, value in old.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
