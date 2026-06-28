#!/usr/bin/env python3
"""
NAIO OS — cohort.py (Phase 18)

Cohort / Instructor Mode checker for rendered NAIO Hermes profile bundles. It verifies
that an instructor can safely facilitate a nurse cohort without PHI collection,
clinical-readiness claims, auto-enrollment, cron scheduling, or direct Hermes mutation.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for cohort.py") from e

REQUIRED = [
    "11-Cohort-Mode/README.md",
    "11-Cohort-Mode/Instructor-Guide.md",
    "11-Cohort-Mode/Cohort-Launch-Checklist.md",
    "11-Cohort-Mode/Week-1-Facilitation-Plan.md",
    "11-Cohort-Mode/Week-2-Facilitation-Plan.md",
    "11-Cohort-Mode/Week-3-Facilitation-Plan.md",
    "11-Cohort-Mode/Week-4-Facilitation-Plan.md",
    "11-Cohort-Mode/Participant-Readiness-Rubric.md",
    "11-Cohort-Mode/Office-Hours-Question-Triage.md",
    "11-Cohort-Mode/Completion-Reflection.md",
    "config/edena-runtime.yaml",
    "cron/rituals.yaml",
]

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
]


def refuse(msg: str) -> None:
    print(f"❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def phi_hits(text: str) -> list[str]:
    hits = []
    for pat, label in PHI_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(f"{label}: {m.group(0)[:24]!r}")
    return hits


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_profile(profile: Path) -> dict:
    missing = [rel for rel in REQUIRED if not (profile / rel).is_file()]
    failures: list[str] = []
    warnings: list[str] = []
    if missing:
        failures.append("missing required cohort files: " + ", ".join(missing))

    runtime = load_yaml(profile / "config/edena-runtime.yaml") or {}
    rituals = load_yaml(profile / "cron/rituals.yaml") or {}
    cohort = runtime.get("cohort", {}) if isinstance(runtime, dict) else {}

    if runtime.get("version") != "2.0.0-phase23":
        failures.append(f"runtime version is not 2.0.0-phase23: {runtime.get('version')}")
    if cohort.get("path") != "11-Cohort-Mode/":
        failures.append("runtime cohort.path is not 11-Cohort-Mode/")
    if cohort.get("auto_enrollment") is not False:
        failures.append("runtime cohort.auto_enrollment must be false")
    if cohort.get("credentialing") != "readiness_reflection_not_certification":
        failures.append("runtime cohort.credentialing must remain readiness reflection, not certification")

    combined_parts = []
    for rel in REQUIRED:
        p = profile / rel
        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}:
            combined_parts.append(read_text(p))
    combined = "\n".join(combined_parts)

    required_phrases = [
        "Phase 18 Cohort Mode",
        "Instructor Guide",
        "Cohort Launch Checklist",
        "Participant Readiness Rubric",
        "Office Hours Question Triage",
        "Completion Reflection",
        "No PHI",
        "not certification",
        "not clinical decision support",
        "no auto-enrollment",
        "Agents propose. Humans judge. Nurses steward.",
    ]
    for phrase in required_phrases:
        if phrase.lower() not in combined.lower():
            failures.append(f"cohort pack missing phrase: {phrase}")

    # Flag positive unsupported claims, but allow safety examples under explicit warning language.
    for line in combined.splitlines():
        stripped = line.strip().lower()
        if not stripped or stripped.startswith("-") or "do not say" in stripped or "not certification" in stripped:
            continue
        for phrase in ["certified clinical ai", "clinical readiness certified", "guaranteed outcomes", "hipaa-compliant clinical tool"]:
            if phrase in stripped:
                failures.append(f"cohort pack contains unsupported facilitation overclaim: {phrase}")

    hits = phi_hits(combined)
    if hits:
        failures.append("PHI-like content detected in cohort pack: " + "; ".join(hits))

    if rituals.get("mode") != "templates_only_not_scheduled":
        failures.append("cron rituals mode is not templates_only_not_scheduled")
    scheduled = []
    if isinstance(runtime.get("cron_rituals"), list):
        scheduled = [r.get("id") for r in runtime["cron_rituals"] if r.get("scheduled") is not False]
    if scheduled:
        failures.append("cron rituals appear scheduled: " + ", ".join(str(x) for x in scheduled))

    status = "ready" if not failures else "blocked"
    return {
        "schema_version": "1.0.0",
        "phase": 18,
        "status": status,
        "cohort_ready": not failures,
        "safe_to_facilitate": not failures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": str(profile),
        "cohort_path": "11-Cohort-Mode/",
        "required_files_checked": len(REQUIRED),
        "missing_required": missing,
        "warnings": warnings,
        "failures": failures,
        "no_phi": not bool(hits),
        "no_clinical_claims": not any("overclaim" in f for f in failures),
        "no_auto_enrollment": cohort.get("auto_enrollment") is False,
        "no_mutation": True,
        "cron_scheduled": bool(scheduled),
        "credentialing": cohort.get("credentialing", "unknown"),
        "doctrine": runtime.get("doctrine", "Agents propose. Humans judge. Nurses steward."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Phase 18 Cohort / Instructor Mode readiness for a rendered NAIO profile bundle.")
    ap.add_argument("--profile", required=True, help="rendered NAIO profile directory")
    ap.add_argument("--json", action="store_true", help="print machine-readable report")
    args = ap.parse_args()
    profile = Path(args.profile).expanduser().resolve()
    if profile == Path.home() or str(profile) in ("/", str(Path.home() / ".hermes")):
        refuse("refusing to cohort-check home or ~/.hermes directly")
    if not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    report = check_profile(profile)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== NAIO OS — Phase 18 cohort readiness check ===\n")
        print(json.dumps(report, indent=2))
        if report["status"] == "ready":
            print("\n✅ COHORT MODE READY — facilitate with no PHI, no clinical claims, and no certification claims.")
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
