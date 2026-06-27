#!/usr/bin/env python3
"""NAIO OS — registry.py (Phase 16). Human-reviewed learning registry only; not endorsement."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for registry.py") from e
REQUIRED=["16-Agent-Registry/README.md","16-Agent-Registry/Registry-Overview.md","16-Agent-Registry/Agent-Intake-Card.md","16-Agent-Registry/Source-Verification-Checklist.md","16-Agent-Registry/EDENA-Agent-Evaluation.md","16-Agent-Registry/Risk-and-Boundary-Review.md","16-Agent-Registry/Nurse-Use-Case-Fit.md","16-Agent-Registry/Registry-Listing-Template.md","16-Agent-Registry/Not-Endorsement-Statement.md","16-Agent-Registry/Human-Review-Queue.md","16-Agent-Registry/Registry-Change-Log.md","16-Agent-Registry/Retirement-and-Recheck-Plan.md","config/edena-runtime.yaml","cron/rituals.yaml"]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["endorsed","approved","certified","validated","clinically ready","clinical ai readiness granted","procurement-ready","procurement ready","deployment-ready","deployment ready","approved for patient care","institutionally approved","compliance validated","safety validated","efficacy validated","safe and effective"]
SAFE_NEGATIONS=["not endorsement","not an endorsement","does not mean endorsement","does not mean endorsed","not certification","not clinical ai readiness","not procurement","not deployment","not safety validation","not efficacy validation","no automatic","do not say","avoid","what cannot be said","does not","not permission","not institutional","do not list","not suitable","not allowed","hard stop","red flags","retire or pause","no patient care","no clinical","cannot be said","registry does not mean"]
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
    if missing: failures.append("missing required registry files: "+", ".join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; registry=runtime.get('registry',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase16': failures.append(f"runtime version is not 2.0.0-phase16: {runtime.get('version')}")
    if registry.get('path')!='16-Agent-Registry/': failures.append('runtime registry.path is not 16-Agent-Registry/')
    if registry.get('registry_use')!='human_reviewed_learning_registry_not_endorsement': failures.append('runtime registry_use must remain human-reviewed learning registry, not endorsement')
    for key in ['auto_vet','auto_list','auto_execute_agent','auto_recommend_for_patient_care']:
        if registry.get(key) is not False: failures.append(f'runtime registry.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 16 NAIO Agent Registry Pack','Registry Overview','Agent Intake Card','Source Verification Checklist','EDENA Agent Evaluation','Risk and Boundary Review','Nurse Use-Case Fit','Registry Listing Template','Not-Endorsement Statement','Human Review Queue','Registry Change Log','Retirement and Recheck Plan','No PHI','No patient care use','No clinical decision support','Not endorsement','Not certification','Not clinical AI readiness','Not procurement approval','Not deployment approval','No automatic vetting','No automatic listing','No automatic agent execution','Human registry steward review','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'registry pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in registry pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in registry pack: '+'; '.join(secrets))
    if over: failures.append('unsupported registry endorsement/deployment overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':16,'status':status,'registry_ready':not failures,'safe_to_list':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'registry_path':'16-Agent-Registry/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'no_endorsement_claims':not bool(over),'no_certification_claims':not bool(over),'no_clinical_readiness_claims':not bool(over),'no_procurement_approval_claims':not bool(over),'no_deployment_approval_claims':not bool(over),'no_auto_vet':registry.get('auto_vet') is False,'no_auto_list':registry.get('auto_list') is False,'no_auto_execute_agent':registry.get('auto_execute_agent') is False,'no_auto_patient_care_recommendation':registry.get('auto_recommend_for_patient_care') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'registry_use':registry.get('registry_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}
def main():
    ap=argparse.ArgumentParser(description='Check Phase 16 NAIO Agent Registry pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to registry-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 16 agent registry check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ REGISTRY PACK READY — human-reviewed learning registry only, no endorsement, no clinical deployment claims.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
