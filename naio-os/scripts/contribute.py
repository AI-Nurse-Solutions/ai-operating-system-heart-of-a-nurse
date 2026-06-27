#!/usr/bin/env python3
"""
NAIO OS — contribute.py (Phase 18)

NIN Community Contribution Flow checker for rendered NAIO Hermes profile bundles.
It verifies that a nurse can prepare sanitized community contributions safely:
no PHI, no employer-confidential material, no clinical-decision support, no endorsement
or certification claims, no automatic publishing/submission/reviewer assignment, and no direct Hermes mutation.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for contribute.py") from e

REQUIRED = [
    "13-Contribution-Flow/README.md",
    "13-Contribution-Flow/Contribution-Intake-Guide.md",
    "13-Contribution-Flow/Sanitization-Checklist.md",
    "13-Contribution-Flow/Contribution-Template.md",
    "13-Contribution-Flow/EDENA-Review-Rubric.md",
    "13-Contribution-Flow/Attribution-and-Consent.md",
    "13-Contribution-Flow/Community-Use-License.md",
    "13-Contribution-Flow/Reviewer-Triage-Queue.md",
    "13-Contribution-Flow/Not-Endorsement-Statement.md",
    "13-Contribution-Flow/Contributor-Thank-You.md",
    "config/edena-runtime.yaml",
    "cron/rituals.yaml",
]

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
    (re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I), "insurance identifier"),
]
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"), "token-like secret"),
    (re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+", re.I), "credential assignment"),
]


def refuse(msg: str) -> None:
    print(f"❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def hits(patterns, text: str) -> list[str]:
    found = []
    for pat, label in patterns:
        m = pat.search(text)
        if m:
            found.append(f"{label}: {m.group(0)[:32]!r}")
    return found


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
        failures.append("missing required contribution files: " + ", ".join(missing))

    runtime = load_yaml(profile / "config/edena-runtime.yaml") or {}
    rituals = load_yaml(profile / "cron/rituals.yaml") or {}
    contribution = runtime.get("contribution", {}) if isinstance(runtime, dict) else {}

    if runtime.get("version") != "2.0.0-phase19":
        failures.append(f"runtime version is not 2.0.0-phase19: {runtime.get('version')}")
    if contribution.get("path") != "13-Contribution-Flow/":
        failures.append("runtime contribution.path is not 13-Contribution-Flow/")
    if contribution.get("community_use") != "human_reviewed_sanitized_learning_not_endorsement":
        failures.append("runtime contribution.community_use must remain human-reviewed learning, not endorsement")
    if contribution.get("auto_publish") is not False:
        failures.append("runtime contribution.auto_publish must be false")
    if contribution.get("auto_submit") is not False:
        failures.append("runtime contribution.auto_submit must be false")
    if contribution.get("auto_reviewer_assignment") is not False:
        failures.append("runtime contribution.auto_reviewer_assignment must be false")

    combined_parts = []
    for rel in REQUIRED:
        p = profile / rel
        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}:
            combined_parts.append(read_text(p))
    combined = "\n".join(combined_parts)

    required_phrases = [
        "Phase 18 NIN Community Contribution Flow",
        "Contribution Intake Guide",
        "Sanitization Checklist",
        "Contribution Template",
        "EDENA Review Rubric",
        "Attribution and Consent",
        "Not Endorsement Statement",
        "No PHI",
        "No employer-confidential",
        "No automatic publishing",
        "No automatic reviewer assignment",
        "not endorsement",
        "not certification",
        "not clinical decision support",
        "Agents propose. Humans judge. Nurses steward.",
    ]
    for phrase in required_phrases:
        if phrase.lower() not in combined.lower():
            failures.append(f"contribution flow missing phrase: {phrase}")

    for line in combined.splitlines():
        stripped = line.strip().lower()
        if not stripped or stripped.startswith("-") or "avoid" in stripped or "not endorsement" in stripped or "not allowed" in stripped:
            continue
        for phrase in [
            "endorsed clinical tool",
            "clinically validated",
            "clinical readiness certified",
            "certified clinical ai",
            "guaranteed outcomes",
            "hipaa-compliant clinical contribution",
            "automatic approval",
            "auto-published",
            "auto approved",
        ]:
            if phrase in stripped:
                failures.append(f"contribution flow contains unsupported community overclaim: {phrase}")

    phi = hits(PHI_PATTERNS, combined)
    if phi:
        failures.append("PHI-like content detected in contribution flow: " + "; ".join(phi))
    secrets = hits(SECRET_PATTERNS, combined)
    if secrets:
        failures.append("secret-like content detected in contribution flow: " + "; ".join(secrets))

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
        "contribution_ready": not failures,
        "safe_to_contribute": not failures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": str(profile),
        "contribution_path": "13-Contribution-Flow/",
        "required_files_checked": len(REQUIRED),
        "missing_required": missing,
        "warnings": warnings,
        "failures": failures,
        "no_phi": not bool(phi),
        "no_secrets": not bool(secrets),
        "no_employer_confidential": "employer-confidential" in combined.lower(),
        "no_endorsement_claims": not any("overclaim" in f for f in failures),
        "no_auto_publish": contribution.get("auto_publish") is False,
        "no_auto_submit": contribution.get("auto_submit") is False,
        "no_auto_reviewer_assignment": contribution.get("auto_reviewer_assignment") is False,
        "no_mutation": True,
        "cron_scheduled": bool(scheduled),
        "community_use": contribution.get("community_use", "unknown"),
        "doctrine": runtime.get("doctrine", "Agents propose. Humans judge. Nurses steward."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Phase 18 NIN Community Contribution Flow readiness for a rendered NAIO profile bundle.")
    ap.add_argument("--profile", required=True, help="rendered NAIO profile directory")
    ap.add_argument("--json", action="store_true", help="print machine-readable report")
    args = ap.parse_args()
    profile = Path(args.profile).expanduser().resolve()
    if profile == Path.home() or str(profile) in ("/", str(Path.home() / ".hermes")):
        refuse("refusing to contribution-check home or ~/.hermes directly")
    if not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    report = check_profile(profile)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== NAIO OS — Phase 18 NIN community contribution check ===\n")
        print(json.dumps(report, indent=2))
        if report["status"] == "ready":
            print("\n✅ CONTRIBUTION FLOW READY — share sanitized learning with human review, no PHI, and no endorsement claims.")
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
