#!/usr/bin/env python3
"""NAIO OS — outcomes.py (Phase 22). Adoption & Outcomes Ledger only; not clinical efficacy, patient outcome, ROI, staffing, compliance, certification, research, QI, or performance-evaluation authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for outcomes.py") from e

REQUIRED=[
"22-Adoption-Outcomes-Ledger/README.md",
"22-Adoption-Outcomes-Ledger/Adoption-Ledger-Overview.md",
"22-Adoption-Outcomes-Ledger/Safe-Use-Metrics-Map.md",
"22-Adoption-Outcomes-Ledger/Time-Saved-Estimate-Worksheet.md",
"22-Adoption-Outcomes-Ledger/Human-Gate-Pattern-Log.md",
"22-Adoption-Outcomes-Ledger/Friction-and-Risk-Register.md",
"22-Adoption-Outcomes-Ledger/Nurse-Confidence-Pulse.md",
"22-Adoption-Outcomes-Ledger/Workflow-Before-After-Capture.md",
"22-Adoption-Outcomes-Ledger/Learning-Milestone-Ledger.md",
"22-Adoption-Outcomes-Ledger/Cohort-Adoption-Summary.md",
"22-Adoption-Outcomes-Ledger/Institutional-Signal-Brief.md",
"22-Adoption-Outcomes-Ledger/Non-Clinical-Outcome-and-No-Efficacy-Claim-Statement.md",
"22-Adoption-Outcomes-Ledger/Adoption-Decision-Record.md",
"config/edena-runtime.yaml",
"cron/rituals.yaml",
]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT|room number|patient name)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["clinically validated","clinical efficacy","efficacy proven","patient outcome improvement","patient outcomes improved","improves patient outcomes","improved patient outcomes","clinical outcome improvement","reduces errors","error reduction proven","mortality reduction","readmission reduction","length of stay reduction","improves safety","safety validated","quality measure impact","quality measure improvement","quality score improvement","roi guaranteed","guaranteed roi","proves roi","return on investment guaranteed","staffing reduction","reduced staffing","solves staffing","staffing efficiency proven","compliance validated","compliance approved","certifies competency","certified competent","competency certified","competency validation","performance evaluation","manager notification","automatic dashboard publication","automatically publish dashboard","automatic institutional reporting","automatically send report","automatic manager notification","automatic performance evaluation","automatic score calculation","automatic scoring","research approved","irb approved","quality improvement approved","qi approved","billing claim","reimbursement claim","procurement approval","deployment approved","badge issued","credential issued"]
SAFE_NEGATIONS=["not ","no ","does not","do not","may not","never ","advisory","draft","estimate","estimated","self-reported","reflection","human review","human steward review","requires human","requires separate","refer","refers","referral","out of scope","stop","pause","non-clinical","not clinical","not patient","not safety","not quality","not roi","not staffing","not compliance","not certification","not performance","not research","not irb","not qi","not billing","not reimbursement","not procurement","not deployment","learning evidence","adoption signal","not a claim"]

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
    if missing: failures.append('missing required outcomes files: '+', '.join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; outcomes=runtime.get('outcomes',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase22': failures.append(f"runtime version is not 2.0.0-phase22: {runtime.get('version')}")
    if outcomes.get('path')!='22-Adoption-Outcomes-Ledger/': failures.append('runtime outcomes.path is not 22-Adoption-Outcomes-Ledger/')
    if outcomes.get('outcomes_use')!='adoption_signal_and_learning_evidence_not_clinical_or_financial_outcomes_claims': failures.append('runtime outcomes_use must remain adoption signal/learning evidence only')
    for key in ['clinical_efficacy_claim','patient_outcome_improvement_claim','patient_safety_validation','quality_measure_impact_claim','roi_guarantee','staffing_reduction_claim','compliance_validation','competency_certification','performance_evaluation','research_determination','irb_determination','quality_improvement_approval','billing_or_reimbursement_claim','procurement_approval','deployment_approval','auto_score','auto_publish_dashboard','auto_send_report','auto_notify_manager','auto_evaluate_performance','auto_escalate','auto_submit_to_institution','auto_issue_badge','auto_issue_credential']:
        if outcomes.get(key) is not False: failures.append(f'runtime outcomes.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 22 Adoption & Outcomes Ledger Pack','Adoption Ledger Overview','Safe-Use Metrics Map','Time-Saved Estimate Worksheet','Human-Gate Pattern Log','Friction and Risk Register','Nurse Confidence Pulse','Workflow Before-After Capture','Learning Milestone Ledger','Cohort Adoption Summary','Institutional Signal Brief','Non-Clinical Outcome and No-Efficacy-Claim Statement','Adoption Decision Record','No PHI','No patient care use','No clinical decision support','Adoption signal and learning evidence only','Not clinical efficacy','Not patient outcome improvement','Not safety validation','Not ROI guarantee','Not staffing reduction','Not compliance validation','Not competency certification','No automatic dashboard publication','No automatic institutional reporting','No automatic manager notification','Human steward review is required','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'outcomes pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in outcomes pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in outcomes pack: '+'; '.join(secrets))
    if over: failures.append('unsupported outcomes/impact overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':22,'status':status,'outcomes_ready':not failures,'safe_to_measure':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'outcomes_path':'22-Adoption-Outcomes-Ledger/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'adoption_signal_only':'adoption signal and learning evidence only' in combined.lower(),'no_outcome_overclaims':not bool(over),'no_clinical_efficacy_claim':outcomes.get('clinical_efficacy_claim') is False,'no_patient_outcome_improvement_claim':outcomes.get('patient_outcome_improvement_claim') is False,'no_patient_safety_validation':outcomes.get('patient_safety_validation') is False,'no_quality_measure_impact_claim':outcomes.get('quality_measure_impact_claim') is False,'no_roi_guarantee':outcomes.get('roi_guarantee') is False,'no_staffing_reduction_claim':outcomes.get('staffing_reduction_claim') is False,'no_compliance_validation':outcomes.get('compliance_validation') is False,'no_competency_certification':outcomes.get('competency_certification') is False,'no_performance_evaluation':outcomes.get('performance_evaluation') is False,'no_research_determination':outcomes.get('research_determination') is False,'no_irb_determination':outcomes.get('irb_determination') is False,'no_qi_approval':outcomes.get('quality_improvement_approval') is False,'no_billing_or_reimbursement_claim':outcomes.get('billing_or_reimbursement_claim') is False,'no_procurement_approval':outcomes.get('procurement_approval') is False,'no_deployment_approval':outcomes.get('deployment_approval') is False,'no_auto_score':outcomes.get('auto_score') is False,'no_auto_publish_dashboard':outcomes.get('auto_publish_dashboard') is False,'no_auto_send_report':outcomes.get('auto_send_report') is False,'no_auto_notify_manager':outcomes.get('auto_notify_manager') is False,'no_auto_evaluate_performance':outcomes.get('auto_evaluate_performance') is False,'no_auto_escalate':outcomes.get('auto_escalate') is False,'no_auto_submit_to_institution':outcomes.get('auto_submit_to_institution') is False,'no_auto_issue_badge':outcomes.get('auto_issue_badge') is False,'no_auto_issue_credential':outcomes.get('auto_issue_credential') is False,'cron_templates_only':rituals.get('mode')=='templates_only_not_scheduled','no_mutation':True}

def main():
    ap=argparse.ArgumentParser(description='Check Phase 22 Adoption & Outcomes Ledger Pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to outcomes-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 22 adoption & outcomes ledger check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ OUTCOMES LEDGER READY — adoption signals and learning evidence only; no clinical efficacy, patient outcome, ROI, staffing, compliance, certification, performance-evaluation, or automatic reporting claims.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
