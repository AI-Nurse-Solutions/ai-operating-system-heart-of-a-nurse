#!/usr/bin/env python3
"""NAIO OS — partner.py (Phase 19). Informational partner/sponsor briefing only; not solicitation, approval, procurement, funding, or clinical deployment authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for partner.py") from e

REQUIRED=[
"19-Partner-Briefing/README.md",
"19-Partner-Briefing/Partner-Briefing-Overview.md",
"19-Partner-Briefing/One-Page-Partner-Brief.md",
"19-Partner-Briefing/Use-Case-Boundary-Map.md",
"19-Partner-Briefing/Stakeholder-Question-Prep.md",
"19-Partner-Briefing/Claim-vs-Proof-Ledger.md",
"19-Partner-Briefing/Demo-Boundary-Script.md",
"19-Partner-Briefing/Partner-Intake-Form.md",
"19-Partner-Briefing/Risk-and-Referral-Notes.md",
"19-Partner-Briefing/Sponsor-Conversation-Guide.md",
"19-Partner-Briefing/Non-Solicitation-and-Non-Approval-Statement.md",
"19-Partner-Briefing/Follow-Up-Decision-Record.md",
"config/edena-runtime.yaml",
"cron/rituals.yaml",
]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["funding secured","funding approved","sponsor approved","sponsor approval","partnership approved","partnership approval","partner approved","contract approved","contracting authority","grant approved","grant application approved","investment advice","fundraising solicitation","securities offering","guaranteed roi","guaranteed outcomes","donation processed","donation accepted","procurement approval","vendor approval","institutional endorsement","institutional approval","compliance determination","legal advice","clinical deployment approval","clinical approval","clinical validation","safety validation","efficacy validation","clinically safe","clinically effective","automatic outreach","automatically contact","automatic follow-up","automatically follow up","automatic sharing","automatically send","automatic data room","automatically create a data room","automatic acceptance of funding","automatically accept funding"]
SAFE_NEGATIONS=["not ","no ","does not","do not","may not","never ","informational only","informational","human review","human partner steward review","advisory","out of scope","refers","refer","requires human","stop","pause","would require","requires separate","non-solicitation","non-approval","not a solicitation","not investment advice","not legal advice","not compliance","not procurement","not partnership","not sponsor","not institutional","not clinical","not funding","not a contract","not a grant"]

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
        # Boundary templates intentionally list prohibited claims as bullets/tables.
        # Runtime YAML may encode explicit false guards; do not flag those as affirmative claims.
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
    if missing: failures.append('missing required partner files: '+', '.join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; partner=runtime.get('partner',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase19': failures.append(f"runtime version is not 2.0.0-phase19: {runtime.get('version')}")
    if partner.get('path')!='19-Partner-Briefing/': failures.append('runtime partner.path is not 19-Partner-Briefing/')
    if partner.get('partner_use')!='informational_partner_briefing_not_solicitation_or_approval': failures.append('runtime partner_use must remain informational, not solicitation or approval')
    for key in ['fundraising_solicitation','investment_advice','grant_application','contracting_authority','partnership_approval','sponsor_approval','institutional_endorsement','procurement_approval','clinical_deployment_approval','legal_advice','compliance_determination','auto_contact_partners','auto_send_materials','auto_follow_up','auto_create_data_room','auto_accept_funding']:
        if partner.get(key) is not False: failures.append(f'runtime partner.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 19 Partner / Sponsor Briefing Pack','Partner Briefing Overview','One-Page Partner Brief','Use-Case Boundary Map','Stakeholder Question Prep','Claim-vs-Proof Ledger','Demo Boundary Script','Partner Intake Form','Risk and Referral Notes','Sponsor Conversation Guide','Non-Solicitation and Non-Approval Statement','Follow-Up Decision Record','No PHI','No patient care use','No clinical decision support','Informational only','Not fundraising solicitation','Not investment advice','Not legal advice','Not compliance determination','Not partnership approval','Not sponsor approval','Not institutional endorsement','Not procurement approval','Not clinical deployment approval','No automatic outreach','No automatic sending','No automatic follow-up','No automatic data room','No automatic acceptance of funding','Human partner steward review is required','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'partner pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in partner pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in partner pack: '+'; '.join(secrets))
    if over: failures.append('unsupported partner/funding/approval overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':19,'status':status,'partner_ready':not failures,'safe_to_brief':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'partner_path':'19-Partner-Briefing/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'informational_only':'informational only' in combined.lower(),'no_partner_overclaims':not bool(over),'no_fundraising_solicitation':partner.get('fundraising_solicitation') is False,'no_investment_advice':partner.get('investment_advice') is False,'no_grant_application':partner.get('grant_application') is False,'no_contracting_authority':partner.get('contracting_authority') is False,'no_partnership_approval':partner.get('partnership_approval') is False,'no_sponsor_approval':partner.get('sponsor_approval') is False,'no_institutional_endorsement':partner.get('institutional_endorsement') is False,'no_procurement_approval':partner.get('procurement_approval') is False,'no_clinical_deployment_approval':partner.get('clinical_deployment_approval') is False,'no_legal_advice':partner.get('legal_advice') is False,'no_compliance_determination':partner.get('compliance_determination') is False,'no_auto_contact_partners':partner.get('auto_contact_partners') is False,'no_auto_send_materials':partner.get('auto_send_materials') is False,'no_auto_follow_up':partner.get('auto_follow_up') is False,'no_auto_create_data_room':partner.get('auto_create_data_room') is False,'no_auto_accept_funding':partner.get('auto_accept_funding') is False,'no_mutation':True,'cron_scheduled':bool(scheduled),'partner_use':partner.get('partner_use','unknown'),'doctrine':runtime.get('doctrine','Agents propose. Humans judge. Nurses steward.')}

def main():
    ap=argparse.ArgumentParser(description='Check Phase 19 Partner / Sponsor Briefing Pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to partner-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 19 partner / sponsor briefing check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ PARTNER BRIEFING PACK READY — informational only, no solicitation, no approval, no automatic outreach.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
