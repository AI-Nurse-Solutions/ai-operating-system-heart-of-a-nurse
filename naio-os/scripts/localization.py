#!/usr/bin/env python3
"""NAIO OS — localization.py (Phase 21). Localization / International Readiness Lane only; not legal, regulatory, compliance, translation certification, licensure, immigration, clinical deployment, or local institutional approval authority."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required for localization.py") from e

REQUIRED=[
"21-Localization-Readiness/README.md",
"21-Localization-Readiness/Localization-Readiness-Overview.md",
"21-Localization-Readiness/Region-and-Audience-Map.md",
"21-Localization-Readiness/Language-and-Tone-Adaptation-Guide.md",
"21-Localization-Readiness/Jurisdiction-Boundary-Checklist.md",
"21-Localization-Readiness/Cultural-Stewardship-Interview.md",
"21-Localization-Readiness/Local-Partner-Question-Prep.md",
"21-Localization-Readiness/Claim-vs-Local-Proof-Ledger.md",
"21-Localization-Readiness/Translation-Review-Workflow.md",
"21-Localization-Readiness/Cross-Border-Data-and-Privacy-Notes.md",
"21-Localization-Readiness/Non-Authority-and-No-Localization-Approval-Statement.md",
"21-Localization-Readiness/Localization-Decision-Record.md",
"config/edena-runtime.yaml",
"cron/rituals.yaml",
]
PHI_PATTERNS=[(re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),"SSN-like pattern"),(re.compile(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b",re.I),"phone-like pattern"),(re.compile(r"\b(?:MRN|medical record|patient id|DOB|date of birth|diagnosis|ICD-?10|CPT)\b[: ]",re.I),"clinical identifier")]
SECRET_PATTERNS=[(re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),"private key"),(re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),"token-like secret"),(re.compile(r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s`]+",re.I),"credential assignment")]
OVERCLAIMS=["legal advice","regulatory advice","compliance determination","localization approved","localization approval","official translation","certified translation","translation certified","translation certification","culturally validated","cultural validation","jurisdiction approved","jurisdictional approval","ministry approved","ministry approval","institutional endorsement","clinical deployment approved","clinical deployment approval","clinical governance authority","procurement approval","procurement approved","cross-border data transfer approved","cross border data transfer approved","data transfer approval","immigration advice","visa advice","licensure advice","nursing license advice","license eligibility","recruitment approved","recruitment activity","fundraising solicitation","automatic translation","automatically translate","automatic localized publication","automatically publish localized","automatic local partner outreach","automatically contact local partners","automatic local steward assignment","automatically assign local stewards","automatic regional data collection","automatically collect regional data","automatic authority submission","automatically submit to authorities"]
SAFE_NEGATIONS=["not ","no ","does not","do not","may not","never ","advisory","draft","human review","human local steward review","requires human","requires separate","refer","refers","referral","out of scope","stop","pause","non-authority","not legal","not regulatory","not compliance","not official","not certified","not jurisdiction","not ministry","not institutional","not clinical","not procurement","not licensure","not immigration","not recruitment","not data transfer","readiness only","not approval"]

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
    if missing: failures.append('missing required localization files: '+', '.join(missing))
    runtime=load_yaml(profile/'config/edena-runtime.yaml') or {}; rituals=load_yaml(profile/'cron/rituals.yaml') or {}; localization=runtime.get('localization',{}) if isinstance(runtime,dict) else {}
    if runtime.get('version')!='2.0.0-phase21': failures.append(f"runtime version is not 2.0.0-phase21: {runtime.get('version')}")
    if localization.get('path')!='21-Localization-Readiness/': failures.append('runtime localization.path is not 21-Localization-Readiness/')
    if localization.get('localization_use')!='adaptation_readiness_not_official_localization_or_jurisdictional_approval': failures.append('runtime localization_use must remain readiness/adaptation only, not official localization or jurisdictional approval')
    for key in ['legal_advice','regulatory_advice','compliance_determination','official_translation','translation_certification','localization_approval','cultural_validation','jurisdictional_approval','ministry_approval','institutional_endorsement','clinical_governance_authority','clinical_deployment_approval','procurement_approval','cross_border_data_transfer_approval','immigration_advice','licensure_advice','recruitment_activity','fundraising_solicitation','auto_translate','auto_publish_localized_materials','auto_contact_local_partners','auto_assign_local_stewards','auto_collect_regional_data','auto_submit_to_authorities']:
        if localization.get(key) is not False: failures.append(f'runtime localization.{key} must be false')
    combined='\n'.join(read(profile/rel) for rel in REQUIRED if (profile/rel).is_file())
    required=['Phase 21 Localization / International Readiness Lane Pack','Localization Readiness Overview','Region and Audience Map','Language and Tone Adaptation Guide','Jurisdiction Boundary Checklist','Cultural Stewardship Interview','Local Partner Question Prep','Claim-vs-Local-Proof Ledger','Translation Review Workflow','Cross-Border Data and Privacy Notes','Non-Authority and No-Localization-Approval Statement','Localization Decision Record','No PHI','No patient care use','No clinical decision support','Readiness and adaptation only','Not legal advice','Not regulatory advice','Not compliance determination','Not official translation','Not translation certification','Not localization approval','Not jurisdictional approval','Not clinical deployment approval','No automatic translation','No automatic localized publishing','No automatic local partner outreach','Human local steward review is required','Agents propose. Humans judge. Nurses steward.']
    for phrase in required:
        if phrase.lower() not in combined.lower(): failures.append(f'localization pack missing phrase: {phrase}')
    phi=hits(PHI_PATTERNS,combined); secrets=hits(SECRET_PATTERNS,combined); over=unsupported_overclaims(combined)
    if phi: failures.append('PHI-like content detected in localization pack: '+'; '.join(phi))
    if secrets: failures.append('secret-like content detected in localization pack: '+'; '.join(secrets))
    if over: failures.append('unsupported localization authority/approval overclaim detected: '+', '.join(sorted(set(over))))
    if rituals.get('mode')!='templates_only_not_scheduled': failures.append('cron rituals mode is not templates_only_not_scheduled')
    scheduled=[]
    if isinstance(runtime.get('cron_rituals'),list): scheduled=[r.get('id') for r in runtime['cron_rituals'] if r.get('scheduled') is not False]
    if scheduled: failures.append('cron rituals appear scheduled: '+', '.join(str(x) for x in scheduled))
    status='ready' if not failures else 'blocked'
    return {'schema_version':'1.0.0','phase':21,'status':status,'localization_ready':not failures,'safe_to_localize':not failures,'generated_at':datetime.now(timezone.utc).isoformat(),'profile':str(profile),'localization_path':'21-Localization-Readiness/','required_files_checked':len(REQUIRED),'missing_required':missing,'warnings':warnings,'failures':failures,'no_phi':not bool(phi),'no_secrets':not bool(secrets),'no_patient_care':'no patient care use' in combined.lower(),'no_clinical_decision_support':'no clinical decision support' in combined.lower(),'readiness_and_adaptation_only':'readiness and adaptation only' in combined.lower(),'no_localization_overclaims':not bool(over),'no_legal_advice':localization.get('legal_advice') is False,'no_regulatory_advice':localization.get('regulatory_advice') is False,'no_compliance_determination':localization.get('compliance_determination') is False,'no_official_translation':localization.get('official_translation') is False,'no_translation_certification':localization.get('translation_certification') is False,'no_localization_approval':localization.get('localization_approval') is False,'no_cultural_validation':localization.get('cultural_validation') is False,'no_jurisdictional_approval':localization.get('jurisdictional_approval') is False,'no_ministry_approval':localization.get('ministry_approval') is False,'no_institutional_endorsement':localization.get('institutional_endorsement') is False,'no_clinical_governance_authority':localization.get('clinical_governance_authority') is False,'no_clinical_deployment_approval':localization.get('clinical_deployment_approval') is False,'no_procurement_approval':localization.get('procurement_approval') is False,'no_cross_border_data_transfer_approval':localization.get('cross_border_data_transfer_approval') is False,'no_immigration_advice':localization.get('immigration_advice') is False,'no_licensure_advice':localization.get('licensure_advice') is False,'no_recruitment_activity':localization.get('recruitment_activity') is False,'no_fundraising_solicitation':localization.get('fundraising_solicitation') is False,'no_auto_translate':localization.get('auto_translate') is False,'no_auto_publish_localized_materials':localization.get('auto_publish_localized_materials') is False,'no_auto_contact_local_partners':localization.get('auto_contact_local_partners') is False,'no_auto_assign_local_stewards':localization.get('auto_assign_local_stewards') is False,'no_auto_collect_regional_data':localization.get('auto_collect_regional_data') is False,'no_auto_submit_to_authorities':localization.get('auto_submit_to_authorities') is False,'no_mutation':True,'cron_scheduled':bool(scheduled)}

def main():
    ap=argparse.ArgumentParser(description='Check Phase 21 Localization / International Readiness Lane Pack for a rendered NAIO profile bundle.'); ap.add_argument('--profile',required=True); ap.add_argument('--json',action='store_true'); args=ap.parse_args(); profile=Path(args.profile).expanduser().resolve()
    if profile==Path.home() or str(profile) in ('/',str(Path.home()/'.hermes')): refuse('refusing to localization-check home or ~/.hermes directly')
    if not profile.is_dir(): refuse(f'profile directory not found: {profile}')
    report=check_profile(profile)
    if args.json: print(json.dumps(report,indent=2))
    else:
        print('\n=== NAIO OS — Phase 21 localization / international readiness lane check ===\n'); print(json.dumps(report,indent=2))
        if report['status']=='ready': print('\n✅ LOCALIZATION READINESS READY — adaptation only; no legal/regulatory/compliance/translation-certification/licensure/clinical/institutional approval, no automatic translation or outreach.')
    return 0 if report['status']=='ready' else 2
if __name__=='__main__': sys.exit(main())
