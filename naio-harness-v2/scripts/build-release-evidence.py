#!/usr/bin/env python3
"""Build a public-safe, unsigned release-evidence bundle for Harness 2.0."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def tree_hash(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in {"state", "__pycache__", ".venv", "evidence"} for part in relative.parts):
            continue
        digest.update(str(relative).encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        count += 1
    return digest.hexdigest(), count


def run(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--hermes-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")

    tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root, env)
    test_text = tests.stdout + tests.stderr
    match = re.search(r"Ran (\d+) tests", test_text)
    test_count = int(match.group(1)) if match else 0

    evals = run([sys.executable, "scripts/run-evals.py", "--root", "."], root, env)
    try:
        eval_report = json.loads(evals.stdout)
    except json.JSONDecodeError:
        eval_report = {"ok": False, "error": "evaluation output was not valid JSON"}

    canary = run([
        sys.executable, "scripts/hermes-canary-smoke.py", "--harness-root", ".",
        "--hermes-source", str(args.hermes_source.resolve()),
    ], root, env)
    try:
        canary_report = json.loads(canary.stdout)
    except json.JSONDecodeError:
        canary_report = {"ok": False, "error": "canary output was not valid JSON"}

    source_hash, file_count = tree_hash(root)
    all_ok = tests.returncode == 0 and bool(eval_report.get("ok")) and bool(canary_report.get("ok"))
    evidence = {
        "schema_version": "2.0.0-evidence",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact": "Nurse AI OS Harness 2.0",
        "release_status": "unsigned_implementation_candidate",
        "clinical_status": "not_clinical_decision_support",
        "data_boundary": "no_phi_synthetic_tests_only",
        "source_tree_hash": source_hash,
        "source_file_count": file_count,
        "verification": {
            "ok": all_ok,
            "unit_tests": {"ok": tests.returncode == 0, "count": test_count},
            "trajectory_evaluations": eval_report,
            "hermes_runtime_canary": canary_report,
        },
        "human_governance": {
            "architecture_recommendations": "approved_by_founder_2026-07-13",
            "steward_council_review": "pending",
            "institutional_validation": "not_claimed",
        },
        "signing": {
            "signed": False,
            "existing_trust_anchor_rotated": False,
            "gate": "matching_private_key_not_available_in_build_environment",
            "required_next_action": "authorized_human_decision_and_verified_key_ceremony_before_signed_release",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
