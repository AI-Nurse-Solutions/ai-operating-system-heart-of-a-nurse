#!/usr/bin/env python3
"""NAIO OS — readiness.py (Phase 18). Formative human review only; not certification."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for readiness.py") from e
REQUIRED=["15-EDENA-Readiness/README.md","15-EDENA-Readiness/Readiness-Overview.md","15-EDENA-Readiness/Eligibility-Self-Check.md","15-EDENA-Readiness/Evidence-Map.md","15-EDENA-Readiness/Stewardship-Reflection.md","15-EDENA-Readiness/Boundary-Competence-Ledger.md","15-EDENA-Readiness/Reviewer-Guide.md","15-EDENA-Readiness/Readiness-Rubric.md","15-EDENA-Readiness/Remediation-Plan.md","15-EDENA-Readiness/Non-Certification-Statement.md","15-EDENA-Readiness/Readiness-Review-Cover-Sheet.md","15-EDENA-Readiness/Badge-Deferral-Notice.md","config/edena-runtime.yaml","cron/rituals.yaml"]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["certified","credentialed","badge issued","passed","competency validated","clinically ready","clinical ai readiness granted","approved for patient care","institutionally approved","compliance validated","safety validated","efficacy validated","deployment-ready","ready for patient care"]
SAFE_NEGATIONS=["not certification","not a certification","does not issue","does not grant","not clinical ai readiness","not competency validation","no automatic","do not say","avoid","what cannot be said","does not","not permission","not institutional","not ready","no certification","no patient-care","no patient care","no clinical","badge deferral","deferred","cannot be said","not validation","readiness does not mean"]
def refuse(msg): print(f"❌ REFUSED: {msg}",file=sys.stderr); sys.exit(2)
def read(path):
    try: return path.read_text(encoding="utf-8")
    except Exception: return ""
def load_yaml(path):
    try: return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception: return None
def hits(patterns,blob):
    out=[]
    for pat,label in patterns:
        m=pat.search(blob)
        if m: out.append(f"{label}: {m.group(0)[:32]!r}")
    return out
def unsupported_overclaims(blob):
    found=[]
    for line in blob.splitlines():
        stripped=line.strip().lower()
        if not stripped or stripped.startswith('-') or stripped.startswith('>') or any(x in stripped for x in SAFE_NEGATIONS): continue
        for claim in OVERCLAIMS:
            if claim in stripped: found.append(claim)
    return found
def check_profile(profile):
    missing=[rel for rel in REQUIRED if not (profile/rel).is_file()]
    failures=[]; warnings=[]
    if missing: failures.append("missing required readiness files: "+", ".join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; readiness=runtime.get('readiness',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase22': failures.append(f"runtime version is not 2.0.0-phase22: {runtime.get('version')}")
    if readiness.get('path')!='15-EDENA-Readiness/': failures.append('runtime readiness.path is not 15-EDENA-Readiness/')
    if readiness.get('readiness_use')!='formative_human_review_not_certification': failures.append('runtime readiness_use must remain formative human review, not certification')
    for key in ['auto_score','auto_pass_fail','auto_issue_badge','auto_issue_credential']:
        if readiness.get(key) is not False: failures.append(f'runtime readiness.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 18 EDENA Micro-Credential Readiness Pack','Readiness Overview','Eligibility Self-Check','Evidence Map','Stewardship Reflection','Boundary Competence Ledger','Human Reviewer Guide','Readiness Rubric','Non-Certification Statement','Badge Deferral Notice','No PHI','No patient care use','No clinical decision support','Not certification','Not clinical AI readiness','Not competency validation','No automatic scoring','No automatic pass or fail','No automatic credential issuance','No automatic badge issuance','Human steward review','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'readiness pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in readiness pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in readiness pack: '+'; '.join(secrets))
    if over: failures.append('unsupported certification/readiness overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':15,'status':status,'readiness_ready':not failures,'safe_to_review':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'readiness_path':'15-EDENA-Readiness/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'no_certification_claims':not bool(over),'no_clinical_readiness_claims':not bool(over),'no_auto_score':readiness.get('auto_score') is False,'no_auto_pass_fail':readiness.get('auto_pass_fail') is False,'no_auto_badge':readiness.get('auto_issue_badge') is False,'no_auto_credential':readiness.get('auto_issue_credential') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'readiness_use':readiness.get('readiness_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}
def main():
    ap=argparse.ArgumentParser(description='Check Phase 18 EDENA readiness pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to readiness-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 18 EDENA readiness check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ READINESS PACK READY — formative human review only, no certification, no badges, no clinical-readiness claims.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
