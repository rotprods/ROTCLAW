#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "budget_reconcile.py"


def run(cmd, cwd=None, expect=0):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != expect:
        raise AssertionError(f"unexpected rc={p.returncode} expect={expect}\nstdout={p.stdout}\nstderr={p.stderr}")
    return p


def init_repo(base: Path) -> None:
    run(["git", "init"], cwd=base)
    run(["git", "config", "user.email", "test@example.com"], cwd=base)
    run(["git", "config", "user.name", "Test"], cwd=base)
    (base / "src").mkdir()
    (base / "tests").mkdir()
    (base / "src" / "parser.py").write_text("def parse(x):\n    return x\n")
    run(["git", "add", "."], cwd=base)
    run(["git", "commit", "-m", "base"], cwd=base)


def mission(path: Path, max_files=2, tests=1):
    data = {
        "schema": "rotclaw.mission.v2",
        "mission_id": "budget-check-001",
        "goal": "Fix parser minimally",
        "risk_class": "A1",
        "repository": "example/repo",
        "base_branch": "main",
        "work_branch": "fix/parser",
        "allowed_paths": ["src/parser.py", "tests/test_parser.py"],
        "denied_paths": ["config/**"],
        "allowed_actions": ["read", "edit", "test"],
        "acceptance": ["parser fixed"],
        "execution_policy": {
            "goal": "Fix parser minimally",
            "non_goals": ["no redesign"],
            "acceptance": ["parser fixed"],
            "untouched": ["dependencies"],
            "change_type": "localized_logic",
            "risk_triggers": [],
            "mode": "LEAN",
            "model_tier": "MEDIUM",
            "complexity_budget": {
                "max_files": max_files,
                "max_new_dependencies": 0,
                "max_new_abstractions": 0,
                "max_new_config_layers": 0,
                "max_new_services": 0,
                "max_new_state_stores": 0,
            },
            "test_plan": {
                "existing_tests_first": True,
                "new_tests": [
                    {"verifies": "parser behavior", "existing_tests_would_miss": True}
                    for _ in range(tests)
                ],
            },
        },
    }
    path.write_text(json.dumps(data))


def main():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        mp = Path(td) / "mission.json"
        mission(mp)
        (repo / "src" / "parser.py").write_text("def parse(x):\n    return x.strip()\n")
        (repo / "tests" / "test_parser.py").write_text("def test_parse():\n    assert True\n")
        p = run(["python3", str(SCRIPT), str(mp), "--repo-root", str(repo)])
        assert "BUDGET_RECONCILE_PASS" in p.stdout

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        mp = Path(td) / "mission.json"
        mission(mp, max_files=1)
        (repo / "src" / "parser.py").write_text("def parse(x):\n    return x.strip()\n")
        (repo / "tests" / "test_parser.py").write_text("def test_parse():\n    assert True\n")
        p = run(["python3", str(SCRIPT), str(mp), "--repo-root", str(repo)], expect=1)
        assert "budget_drift:max_files:2>1" in p.stdout

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        mp = Path(td) / "mission.json"
        mission(mp, max_files=2, tests=0)
        (repo / "tests" / "test_parser.py").write_text("def test_parse():\n    assert True\n")
        p = run(["python3", str(SCRIPT), str(mp), "--repo-root", str(repo)], expect=1)
        assert "new_tests:1>0" in p.stdout

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        mp = Path(td) / "mission.json"
        mission(mp, max_files=2, tests=0)
        (repo / "package.json").write_text('{"dependencies":{"x":"1.0.0"}}\n')
        p = run(["python3", str(SCRIPT), str(mp), "--repo-root", str(repo)], expect=1)
        assert "max_new_dependencies:1>0" in p.stdout

    print("BUDGET_RECONCILE_CONTRACT_PASS")


if __name__ == "__main__":
    main()
