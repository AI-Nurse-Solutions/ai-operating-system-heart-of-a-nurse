#!/usr/bin/env python3
"""NAIO OS — governance.py (Phase 18). Advisory Steward Council only; not institutional authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for governance.py") from e
REQUIRED=["18-Governance-Board/README.md","18-Governance-Board/Governance-Board-Charter.md","18-Governance-Board/Steward-Council-Overview.md","18-Governance-Board/Member-Role-Card.md","18-Governance-Board/Review-Intake-Form.md","18-Governance-Board/Agenda-Template.md","18-Governance-Board/Decision-Record.md","18-Governance-Board/Conflict-of-Interest-Disclosure.md","18-Governance-Board/Boundary-and-Scope-Statement.md","18-Governance-Board/Escalation-and-Referral-Path.md","18-Governance-Board/Voting-and-Quorum-Checklist.md","18-Governance-Board/Transparency-Ledger.md","18-Governance-Board/Non-Authority-Statement.md","config/edena-runtime.yaml","cron/rituals.yaml"]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["legal authority","institutional authority","institutional approval","institutional endorsement","clinical governance authority","compliance determination","legal advice","procurement approval","certification authority","certification","credentialing","disciplinary action","approved by the board","board-authorized","board authorized","policy approved","policy enforced","automatic approval","automatic approvals","automatic policy enforcement","automatically approve","automatically enforce","automatic member assignment","automatically assign members","automatic publication of minutes","automatically publish minutes","automatic escalation","clinically safe","clinically effective","safety validated","efficacy validated","legally reviewed","compliant"]
SAFE_NEGATIONS=["not legal","not compliance","not institutional","not clinical","not procurement","not certification","not credentialing","not disciplinary","not legal advice","not institutional approval","not institutional endorsement","not clinical governance authority","not compliance determination","not authority","does not create","does not automatically","does not", "no automatic", "advisory only", "advisory", "stewardship", "refers", "refer", "out of scope", "may not", "do not say", "not safety validation", "not efficacy validation", "stop", "pause"]
def refuse(msg):
    print(f"❌ REFUSED: {msg}",file=sys.stderr)
    sys.exit(2)
def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""
def load_yaml(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
def hits(patterns,blob):
    out=[]
    for pat,label in patterns:
        m=pat.search(blob)
        if m:
            out.append(f"{label}: {m.group(0)[:32]!r}")
    return out
def unsupported_overclaims(blob):
    found=[]
    for line in blob.splitlines():
        stripped=line.strip().lower()
        if not stripped:
            continue
        # Boundary templates intentionally list prohibited authority types as bullets/tables.
        # Runtime YAML may also encode explicit false guards such as certification: false.
        # Treat affirmative prose as overclaims; do not flag out-of-scope lists or false metadata.
        if stripped.startswith('-') or stripped.startswith('>') or stripped.startswith('|'):
            continue
        if ': false' in stripped or 'not_' in stripped:
            continue
        if any(x in stripped for x in SAFE_NEGATIONS):
            continue
        for claim in OVERCLAIMS:
            if claim in stripped:
                found.append(claim)
    return found
def check_profile(profile):
    missing=[rel for rel in REQUIRED if not (profile/rel).is_file()]
    failures=[]
    warnings=[]
    if missing:
        failures.append("missing required governance files: "+", ".join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}
    rituals=load_yaml(profile/'cron/rituals.yaml') or {}
    governance=runtime.get('governance',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase23':
        failures.append(f"runtime version is not 2.0.0-phase23: {runtime.get('version')}")
    if governance.get('path')!='18-Governance-Board/':
        failures.append('runtime governance.path is not 18-Governance-Board/')
    if governance.get('governance_use')!='advisory_stewardship_council_not_institutional_authority':
        failures.append('runtime governance_use must remain advisory stewardship, not institutional authority')
    for key in ['legal_advice','compliance_determination','clinical_governance_authority','institutional_approval','institutional_endorsement','procurement_approval','certification','credentialing','disciplinary_action','auto_approve_policy','auto_enforce_policy','auto_assign_members','auto_publish_minutes','auto_escalate']:
        if governance.get(key) is not False:
            failures.append(f'runtime governance.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 18 Governance Board / Steward Council Pack','Governance Board Charter','Steward Council Overview','Member Role Card','Governance Review Intake Form','Steward Council Agenda Template','Advisory Decision Record','Conflict of Interest Disclosure','Boundary and Scope Statement','Escalation and Referral Path','Voting and Quorum Checklist','Transparency Ledger','Non-Authority Statement','No PHI','No patient care use','No clinical decision support','Advisory only','Not legal advice','Not compliance determination','Not institutional approval','Not institutional endorsement','Not clinical governance authority','Not procurement approval','Not certification','Not credentialing','Not disciplinary action','No automatic approvals','No automatic policy enforcement','No automatic member assignment','No automatic publication of minutes','Human steward review is required','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower():
            failures.append(f'governance pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined)
    secrets=hits(SECRET_PATTERNS,combined)
    over=unsupported_overclaims(combined)
    if phi:
        failures.append('PHI-like content detected in governance pack: '+'; '.join(phi))
    if secrets:
        failures.append('secret-like content detected in governance pack: '+'; '.join(secrets))
    if over:
        failures.append('unsupported governance/authority overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled':
        failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list):
        scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled:
        failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':18,'status':status,'governance_ready':not failures,'safe_to_convene':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'governance_path':'18-Governance-Board/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'advisory_only':'advisory only' in combined.lower(),'no_authority_overclaims':not bool(over),'no_legal_advice':governance.get('legal_advice') is False,'no_compliance_determination':governance.get('compliance_determination') is False,'no_clinical_governance_authority':governance.get('clinical_governance_authority') is False,'no_institutional_approval':governance.get('institutional_approval') is False,'no_institutional_endorsement':governance.get('institutional_endorsement') is False,'no_procurement_approval':governance.get('procurement_approval') is False,'no_certification':governance.get('certification') is False,'no_credentialing':governance.get('credentialing') is False,'no_disciplinary_action':governance.get('disciplinary_action') is False,'no_auto_approve_policy':governance.get('auto_approve_policy') is False,'no_auto_enforce_policy':governance.get('auto_enforce_policy') is False,'no_auto_assign_members':governance.get('auto_assign_members') is False,'no_auto_publish_minutes':governance.get('auto_publish_minutes') is False,'no_auto_escalate':governance.get('auto_escalate') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'governance_use':governance.get('governance_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}
def main():
    ap=argparse.ArgumentParser(description='Check Phase 18 Governance Board / Steward Council pack for a rendered NAIO profile bundle.')
    ap.add_argument('--profile',required=True)
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')):
        refuse('refusing to governance-check home or ~/.hermes directly')
    if not profile.is_dir():
        refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json:
        print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 18 governance board / steward council check ===\n')
        print(json.dumps(report,indent=2))
        if report['status']=='ready':
            print('\n✅ GOVERNANCE PACK READY — advisory stewardship only, no institutional authority, no automatic approvals.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__':
    sys.exit(main())
