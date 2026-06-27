#!/usr/bin/env python3
"""
NAIO OS — activation.py (Phase 16)

First-run activation checker for rendered NAIO Hermes profile bundles. It checks
whether a nurse can safely start: START-HERE.md exists, the 7-day path exists,
EDENA/no-PHI boundaries are present, cron remains templates-only, and no direct
Hermes mutation is implied.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit("pyyaml is required for activation.py") from e

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
]

REQUIRED_FILES = [
    "START-HERE.md",
    "README-FIRST.md",
    "SOUL.md",
    ".hermes.md",
    "config/edena-runtime.yaml",
    "config/human-gates.yaml",
    "cron/rituals.yaml",
    "07-First-Week/Day-1-Setup.md",
    "07-First-Week/Day-2-SOUL-Review.md",
    "07-First-Week/Day-3-Project-Triage.md",
    "07-First-Week/Day-4-Lamp-Huddle.md",
    "07-First-Week/Day-5-Knowledge-Inbox.md",
    "07-First-Week/Day-6-Boundary-Review.md",
    "07-First-Week/Day-7-Weekly-Ledger.md",
]

DOCTRINE = "Agents propose. Humans judge. Nurses steward."
NO_PHI = "No PHI"


def refuse(msg: str) -> None:
    print(f"❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def scan_phi(profile: Path) -> list[str]:
    hits: list[str] = []
    for p in sorted(profile.rglob("*")):
        if not p.is_file() or p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
            continue
        txt = read_text(p)
        for pat, label in PHI_PATTERNS:
            m = pat.search(txt)
            if m:
                hits.append(f"{p.relative_to(profile)}: {label}: {m.group(0)[:24]!r}")
    return hits


def activation_report(profile: Path) -> tuple[dict, int]:
    missing_required = [rel for rel in REQUIRED_FILES if not (profile / rel).is_file()]
    warnings: list[str] = []
    failures: list[str] = []

    if missing_required:
        failures.extend(f"missing required activation file: {rel}" for rel in missing_required)

    combined_parts = []
    for p in sorted(profile.rglob("*")):
        if p.is_file() and p.stat().st_size < 300_000:
            combined_parts.append(read_text(p))
    combined = "\n".join(combined_parts)

    if DOCTRINE not in combined:
        failures.append("doctrine line missing from rendered profile")
    if NO_PHI not in combined and "no-PHI" not in combined and "no_phi" not in combined:
        failures.append("no-PHI boundary missing from rendered profile")

    phi_hits = scan_phi(profile)
    if phi_hits:
        failures.extend(f"PHI-like indicator detected: {hit}" for hit in phi_hits[:8])

    runtime_path = profile / "config/edena-runtime.yaml"
    rituals_path = profile / "cron/rituals.yaml"
    runtime = {}
    rituals = {}
    if runtime_path.is_file():
        try:
            runtime = yaml.safe_load(read_text(runtime_path)) or {}
        except Exception as e:
            failures.append(f"edena-runtime.yaml malformed: {e}")
    if rituals_path.is_file():
        try:
            rituals = yaml.safe_load(read_text(rituals_path)) or {}
        except Exception as e:
            failures.append(f"cron/rituals.yaml malformed: {e}")

    if runtime.get("version") != "2.0.0-phase16":
        failures.append(f"runtime version is not 2.0.0-phase16: {runtime.get('version')}")
    if runtime.get("mutation_scope") != "target-directory-only":
        failures.append("runtime mutation_scope must be target-directory-only")
    if rituals.get("mode") != "templates_only_not_scheduled":
        failures.append("cron rituals must remain templates_only_not_scheduled")
    if any(x.get("scheduled") is not False for x in runtime.get("cron_rituals", [])):
        failures.append("one or more cron rituals is marked scheduled")

    start_here = read_text(profile / "START-HERE.md") if (profile / "START-HERE.md").is_file() else ""
    if "broad strokes now, go deeper later" not in start_here.lower():
        warnings.append("START-HERE.md should include the trusted-onboarding line")
    for phrase in ["Open START-HERE.md", "First 7 Days", "No PHI", DOCTRINE]:
        if phrase not in (start_here + combined):
            failures.append(f"activation phrase missing: {phrase}")

    status = "ready" if not failures else "blocked"
    report = {
        "schema_version": "1.0.0",
        "phase": 16,
        "status": status,
        "safe_to_start": not failures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": str(profile),
        "first_prompt": "Open START-HERE.md",
        "first_week_path": "07-First-Week/",
        "required_files_checked": len(REQUIRED_FILES),
        "missing_required": missing_required,
        "missing_optional_items": warnings,
        "failures": failures,
        "no_mutation": True,
        "cron_scheduled": False,
        "doctrine": DOCTRINE,
    }
    return report, 0 if not failures else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Check first-run activation readiness for a rendered NAIO profile bundle.")
    parser.add_argument("--profile", required=True, help="rendered NAIO-Hermes-Profile directory")
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args()

    profile = Path(args.profile).expanduser().resolve()
    if not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    if profile == Path.home() or str(profile) in ("/", str(Path.home() / ".hermes")):
        refuse("refusing to activation-check home or ~/.hermes directly")

    report, code = activation_report(profile)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== NAIO OS — Phase 16 activation check ===\n")
        print(json.dumps(report, indent=2))
        if code == 0:
            print("\n✅ ACTIVATION READY — open START-HERE.md and begin Day 1.")
        else:
            print("\n❌ ACTIVATION BLOCKED — fix the failures above before first use.")
    return code


if __name__ == "__main__":
    sys.exit(main())
