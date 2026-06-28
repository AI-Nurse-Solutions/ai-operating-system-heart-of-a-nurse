#!/usr/bin/env python3
"""NAIO OS — commercial.py (Phase 23). Commercial Activation Pack for Founding Steward Cohort and pilot conversations; no PHI, no clinical decisions, no certification, no procurement/deployment approval, and no automatic enrollment, payment, outreach, reporting, or contract authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for commercial.py") from e

REQUIRED=[
"23-Commercial-Activation/README.md",
"23-Commercial-Activation/Founding-Steward-Cohort-Offer.md",
"23-Commercial-Activation/Application-CTA-and-Form-Copy.md",
"23-Commercial-Activation/Launch-Conversion-Path.md",
"23-Commercial-Activation/Pilot-Conversation-Deck-Guide.md",
"23-Commercial-Activation/Pilot-Charter-One-Pager.md",
"23-Commercial-Activation/Warm-Invite-and-Follow-Up-Emails.md",
"23-Commercial-Activation/Cohort-Seat-and-Scholarship-Policy.md",
"23-Commercial-Activation/Manual-Review-Decision-Record.md",
"23-Commercial-Activation/Claim-Boundary-and-No-Authority-Statement.md",
"23-Commercial-Activation/Commercial-Activation-Decision-Record.md",
"config/edena-runtime.yaml",
"cron/rituals.yaml",
]
PHI_PATTERNS=[
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),
    (re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),
    (re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT|room number|patient name)\b[: ]",re.I),"clinical identifier"),
]
SECRET_PATTERNS=[
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),
    (re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),
    (re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment"),
]
OVERCLAIMS=[
    "clinical deployment approved","clinical deployment approval","approved for clinical use","patient outcome improvement","patient outcomes improved","clinical efficacy","safety validated","compliance validated","certifies competency","competency certification","credential issued","badge issued","guaranteed seats","guaranteed admission","guaranteed sponsorship","guaranteed funding","guaranteed roi","staffing reduction","procurement approved","procurement approval","contract approved","contracting authority","legal advice","compliance determination","automatic enrollment","auto-enroll","automatic payment","auto payment","automatic invoice","automatic outreach","automatic follow-up","automatic partner contact","automatic reporting","automatic dashboard","manager notification","performance evaluation","fundraising solicitation","investment advice","grant application","data room created","accept funding automatically",
]
SAFE_NEGATIONS=[
    "not ","no ","does not","do not","may not","never ","without ","out of scope","refuse","refuses","blocked","human review","human steward review","requires human","manual review","review before","draft","informational","exploratory","conversation","not clinical","not patient","not safety","not compliance","not certification","not credential","not badge","not procurement","not deployment","not legal","not fundraising","not investment","not grant","not automatic","no automatic","no auto","payment link only after","application only","not acceptance","not approval","not authority","stop","pause",": false","false",
]

def refuse(msg):
    print(f"❌ REFUSED: {msg}", file=sys.stderr); sys.exit(2)

def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding='utf-8')) if path.is_file() else None

def read(path):
    return path.read_text(encoding='utf-8', errors='ignore') if path.is_file() else ''

def hits(patterns, text):
    found=[]
    for pat,name in patterns:
        m=pat.search(text)
        if m: found.append(f"{name}: {m.group(0)[:48]}")
    return found

def unsupported_overclaims(text):
    found=[]
    lines=text.splitlines()
    for phrase in OVERCLAIMS:
        pat=re.compile(re.escape(phrase), re.I)
        for line in lines:
            if not pat.search(line):
                continue
            ctx=line.lower()
            if any(s in ctx for s in SAFE_NEGATIONS):
                continue
            found.append(phrase)
    return found

def check_profile(profile: Path) -> dict:
    missing=[rel for rel in REQUIRED if not (profile/rel).is_file()]
    failures=[]; warnings=[]
    if missing: failures.append('missing required commercial activation files: '+', '.join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; commercial=runtime.get('commercial',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase23': failures.append(f"runtime version is not 2.0.0-phase23: {runtime.get('version')}")
    if commercial.get('path')!='23-Commercial-Activation/': failures.append('runtime commercial.path is not 23-Commercial-Activation/')
    if commercial.get('commercial_use')!='founding_steward_cohort_and_pilot_conversation_activation_not_procurement_or_clinical_deployment': failures.append('runtime commercial_use must remain founding cohort/pilot conversation activation only')
    for key in ['clinical_deployment_approval','procurement_approval','contracting_authority','legal_advice','compliance_determination','certification','credentialing','competency_validation','fundraising_solicitation','investment_advice','grant_application','auto_enroll','auto_accept_payment','auto_send_invoice','auto_contact_partners','auto_follow_up','auto_create_data_room','auto_accept_funding','auto_publish_dashboard','auto_report_to_institution','auto_notify_manager']:
        if commercial.get(key) is not False: failures.append(f'runtime commercial.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 23 Commercial Activation Pack','Founding Steward Cohort Offer','Application CTA and Form Copy','Launch Conversion Path','Pilot Conversation Deck Guide','Pilot Charter One-Pager','Warm Invite and Follow-Up Emails','Cohort Seat and Scholarship Policy','Manual Review Decision Record','Claim Boundary and No-Authority Statement','Commercial Activation Decision Record','No PHI','No clinical decisions','No certification claim','Human judgment first','application is not acceptance','pilot charter is not procurement approval','payment link only after human acceptance']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'commercial pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in commercial pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in commercial pack: '+'; '.join(secrets))
    if over: failures.append('unsupported commercial/authority overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    for r in runtime.get('cron_rituals',[]) if isinstance(runtime,dict) else []:
        if r.get('scheduled') is not False: scheduled.append(r.get('id'))
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':23,'status':status,'commercial_ready':not failures,'safe_to_activate':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'commercial_path':'23-Commercial-Activation/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_clinical_decisions':'no clinical decisions' in combined.lower(),'no_certification_claim':'no certification claim' in combined.lower(),'no_procurement_or_deployment_approval':'procurement approval' in combined.lower() and 'clinical deployment' in combined.lower(),'no_automatic_commercial_actions':not any(commercial.get(k) is not False for k in ['auto_enroll','auto_accept_payment','auto_send_invoice','auto_contact_partners','auto_follow_up','auto_create_data_room','auto_accept_funding','auto_publish_dashboard','auto_report_to_institution','auto_notify_manager']),'no_mutation':True,'human_review_required':True}

def main():
    ap=argparse.ArgumentParser(description='Check Phase 23 Commercial Activation Pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to commercial-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 23 commercial activation check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ COMMERCIAL ACTIVATION READY — founding cohort and pilot conversation assets only; no PHI, clinical decisions, certification, procurement/deployment approval, or automatic enrollment/payment/outreach/reporting claims.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
