#!/usr/bin/env python3
"""NAIO OS — pilot.py (Phase 14)

Institutional Pilot Pack checker for rendered NAIO Hermes profile bundles.
Verifies non-clinical pilot posture: no PHI, no patient care use, no clinical decision support,
no institutional endorsement/compliance/certification claims, no auto-reporting, no auto-enrollment,
no automatic escalation, no cron scheduling, and no direct Hermes mutation.
"""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for pilot.py") from e

REQUIRED = [
    "14-Institutional-Pilot/README.md",
    "14-Institutional-Pilot/Pilot-Charter.md",
    "14-Institutional-Pilot/Stakeholder-Brief.md",
    "14-Institutional-Pilot/Risk-Register.md",
    "14-Institutional-Pilot/No-PHI-Pilot-Boundary.md",
    "14-Institutional-Pilot/Participant-Onboarding-Checklist.md",
    "14-Institutional-Pilot/Weekly-Pilot-Ledger.md",
    "14-Institutional-Pilot/Pilot-Outcome-Reflection.md",
    "14-Institutional-Pilot/Governance-Escalation-Path.md",
    "14-Institutional-Pilot/Not-Clinical-Deployment-Statement.md",
    "14-Institutional-Pilot/Pilot-Closeout-Brief.md",
    "config/edena-runtime.yaml",
    "cron/rituals.yaml",
]
PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b", re.I), "phone-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]", re.I), "clinical identifier"),
]
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"), "token-like secret"),
    (re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+", re.I), "credential assignment"),
]

def refuse(msg):
    print(f"❌ REFUSED: {msg}", file=sys.stderr); sys.exit(2)

def text(path: Path) -> str:
    try: return path.read_text(encoding="utf-8")
    except Exception: return ""

def load_yaml(path: Path):
    try: return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception: return None

def hits(patterns, blob):
    out=[]
    for pat,label in patterns:
        m=pat.search(blob)
        if m: out.append(f"{label}: {m.group(0)[:32]!r}")
    return out

def check_profile(profile: Path) -> dict:
    missing=[rel for rel in REQUIRED if not (profile/rel).is_file()]
    failures=[]; warnings=[]
    if missing: failures.append("missing required pilot files: "+", ".join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}
    rituals=load_yaml(profile/'cron/rituals.yaml') or {}
    pilot=runtime.get('pilot', {}) if isinstance(runtime, dict) else {}
    if runtime.get('version') != '2.0.0-phase14': failures.append(f"runtime version is not 2.0.0-phase14: {runtime.get('version')}")
    if pilot.get('path') != '14-Institutional-Pilot/': failures.append('runtime pilot.path is not 14-Institutional-Pilot/')
    if pilot.get('pilot_use') != 'non_clinical_learning_pilot_not_deployment': failures.append('runtime pilot.pilot_use must remain non-clinical learning, not deployment')
    for key in ['auto_report','auto_enroll','auto_escalate']:
        if pilot.get(key) is not False: failures.append(f'runtime pilot.{key} must be false')
    combined='\n'.join(text(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=[
        'Phase 14 Institutional Pilot Pack','Pilot Charter','Stakeholder Brief','Risk Register','No-PHI Pilot Boundary',
        'Participant Onboarding Checklist','Weekly Pilot Ledger','Governance Escalation Path','Not Clinical Deployment Statement',
        'non-clinical','No PHI','No patient care use','No clinical decision support','No institutional endorsement',
        'No compliance','No certification','No automatic reporting','No automatic participant enrollment',
        'Human governance review','Agents propose. Humans judge. Nurses steward.'
    ]
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'pilot pack missing phrase: {phrase}')
    for line in combined.splitlines():
        stripped=line.strip().lower()
        if not stripped or stripped.startswith('-') or stripped.startswith('>') or 'avoid' in stripped or 'not clinical' in stripped or 'does not' in stripped or 'out of scope' in stripped or 'no institutional endorsement' in stripped or 'no automatic participant enrollment' in stripped or 'no one is auto-enrolled' in stripped or 'no automatic reporting' in stripped or 'not deployment' in stripped or 'not certification' in stripped or 'not permission' in stripped or 'not imply' in stripped or 'not claim' in stripped:
            continue
        for phrase in ['approved clinical pilot','validated ai workflow','hipaa-compliant deployment','certified nurse ai operator','ready for patient care','institutional endorsement','compliance validated','safety validated','efficacy validated','automatic reporting to leadership','auto-enrolled']:
            if phrase in stripped:
                failures.append(f'pilot pack contains unsupported institutional overclaim: {phrase}')
    phi=hits(PHI_PATTERNS, combined); secrets=hits(SECRET_PATTERNS, combined)
    if phi: failures.append('PHI-like content detected in pilot pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in pilot pack: '+'; '.join(secrets))
    if rituals.get('mode') != 'templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'), list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {
        'schema_version':'1.0.0','phase':14,'status':status,'pilot_ready':not failures,'safe_to_pilot':not failures,
        'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'pilot_path':'14-Institutional-Pilot/',
        'required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,
        'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),
        'no_clinical_decision_support':'no clinical decision support' in combined.lower(),
        'no_institutional_endorsement_claims':not any('overclaim' in f for f in failures),
        'no_auto_report':pilot.get('auto_report') is False,'no_auto_enroll':pilot.get('auto_enroll') is False,'no_auto_escalate':pilot.get('auto_escalate') is False,
        'no_mutation':True,'cron_scheduled':bool(scheduled),'pilot_use':pilot.get('pilot_use','unknown'),
        'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.'),
    }

def main():
    ap=argparse.ArgumentParser(description='Check Phase 14 Institutional Pilot Pack readiness for a rendered NAIO profile bundle.')
    ap.add_argument('--profile', required=True); ap.add_argument('--json', action='store_true')
    args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile == Path.home() or str(profile) in ('/', str(Path.home()/'.hermes')): refuse('refusing to pilot-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report, indent=2))
    else:
        print('\n=== NAIO OS — Phase 14 institutional pilot check ===\n'); print(json.dumps(report, indent=2))
        if report['status']=='ready': print('\n✅ PILOT PACK READY — non-clinical small-group adoption with human governance review, no PHI, and no deployment claims.')
    return 0 if report['status']=='ready' else 2
if __name__ == '__main__': sys.exit(main())
