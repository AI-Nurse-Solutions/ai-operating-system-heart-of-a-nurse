#!/usr/bin/env python3
"""Build the standalone deterministic THRIVE Wellness Marketing & Management release.

Packages files only. It never installs THRIVE, modifies a Hermes profile, creates
memory, connects systems, schedules work, runs agents, contacts people, publishes,
spends, or performs a clinical, marketing, employment, financial, or external action.
"""
from __future__ import annotations
import hashlib,json,re,sys,zipfile
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'wellness-services-marketing-managers'
PACKAGE=ROOT/'packages/thrive'
DOWNLOADS=ROOT/'downloads'
ZIP_NAME='thrive-wellness-marketing-management-complete-edition.zip'
ZIP_PREFIX='THRIVE-Wellness-Marketing-Management-Complete-Edition'
FIXED_ZIP_TIME=(2026,7,17,0,0,0)
PROGRAM_NAME='Wellness-Services-Marketer-and-Manager-Complete-AI-OS-with-THRIVE-SuperPowers-Hermes-Program.md'
SOURCE_PACK='Wellness-Services-Marketer-and-Manager-THRIVE-SuperPowers-Pack-v1.0'
WRAPPER_DIGESTS={
 '00-READ-FIRST.md':'12941b98af5cabc887a9f164b43e7ed4c82aa450d9b94231d544726a0ccbe8b1',
 'ROLE-PACK.json':'40fbb009ccf2c5d421535c368c5e13904b26839cf0b30f032af79ff1e7a832c6',
}

def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def package_files()->dict[str,Path]:
 files={}
 for p in PACKAGE.rglob('*'):
  if p.is_symlink():raise ValueError(f'THRIVE package symlink forbidden: {p.relative_to(PACKAGE)}')
  if p.is_file():files[p.relative_to(PACKAGE).as_posix()]=p
 return files

def parse_ledger(path:Path)->dict[str,str]:
 out={}
 for line in path.read_text(encoding='utf-8').splitlines():
  m=re.fullmatch(r'([0-9a-f]{64})  ([^\\]+)',line)
  if not m:raise ValueError(f'Invalid THRIVE checksum line: {line!r}')
  digest,name=m.groups()
  parts=Path(name).parts
  if name.startswith('/') or '..' in parts or name in out:raise ValueError(f'Unsafe/duplicate THRIVE checksum path: {name}')
  out[name]=digest
 return out

def load_manifest()->dict:
 for name,digest in WRAPPER_DIGESTS.items():
  if sha256(PACKAGE/name)!=digest:raise ValueError(f'THRIVE trusted wrapper digest mismatch: {name}')
 m=json.loads((PACKAGE/'ROLE-PACK.json').read_text(encoding='utf-8'))
 expected={
  'activation':'user_initiated_guided_complete_setup_with_combined_activation_card',
  'canonical_dashboard_route':'/wellness-services-marketing-managers/dashboard','dashboard_alias':'/wellness-services-marketing-managers/mission-control',
  'fixtures_adapters_total':10,'mission_control':'My THRIVE Mission Control','namespace':'wellness_thrive.*',
  'optional_superpowers_active_after_install':0,'optional_superpowers_total':24,'package_version':'2026.07.17.1',
  'population_lane':'wellness_services_marketing_management','program_id':'WELLMKT-AIOS-THRIVE-COMPLETE-1.0',
  'records_total':18,'role':'Wellness Services Marketer & Manager — THRIVE','route':'/wellness-services-marketing-managers/',
  'runtime_criteria':{'publication_status':'specified_not_prepassed','s1':40,'s2':120,'total':160},
  'schemas_total':18,'suggested_agents_active_after_install':0,'suggested_agents_total':10,'templates_total':30,'workflows_total':24,
 }
 for k,v in expected.items():
  if m.get(k)!=v:raise ValueError(f'THRIVE manifest mismatch for {k}')
 true_keys=('foundation_first','institutional_deployment_requires_separate_authorization','no_phi','pre_install_disclosure_required','standalone_wellness_business_lane','thrive_overlay_second')
 false_keys=('automatic_connectors','automatic_cron','automatic_external_actions','automatic_memory','automatic_shared_access','clinical_decisions','employment_decisions','financial_or_procurement_authority','health_claim_release_authority','hospital_administration_population_state_shared','install_on_download','live_person_contact','medical_resident_population_state_shared','nursing_population_state_shared','official_system_writes','person_level_data_allowed','respiratory_care_population_state_shared','role_selection_verifies_credentials_or_authority')
 for k in true_keys:
  if m.get(k) is not True:raise ValueError(f'THRIVE safe flag must be true: {k}')
 for k in false_keys:
  if m.get(k) is not False:raise ValueError(f'THRIVE safe flag must be false: {k}')
 return m

