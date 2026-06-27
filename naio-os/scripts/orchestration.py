#!/usr/bin/env python3
"""NAIO OS — orchestration.py (Phase 17). Florence-X dry-run orchestration preview only."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for orchestration.py") from e
REQUIRED=["17-Florence-X-Orchestration/README.md","17-Florence-X-Orchestration/Orchestration-Overview.md","17-Florence-X-Orchestration/Shared-Intent-Card.md","17-Florence-X-Orchestration/Shared-Context-Card.md","17-Florence-X-Orchestration/Semantic-State-Card.md","17-Florence-X-Orchestration/Agent-Role-Map.md","17-Florence-X-Orchestration/Handoff-Contract.md","17-Florence-X-Orchestration/Interaction-Fields-Checklist.md","17-Florence-X-Orchestration/Human-Orchestrator-Review.md","17-Florence-X-Orchestration/Dry-Run-Orchestration-Plan.md","17-Florence-X-Orchestration/Stop-and-Escalation-Rules.md","17-Florence-X-Orchestration/Trace-Ledger.md","17-Florence-X-Orchestration/Non-Deployment-Statement.md","config/edena-runtime.yaml","cron/rituals.yaml"]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["autonomous orchestration","multi-agent runtime enabled","shared memory enabled","shared memory runtime enabled","automatic handoff","automatic routing","automatic escalation","automatic agent execution","clinical orchestration","patient-care coordination","patient care coordination","production deployment","production-ready","deployment-ready","approved for clinical use","clinically ready","safety validated","efficacy validated"]
SAFE_NEGATIONS=["not autonomous","not multi-agent runtime","not runtime","no shared memory runtime","shared memory is orange-deferred","orange-deferred","deferred","no automatic","do not say","not clinical","not patient","not deployment","not production","not safety validation","not efficacy validation","does not enable","does not", "preview only", "dry-run", "dry run", "template", "stop immediately", "stop rule", "not execution", "not a database", "not automated", "no patient care"]
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
    if missing: failures.append("missing required orchestration files: "+", ".join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; orchestration=runtime.get('orchestration',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase17': failures.append(f"runtime version is not 2.0.0-phase17: {runtime.get('version')}")
    if orchestration.get('path')!='17-Florence-X-Orchestration/': failures.append('runtime orchestration.path is not 17-Florence-X-Orchestration/')
    if orchestration.get('orchestration_use')!='dry_run_preview_not_autonomous_multi_agent_runtime': failures.append('runtime orchestration_use must remain dry-run preview, not autonomous runtime')
    if orchestration.get('shared_memory_posture')!='orange_deferred_until_governed_review': failures.append('shared_memory_posture must remain orange_deferred_until_governed_review')
    for key in ['auto_handoff','auto_route','auto_execute_agents','auto_escalate','shared_memory_runtime']:
        if orchestration.get(key) is not False: failures.append(f'runtime orchestration.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 17 Florence-X Orchestration Preview Pack','Orchestration Overview','Shared Intent Card','Shared Context Card','Florence-X Semantic State Card','Agent Role Map','Handoff Contract','Interaction Fields Checklist','Human Orchestrator Review','Dry-Run Orchestration Plan','Stop and Escalation Rules','Trace Ledger','Non-Deployment Statement','No PHI','No patient care use','No clinical decision support','Preview only','Dry-run templates only','Not autonomous orchestration','Not multi-agent runtime enablement','No shared memory runtime','Shared memory is Orange-deferred until governed review','No automatic handoffs','No automatic agent execution','No automatic routing','No automatic escalation','Human orchestrator review','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'orchestration pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in orchestration pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in orchestration pack: '+'; '.join(secrets))
    if over: failures.append('unsupported orchestration/runtime overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':17,'status':status,'orchestration_ready':not failures,'safe_to_rehearse':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'orchestration_path':'17-Florence-X-Orchestration/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'no_autonomous_orchestration_claims':not bool(over),'no_runtime_enablement_claims':not bool(over),'no_shared_memory_runtime':orchestration.get('shared_memory_runtime') is False,'shared_memory_orange_deferred':orchestration.get('shared_memory_posture')=='orange_deferred_until_governed_review','no_auto_handoff':orchestration.get('auto_handoff') is False,'no_auto_route':orchestration.get('auto_route') is False,'no_auto_execute_agents':orchestration.get('auto_execute_agents') is False,'no_auto_escalate':orchestration.get('auto_escalate') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'orchestration_use':orchestration.get('orchestration_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}
def main():
    ap=argparse.ArgumentParser(description='Check Phase 17 Florence-X orchestration preview pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to orchestration-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 17 Florence-X orchestration check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ ORCHESTRATION PREVIEW READY — dry-run templates only, no autonomous runtime, no shared memory runtime.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
