#!/usr/bin/env python3
"""
NAIO OS — self-test.py (Phase 8)

Focused verification harness for the downloadable Nurse AI OS bundle. This is
not a substitute for a repository test suite; it is a user-facing smoke test
that proves the installer can validate imports, render a target-only profile
bundle, and refuse unsafe paths/tiers.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - healthcheck catches this in normal use
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
PASS = 0
FAIL = 0


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")


def check(msg: str, condition: bool, detail: str = "") -> None:
    if condition:
        ok(msg if not detail else f"{msg} ({detail})")
    else:
        fail(msg if not detail else f"{msg} ({detail})")


def sample_soul() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-06-27T00:00:00Z",
        "generator": "soul-quiz",
        "identity": {
            "name": "Maria",
            "role": "staff",
            "role_label": "Staff Nurse",
            "one_liner": "ICU nurse building safe AI routines",
            "always_remember": "No PHI. No clinical decisions.",
        },
        "voice": {
            "length": "Conversational",
            "formality": "Professional",
            "pushback": "Direct but kind",
            "avoid": "Hype",
        },
        "values": ["dignity", "safety", "learning"],
        "spheres": ["personal", "professional", "community"],
        "interests": [],
        "tier_ceilings": {
            "personal": "green",
            "professional": "yellow",
            "community": "yellow",
        },
        "boundaries": {
            "no_phi_confirmed": True,
            "no_clinical_decisions_confirmed": True,
            "confidential_list": [],
            "wellbeing_rule": "Pause when overwhelmed.",
            "decisions_always_mine": ["clinical decisions", "sending external messages"],
            "drafts_without_asking": ["notes", "outlines"],
        },
        "doctrine": {
            "edena": "edena-policy@2.0.0",
            "florence_x": "florence-x@2.0.0",
            "core_line": "Agents propose. Humans judge. Nurses steward.",
        },
    }


def sample_projects() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-06-27T00:00:00Z",
        "generator": "life-quiz",
        "identity": {"name": "Maria"},
        "spheres_active": ["personal", "professional"],
        "project_count": 2,
        "projects": [
            {
                "name": "Health and wellbeing",
                "suggested_prompt_name": "Weekly Energy Review",
                "sphere": "personal",
                "sphere_label": "Personal / Family",
                "edena_tier": "green",
                "slug": "health-wellbeing",
                "help": "sleep planning",
                "goal_90_days": "consistent rest",
                "human_gate": "every-output",
                "reversibility": "reversible",
                "file_path": "04-Projects/health-wellbeing.md",
            },
            {
                "name": "Meeting prep",
                "suggested_prompt_name": "Meeting Prep Brief",
                "sphere": "professional",
                "sphere_label": "Professional",
                "edena_tier": "yellow",
                "slug": "meeting-prep",
                "help": "agenda prep",
                "goal_90_days": "meetings are calmer",
                "human_gate": "before-external-use",
                "reversibility": "reversible",
                "file_path": "04-Projects/meeting-prep.md",
            },
        ],
    }


def verify_target(target: Path) -> None:
    expected = [
        "README-FIRST.md",
        "SOUL.md",
        ".hermes.md",
        "spheres/personal.SOUL.md",
        "spheres/professional.SOUL.md",
        "spheres/community.SOUL.md",
        "projects/health-wellbeing.SYSTEM.md",
        "projects/meeting-prep.SYSTEM.md",
        "skills/lamp-huddle-steward/SKILL.md",
        "skills/weekly-ledger-review/SKILL.md",
        "skills/project-next-action-brief/SKILL.md",
        "skills/knowledge-inbox-digest/SKILL.md",
        "skills/edena-tier-audit/SKILL.md",
        "cron/rituals.yaml",
        "cron/README.md",
        "cron/prompts/weekly-lamp-huddle-review.md",
        "cron/prompts/monday-project-next-actions.md",
        "cron/prompts/monthly-edena-tier-audit.md",
        "cron/prompts/knowledge-inbox-digest.md",
        "config/edena-runtime.yaml",
        "config/human-gates.yaml",
        "config/hermes-profile.patch.yaml",
        "logs/render-report.json",
    ]
    for rel in expected:
        check(f"generated {rel}", (target / rel).is_file())

    if yaml is None:
        fail("pyyaml unavailable; cannot inspect rendered runtime")
        return
    runtime = yaml.safe_load((target / "config/edena-runtime.yaml").read_text(encoding="utf-8"))
    rituals = yaml.safe_load((target / "cron/rituals.yaml").read_text(encoding="utf-8"))
    combined = "\n".join(p.read_text(errors="ignore") for p in target.rglob("*") if p.is_file())

    check("runtime version phase8", runtime.get("version") == "2.0.0-phase8")
    check("runtime includes 5 skills", len(runtime.get("skills", [])) == 5)
    check("runtime includes 4 cron rituals", len(runtime.get("cron_rituals", [])) == 4)
    check("cron rituals are templates only", rituals.get("mode") == "templates_only_not_scheduled")
    check("cron rituals remain unscheduled", all(x.get("scheduled") is False for x in runtime.get("cron_rituals", [])))
    check("skills are EDENA tier-tagged", combined.count("edena_tier:") >= 5)
    check("Green and Yellow gates are present", "human_gate: every-output" in combined and "human_gate: before-external-use" in combined)
    check("no-PHI boundary is carried", "Do not request or infer patient information" in combined)
    check("doctrine is carried", "Agents propose. Humans judge. Nurses steward." in combined)


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO OS Phase 8 self-test harness")
    parser.add_argument("--keep-target", action="store_true", help="do not delete the generated temporary target")
    args = parser.parse_args()

    print("\n=== NAIO OS — Phase 8 self-test ===\n")
    print("This is an ad-hoc smoke test for the downloadable bundle, not canonical suite green.\n")

    hc = run(["python3", "scripts/healthcheck.py"])
    check("full healthcheck exits 0", hc.returncode == 0, f"exit={hc.returncode}")

    update = run(["python3", "scripts/check-update.py", "--local-only", "--json"])
    check("local update advisory verifies rollback protection", update.returncode == 0 and '"rollback_protected": true' in update.stdout and '"no_mutation": true' in update.stdout, f"exit={update.returncode}")

    tmp = Path(tempfile.mkdtemp(prefix="naio-os-self-test-"))
    target = tmp / "NAIO-Hermes-Profile"
    try:
        soul_path = tmp / "naio-soul.json"
        projects_path = tmp / "naio-projects.json"
        soul_path.write_text(json.dumps(sample_soul()), encoding="utf-8")
        projects_path.write_text(json.dumps(sample_projects()), encoding="utf-8")

        dry = run(["bash", "install.sh", "--dry-run", "--soul", str(soul_path), "--projects", str(projects_path)])
        check("dry-run validates imports and writes nothing", dry.returncode == 0 and "Nothing written" in (dry.stdout + dry.stderr), f"exit={dry.returncode}")

        applied = run(["bash", "install.sh", "--apply", "--soul", str(soul_path), "--projects", str(projects_path), "--target", str(target)])
        check("target-only apply exits 0", applied.returncode == 0, f"exit={applied.returncode}")
        if target.exists():
            verify_target(target)
            recovery = run(["python3", "scripts/recovery.py", "--drill", "--profile", str(target)])
            check("recovery drill snapshots/verifies/extracts/plans with no mutation", recovery.returncode == 0 and '"status": "drill-passed"' in recovery.stdout and '"no_mutation": true' in recovery.stdout, f"exit={recovery.returncode}")
        else:
            fail("target directory was not created")

        refuses_home = run(["python3", "scripts/render-profile.py", "--soul", str(soul_path), "--target", str(Path.home() / ".hermes"), "--force"])
        check("renderer refuses direct ~/.hermes overwrite", refuses_home.returncode == 2, f"exit={refuses_home.returncode}")

        orange = sample_soul()
        orange["tier_ceilings"] = {"professional": "orange"}
        orange_path = tmp / "bad-orange.json"
        orange_path.write_text(json.dumps(orange), encoding="utf-8")
        refuses_orange = run(["bash", "install.sh", "--apply", "--soul", str(orange_path), "--target", str(tmp / "bad-target")])
        check("installer refuses Orange onboarding tier", refuses_orange.returncode == 2, f"exit={refuses_orange.returncode}")
    finally:
        if args.keep_target:
            print(f"\nTemporary self-test directory kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n--- self-test summary ---")
    print(f"  ok:   {PASS}")
    print(f"  fail: {FAIL}")
    if FAIL:
        print("\n❌ SELF-TEST FAILED — do not apply this bundle yet.")
    else:
        print("\n✅ SELF-TEST PASSED — bundle behavior is consistent with Phase 8 safety contract.")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