def validate_sources(m:dict,files:dict[str,Path])->None:
 records=m.get('source_files',[])
 if len(records)!=23:raise ValueError('THRIVE source record count must be 23')
 record_paths=[]
 for r in records:
  name=r['packaged_path'];record_paths.append(name)
  if name not in files:raise ValueError(f'Missing THRIVE packaged source: {name}')
  p=files[name]
  if p.stat().st_size!=r['bytes'] or sha256(p)!=r['source_sha256']:raise ValueError(f'THRIVE packaged source drift: {name}')
  for key in ('upstream_path','upstream_sha256','upstream_bytes','transformation'):
   if key not in r:raise ValueError(f'THRIVE provenance field missing: {name}/{key}')
 if len(record_paths)!=len(set(record_paths)):raise ValueError('Duplicate THRIVE source records')
 expected=set(record_paths)|{'00-READ-FIRST.md','ROLE-PACK.json','PACKAGE-CHECKSUMS.sha256'}
 if set(files)!=expected:raise ValueError(f'THRIVE exact inventory mismatch: {sorted(set(files)^expected)}')
 ledger=parse_ledger(PACKAGE/'PACKAGE-CHECKSUMS.sha256')
 expected_ledger=set(files)-{'PACKAGE-CHECKSUMS.sha256'}
 if set(ledger)!=expected_ledger:raise ValueError('THRIVE package checksum coverage mismatch')
 for name,digest in ledger.items():
  if sha256(files[name])!=digest:raise ValueError(f'THRIVE package checksum mismatch: {name}')
 upstream=parse_ledger(PACKAGE/'UPSTREAM-SHA256SUMS.txt')
 if len(upstream)!=22:raise ValueError('THRIVE upstream ledger must contain 22 entries')
 upstream_records={r['upstream_path']:r for r in records if r['upstream_path']!='SHA256SUMS.txt'}
 if set(upstream)!=set(upstream_records):raise ValueError('THRIVE upstream ledger/source-record mismatch')
 for name,digest in upstream.items():
  if upstream_records[name]['upstream_sha256']!=digest:raise ValueError(f'THRIVE upstream digest mismatch: {name}')

def validate_program()->None:
 program=(PACKAGE/PROGRAM_NAME).read_text(encoding='utf-8')
 required=(
  'exact combined **THRIVE Activation Card**','Stop after displaying the card. Create no state and wait for explicit post-card authority.',
  'general request to “publish and install” is never approval','invalidates approval and requires a new card',
  'INSTALL THRIVE AFTER S0 — USE EXACT VERIFIED COMPONENT HASHES AND KEEP ALL POWERS AND AGENTS INACTIVE.','**Nothing installs or continues in the background.**',
 )
 for phrase in required:
  if phrase not in program:raise ValueError(f'THRIVE program consent contract missing: {phrase}')
 marker=re.compile(r'<!-- BEGIN COMPONENT: ([^|]+) \| SHA256: ([0-9a-f]{64}) -->\n(.*?)\n<!-- END COMPONENT: \1 -->',re.S)
 blocks=marker.findall(program)
 if len(blocks)!=17:raise ValueError(f'THRIVE embedded component count {len(blocks)}')
 for rel,digest,body in blocks:
  p=PACKAGE/SOURCE_PACK/rel.strip()
  if not p.is_file() or sha256(p)!=digest or body.strip()!=p.read_text(encoding='utf-8').strip():raise ValueError(f'THRIVE embedded component mismatch: {rel}')
 read_first=(PACKAGE/'00-READ-FIRST.md').read_text(encoding='utf-8')
 for phrase in ('Downloading, selecting, opening, or unzipping this package does not install or activate anything','specified—not pre-passed','Private-workspace approval does not authorize organizational deployment'):
  if phrase not in read_first:raise ValueError(f'THRIVE wrapper boundary missing: {phrase}')

def build()->dict:
 m=load_manifest();files=package_files();validate_sources(m,files);validate_program()
 DOWNLOADS.mkdir(parents=True,exist_ok=True);output=DOWNLOADS/ZIP_NAME
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in sorted(files):
   info=zipfile.ZipInfo(f'{ZIP_PREFIX}/{name}',FIXED_ZIP_TIME);info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,files[name].read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 record={k:m[k] for k in ('activation','foundation_first','install_on_download','installation_status','institutional_deployment_requires_separate_authorization','no_phi','optional_superpowers_active_after_install','optional_superpowers_total','package_version','person_level_data_allowed','population_lane','pre_install_disclosure_required','role','route','runtime_criteria','schemas_total','standalone_wellness_business_lane','suggested_agents_active_after_install','suggested_agents_total','templates_total','workflows_total')}
 record.update({'bytes':output.stat().st_size,'download':f'downloads/{ZIP_NAME}','sha256':sha256(output)})
 public={'installation_status':'not_installed','packages':[record],'purpose':'standalone wellness services marketing and management lane; isolated from nursing, clinical, research, respiratory, resident, and hospital-administration state','release':m['package_version'],'schema_version':'1.0'}
 (DOWNLOADS/'manifest.json').write_text(json.dumps(public,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 (DOWNLOADS/'CHECKSUMS.sha256').write_text(f'{record["sha256"]}  {ZIP_NAME}\n',encoding='utf-8')
 print('THRIVE_PACKAGES=1');print('INSTALLATION_STATUS=not_installed');print(f'THRIVE_ZIP_SHA256={record["sha256"]}');print(f'THRIVE_ZIP_BYTES={record["bytes"]}')
 return record

def main()->int:
 try:build()
 except Exception as e:print(f'ERROR: {e}',file=sys.stderr);return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
