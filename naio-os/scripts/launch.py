#!/usr/bin/env python3
"""
NAIO OS — launch.py (Phase 18)

Public Launch Pack checker for rendered NAIO Hermes profile bundles. It verifies
that a nurse has the shareable, no-PHI, nurse-facing public launch assets needed
to invite others without overclaiming clinical readiness or automating anything.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for launch.py") from e

DOCTRINE = "Agents propose. Humans judge. Nurses steward."
REQUIRED_FILES = [
    "10-Public-Launch/README.md",
    "10-Public-Launch/Launch-Checklist.md",
    "10-Public-Launch/Safety-Boundaries.md",
    "10-Public-Launch/FAQ.md",
    "10-Public-Launch/Founder-Note.md",
    "10-Public-Launch/Demo-Script.md",
    "10-Public-Launch/Social-Post-LinkedIn.md",
    "10-Public-Launch/Social-Post-Instagram-Facebook.md",
    "10-Public-Launch/Email-Invite.md",
]
PHI_PATTERNS = [
    re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
    re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I),
    re.compile(r"\b(?:insurance|medicaid|medicare|policy)\s*(?:#|number|id)\b", re.I),
]


def refuse(msg: str) -> None:
    print(f"❌ REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def phi_hits(text: str) -> list[str]:
    hits = []
    for pat in PHI_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(m.group(0)[:32])
    return hits


def check_launch(profile: Path) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    missing = [rel for rel in REQUIRED_FILES if not (profile / rel).is_file()]
    failures.extend(f"missing required launch file: {rel}" for rel in missing)

    runtime_path = profile / "config/edena-runtime.yaml"
    runtime = {}
    if runtime_path.is_file():
        try:
            runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            failures.append(f"cannot parse edena-runtime.yaml: {e}")
    else:
        failures.append("missing config/edena-runtime.yaml")

    if runtime.get("version") != "2.0.0-phase22":
        failures.append(f"runtime version is not 2.0.0-phase22: {runtime.get('version')}")
    launch = runtime.get("launch", {}) if isinstance(runtime, dict) else {}
    if launch.get("path") != "10-Public-Launch/":
        failures.append("runtime launch.path is not 10-Public-Launch/")
    if launch.get("public_claims") != "no_clinical_readiness_claims":
        failures.append("runtime launch.public_claims must forbid clinical-readiness claims")
    if launch.get("auto_publish") is not False:
        failures.append("runtime launch.auto_publish must be false")

    combined_parts = []
    for rel in REQUIRED_FILES:
        p = profile / rel
        if p.is_file():
            combined_parts.append(read_text(p))
    combined = "\n".join(combined_parts)

    for phrase in [
        DOCTRINE,
        "No PHI",
        "No patient-specific clinical decisions",
        "not clinical decision support",
        "Carry the lamp. Keep the ledger.",
        "broad strokes now, go deeper later",
    ]:
        if phrase.lower() not in combined.lower():
            failures.append(f"launch pack missing phrase: {phrase}")

    # The safety file may quote prohibited phrases under a "Do not say" section.
    # Flag only positive/unsupported overclaims outside those explicit warning lines.
    for line in combined.splitlines():
        stripped = line.strip().lower()
        if not stripped or stripped.startswith("-") or "do not say" in stripped or "safer language" in stripped:
            continue
        for phrase in ["every major hospital", "guaranteed outcomes", "hipaa-compliant clinical tool", "clinically ready"]:
            if phrase in stripped:
                failures.append(f"launch pack contains unsupported public overclaim: {phrase}")

    hits = phi_hits(combined)
    if hits:
        failures.append("PHI-like indicators detected in launch pack: " + "; ".join(hits))

    checklist = read_text(profile / "10-Public-Launch/Launch-Checklist.md")
    for marker in ["HTTP 200", "content check", "no-PHI", "human review"]:
        if marker.lower() not in checklist.lower():
            warnings.append(f"launch checklist should mention {marker}")

    return {
        "phase": 18,
        "status": "ready" if not failures else "blocked",
        "safe_to_share": not failures,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": str(profile),
        "launch_path": "10-Public-Launch/",
        "required_files_checked": len(REQUIRED_FILES),
        "missing_required": missing,
        "warnings": warnings,
        "failures": failures,
        "no_mutation": True,
        "auto_publish": False,
        "cron_scheduled": False,
        "public_claims": "no_clinical_readiness_claims",
        "doctrine": DOCTRINE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Phase 18 Public Launch Pack readiness for a rendered NAIO profile bundle.")
    parser.add_argument("--profile", required=True, help="rendered NAIO Hermes profile directory")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    profile = Path(args.profile).expanduser().resolve()
    if not profile.exists() or not profile.is_dir():
        refuse(f"profile directory not found: {profile}")
    if profile == Path.home() or str(profile) in ("/", str(Path.home() / ".hermes")):
        refuse("refusing to launch-check home or ~/.hermes directly")
    result = check_launch(profile)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n=== NAIO OS — Phase 18 public launch check ===\n")
        print(json.dumps(result, indent=2))
        if result["safe_to_share"]:
            print("\n✅ LAUNCH PACK READY — review, personalize, and share without PHI or clinical claims.")
        else:
            print("\n❌ LAUNCH PACK BLOCKED — fix failures before sharing.")
    return 0 if result["safe_to_share"] else 2


if __name__ == "__main__":
    sys.exit(main())
