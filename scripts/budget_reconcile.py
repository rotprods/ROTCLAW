#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEPENDENCY_MANIFESTS = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "poetry.lock",
    "Pipfile", "Pipfile.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
}
TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__)(/|$)|(^|/)(test_[^/]+|[^/]+\.test\.[^/]+|[^/]+\.spec\.[^/]+)$")
TEST_ADDITION_RE = re.compile(r"^\+(?:\s*)(?:def\s+test_|async\s+def\s+test_|it\s*\(|test\s*\(|describe\s*\(|Deno\.test\s*\(|#\[test\])")
ABSTRACTION_RE = re.compile(r"^\+(?!\+)(?:\s*)(?:class|interface|protocol|abstract\s+class|trait)\s+[A-Za-z_]")
CONFIG_PATH_RE = re.compile(r"(^|/)(config|configs|configuration)(/|$)")
SERVICE_PATH_RE = re.compile(r"(^|/)(services?|daemons?|workers?)(/|$)")
STATE_PATH_RE = re.compile(r"(^|/)(stores?|storage|database|db|state)(/|$)")


def fail(msg: str) -> None:
    print("BUDGET_RECONCILE_BLOCKED")
    print(msg)
    raise SystemExit(1)


def run(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=20)
    if p.returncode != 0:
        fail("git_failed:" + " ".join(args) + ":" + p.stderr[-500:])
    return p.stdout


def worktree_files(repo: Path) -> list[str]:
    files = set(x for x in run(repo, "diff", "--name-only", "HEAD").splitlines() if x.strip())
    files.update(x for x in run(repo, "ls-files", "--others", "--exclude-standard").splitlines() if x.strip())
    return sorted(files)


def added_diff(repo: Path) -> str:
    tracked = run(repo, "diff", "--unified=0", "HEAD")
    chunks = [tracked]
    for rel in run(repo, "ls-files", "--others", "--exclude-standard").splitlines():
        path = repo / rel
        if path.is_file():
            text = path.read_text(errors="replace")
            chunks.append("\n".join("+" + line for line in text.splitlines()))
    return "\n".join(chunks)


def observe(repo: Path) -> dict:
    files = worktree_files(repo)
    added = added_diff(repo)
    new_test_markers = sum(1 for line in added.splitlines() if TEST_ADDITION_RE.search(line))
    test_files = [f for f in files if TEST_PATH_RE.search(f)]
    dependency_files = [f for f in files if Path(f).name in DEPENDENCY_MANIFESTS]
    config_files = [f for f in files if CONFIG_PATH_RE.search(f)]
    service_files = [f for f in files if SERVICE_PATH_RE.search(f)]
    state_files = [f for f in files if STATE_PATH_RE.search(f)]
    abstractions = sum(1 for line in added.splitlines() if ABSTRACTION_RE.search(line))
    return {
        "files": files,
        "file_count": len(files),
        "test_files": test_files,
        "new_test_count": new_test_markers,
        "dependency_files": dependency_files,
        "new_dependency_count": len(dependency_files),
        "config_files": config_files,
        "new_config_layer_count": len(config_files),
        "service_files": service_files,
        "new_service_count": len(service_files),
        "state_files": state_files,
        "new_state_store_count": len(state_files),
        "new_abstraction_count": abstractions,
    }


def reconcile(mission: dict, observed: dict) -> dict:
    if mission.get("schema") != "rotclaw.mission.v2":
        fail("budget_reconcile_requires_rotclaw.mission.v2")
    ep = mission.get("execution_policy") or {}
    budget = ep.get("complexity_budget") or {}
    required = {
        "max_files": "file_count",
        "max_new_dependencies": "new_dependency_count",
        "max_new_abstractions": "new_abstraction_count",
        "max_new_config_layers": "new_config_layer_count",
        "max_new_services": "new_service_count",
        "max_new_state_stores": "new_state_store_count",
    }
    violations = []
    for limit_key, observed_key in required.items():
        if limit_key not in budget:
            fail("missing_complexity_budget:" + limit_key)
        limit = budget[limit_key]
        actual = observed[observed_key]
        if actual > limit:
            violations.append(f"{limit_key}:{actual}>{limit}")

    declared_tests = len((ep.get("test_plan") or {}).get("new_tests") or [])
    if observed["new_test_count"] > declared_tests:
        violations.append(f"new_tests:{observed['new_test_count']}>{declared_tests}")

    allowed = set(mission.get("allowed_paths") or [])
    if not allowed:
        violations.append("empty_allowed_paths")

    if violations:
        fail("budget_drift:" + ";".join(violations))

    return {
        "schema": "rotclaw.budget-reconciliation.v1",
        "mission_id": mission["mission_id"],
        "mode": ep.get("mode"),
        "declared_budget": budget,
        "declared_new_tests": declared_tests,
        "observed": observed,
        "verdict": "PASS",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mission")
    ap.add_argument("--repo-root", default=str(ROOT))
    ap.add_argument("--json-out")
    args = ap.parse_args()
    mission = json.loads(Path(args.mission).read_text())
    observed = observe(Path(args.repo_root).resolve())
    result = reconcile(mission, observed)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2) + "\n")
    print("BUDGET_RECONCILE_PASS")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
