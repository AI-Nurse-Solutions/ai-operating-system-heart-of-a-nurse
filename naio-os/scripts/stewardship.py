#!/usr/bin/env python3
"""NAIO OS — stewardship.py (Phase 20). Advisory institutional stewardship operating model only; not legal, compliance, procurement, staffing, clinical deployment, or implementation authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for stewardship.py") from e

REQUIRED=[
"20-Stewardship-Operating-Model/README.md",
"20-Stewardship-Operating-Model/Operating-Model-Overview.md",
"20-Stewardship-Operating-Model/Role-and-Cadence-Map.md",
"20-Stewardship-Operating-Model/Intake-to-Decision-Workflow.md",
"20-Stewardship-Operating-Model/Human-Gate-RACI.md",
"20-Stewardship-Operating-Model/Stewardship-Meeting-Agenda.md",
"20-Stewardship-Operating-Model/Risk-Escalation-Map.md",
"20-Stewardship-Operating-Model/Stewardship-Metrics-Scorecard.md",
"20-Stewardship-Operating-Model/Implementation-Backlog-Template.md",
"20-Stewardship-Operating-Model/Adoption-Readiness-Conversation-Guide.md",
"20-Stewardship-Operating-Model/Non-Authority-and-No-Deployment-Statement.md",
"20-Stewardship-Operating-Model/Quarterly-Stewardship-Review.md",
"config/edena-runtime.yaml",
"cron/rituals.yaml",
]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["operating authority","institutional operating authority","implementation approved","implementation approval","deployment approved","deployment approval","clinical deployment approved","clinical deployment approval","clinical workflow approved","clinical governance authority","policy authority","policy enforcement","compliance approved","compliance determination","legally approved","legal advice","procurement approved","procurement approval","budget approved","budget approval","contract approved","contracting authority","staffing decision","staffing approval","labor relations decision","hr decision","credentialing authority","certification authority","automatic implementation","automatically implement","automatic owner assignment","automatically assign owners","automatic stakeholder notification","automatically notify","automatic escalation","automatically escalate","automatic dashboard publication","automatically publish dashboard"]
SAFE_NEGATIONS=["not ","no ","does not","do not","may not","never ","advisory","draft","human review","human institutional steward review","requires human","requires separate","refer","refers","referral","out of scope","stop","pause","non-authority","no-deployment","not legal","not compliance","not procurement","not clinical","not staffing","not implementation","not institutional","not policy","not budget","not contract","not hr"]

def refuse(msg): print(f"❌ REFUSED: {msg}",file=sys.stderr); sys.exit(2)
def read(path):
    try: return path.read_text(encoding='utf-8')
    except Exception: return ''
def load_yaml(path):
    try: return yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception: return None
def hits(patterns, blob):
    out=[]
    for pat,label in patterns:
        m=pat.search(blob)
        if m: out.append(f"{label}: {m.group(0)[:32]!r}")
    return out
def unsupported_overclaims(blob):
    found=[]
    for line in blob.splitlines():
        stripped=line.strip().lower()
        if not stripped: continue
        if stripped.startswith('-') or stripped.startswith('>') or stripped.startswith('|') or stripped.startswith('#'):
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
    failures=[]; warnings=[]
    if missing: failures.append('missing required stewardship files: '+', '.join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; stewardship=runtime.get('stewardship',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase21': failures.append(f"runtime version is not 2.0.0-phase21: {runtime.get('version')}")
    if stewardship.get('path')!='20-Stewardship-Operating-Model/': failures.append('runtime stewardship.path is not 20-Stewardship-Operating-Model/')
    if stewardship.get('stewardship_use')!='advisory_operating_model_not_institutional_authority': failures.append('runtime stewardship_use must remain advisory operating model, not institutional authority')
    for key in ['legal_advice','compliance_determination','procurement_approval','budget_approval','contracting_authority','institutional_policy_authority','clinical_governance_authority','clinical_deployment_approval','staffing_decision','labor_relations_decision','credentialing','certification','auto_implement','auto_assign_owners','auto_notify_stakeholders','auto_escalate','auto_publish_dashboard']:
        if stewardship.get(key) is not False: failures.append(f'runtime stewardship.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 20 Institutional Stewardship Operating Model Pack','Operating Model Overview','Role and Cadence Map','Intake-to-Decision Workflow','Human-Gate RACI','Stewardship Meeting Agenda','Risk Escalation Map','Stewardship Metrics Scorecard','Implementation Backlog Template','Adoption Readiness Conversation Guide','Non-Authority and No-Deployment Statement','Quarterly Stewardship Review','No PHI','No patient care use','No clinical decision support','Advisory operating model only','Not legal advice','Not compliance determination','Not procurement approval','Not clinical deployment approval','No staffing decisions','No automatic implementation','No automatic owner assignment','No automatic stakeholder notification','No automatic escalation','Human institutional steward review is required','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'stewardship pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in stewardship pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in stewardship pack: '+'; '.join(secrets))
    if over: failures.append('unsupported stewardship authority/implementation overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':20,'status':status,'stewardship_ready':not failures,'safe_to_coordinate':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'stewardship_path':'20-Stewardship-Operating-Model/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'advisory_operating_model_only':'advisory operating model only' in combined.lower(),'no_stewardship_overclaims':not bool(over),'no_legal_advice':stewardship.get('legal_advice') is False,'no_compliance_determination':stewardship.get('compliance_determination') is False,'no_procurement_approval':stewardship.get('procurement_approval') is False,'no_budget_approval':stewardship.get('budget_approval') is False,'no_contracting_authority':stewardship.get('contracting_authority') is False,'no_institutional_policy_authority':stewardship.get('institutional_policy_authority') is False,'no_clinical_governance_authority':stewardship.get('clinical_governance_authority') is False,'no_clinical_deployment_approval':stewardship.get('clinical_deployment_approval') is False,'no_staffing_decision':stewardship.get('staffing_decision') is False,'no_labor_relations_decision':stewardship.get('labor_relations_decision') is False,'no_credentialing':stewardship.get('credentialing') is False,'no_certification':stewardship.get('certification') is False,'no_auto_implement':stewardship.get('auto_implement') is False,'no_auto_assign_owners':stewardship.get('auto_assign_owners') is False,'no_auto_notify_stakeholders':stewardship.get('auto_notify_stakeholders') is False,'no_auto_escalate':stewardship.get('auto_escalate') is False,'no_auto_publish_dashboard':stewardship.get('auto_publish_dashboard') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'stewardship_use':stewardship.get('stewardship_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}

def main():
    ap=argparse.ArgumentParser(description='Check Phase 20 Institutional Stewardship Operating Model Pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to stewardship-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 20 institutional stewardship operating model check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ STEWARDSHIP OPERATING MODEL READY — advisory only, no legal/compliance/procurement/clinical/staffing authority, no automatic implementation.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
