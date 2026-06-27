#!/usr/bin/env python3
"""
NAIO OS — evidence.py (Phase 12)

EDENA Evidence Trail checker for rendered NAIO Hermes profile bundles. It verifies
that a learner can collect reflection/evidence artifacts safely without PHI,
clinical-competency claims, automatic scoring, external submission, or direct Hermes mutation.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for evidence.py") from e

REQUIRED = [
    "12-Evidence-Trail/README.md",
    "12-Evidence-Trail/Evidence-Capture-Guide.md",
    "12-Evidence-Trail/EDENA-Lens-Reflection.md",
    "12-Evidence-Trail/Artifact-Log.md",
    "12-Evidence-Trail/Human-Gate-Ledger.md",
    "12-Evidence-Trail/Boundary-Incident-Template.md",
    "12-Evidence-Trail/Portfolio-Index.md",
    "12-Evidence-Trail/Facilitator-Review-Notes.md",
    "12-Evidence-Trail/Evidence-Export-Checklist.md",
    "12-Evidence-Trail/Not-Certification-Statement.md",
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
        failures.append("missing required evidence files: " + ", ".join(missing))

    runtime = load_yaml(profile / "config/edena-runtime.yaml") or {}
    rituals = load_yaml(profile / "cron/rituals.yaml") or {}
    evidence = runtime.get("evidence", {}) if isinstance(runtime, dict) else {}

    if runtime.get("version") != "2.0.0-phase12":
        failures.append(f"runtime version is not 2.0.0-phase12: {runtime.get('version')}")
    if evidence.get("path") != "12-Evidence-Trail/":
        failures.append("runtime evidence.path is not 12-Evidence-Trail/")
    if evidence.get("credentialing") != "evidence_of_learning_not_certification":
        failures.append("runtime evidence.credentialing must remain evidence of learning, not certification")
    if evidence.get("auto_score") is not False:
        failures.append("runtime evidence.auto_score must be false")
    if evidence.get("auto_submit") is not False:
        failures.append("runtime evidence.auto_submit must be false")

    combined_parts = []
    for rel in REQUIRED:
        p = profile / rel
        if p.is_file() and p.suffix in {".md", ".yaml", ".yml"}:
            combined_parts.append(read_text(p))
    combined = "\n".join(combined_parts)

    required_phrases = [
        "Phase 12 EDENA Evidence Trail",
        "Evidence Capture Guide",
        "EDENA Lens Reflection",
        "Artifact Log",
        "Human Gate Ledger",
        "Boundary Incident Template",
        "Portfolio Index",
        "Not Certification Statement",
        "No PHI",
        "not certification",
        "not clinical decision support",
        "no automatic scoring",
        "no automatic submission",
        "Agents propose. Humans judge. Nurses steward.",
    ]
    for phrase in required_phrases:
        if phrase.lower() not in combined.lower():
            failures.append(f"evidence trail missing phrase: {phrase}")

    for line in combined.splitlines():
        stripped = line.strip().lower()
        if not stripped or stripped.startswith("-") or "do not say" in stripped or "not certification" in stripped:
            continue
        for phrase in [
            "certified clinical ai",
            "clinical readiness certified",
            "clinical competence certified",
            "guaranteed outcomes",
            "hipaa-compliant clinical tool",
            "automatic pass",
            "auto-scored certification",
        ]:
            if phrase in stripped:
                failures.append(f"evidence trail contains unsupported credentialing overclaim: {phrase}")

    hits = phi_hits(combined)
    if hits:
        failures.append("PHI-like content detected in evidence trail: " + "; ".join(hits))

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
        "phase": 12,
        "status": status,
        "evidence_ready": not failures,
        "safe_to_document": not failures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": str(profile),
        "evidence_path": "12-Evidence-Trail/",
        "required_files_checked": len(REQUIRED),
        "missing_required": missing,
        "warnings": warnings,
        "failures": failures,
        "no_phi": not bool(hits),
        "no_clinical_claims": not any("overclaim" in f for f in failures),
        "no_auto_score": evidence.get("auto_score") is False,
        "no_auto_submit": evidence.get("auto_submit") is False,
        "no_mutation": True,
        "cron_scheduled": bool(scheduled),
        "credentialing": evidence.get("credentialing", "unknown"),
        "doctrine": runtime.get("doctrine", "Agents propose. Humans judge. Nurses steward."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Phase 12 EDENA Evidence Trail readiness for a rendered NAIO profile bundle.")
    ap.add_argument("--profile", required=True, help="rendered NAIO profile directory")
    ap.add_argument("--json", action="store_true", help="print machine-readable report")
    args = ap.parse_args()
    profile = Path(args.profile).expanduser().resolve()
    if profile == Path.home() or str(profile) in ("/", str(Path.home() / ".hermes")):
        refuse("refusing to evidence-check home or ~/.hermes directly")
    if not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    report = check_profile(profile)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== NAIO OS — Phase 12 EDENA evidence trail check ===\n")
        print(json.dumps(report, indent=2))
        if report["status"] == "ready":
            print("\n✅ EVIDENCE TRAIL READY — document learning with no PHI, no automatic scoring, and no certification claims.")
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
