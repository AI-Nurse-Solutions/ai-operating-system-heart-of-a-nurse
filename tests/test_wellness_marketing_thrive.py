#!/usr/bin/env python3
"""Acceptance, provenance, consent, schema, isolation, video, and package tests for THRIVE."""
from __future__ import annotations
import hashlib,json,re,runpy,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LANE=ROOT/'wellness-services-marketing-managers';PKG=LANE/'packages/thrive';DL=LANE/'downloads'
PROGRAM=PKG/'Wellness-Services-Marketer-and-Manager-Complete-AI-OS-with-THRIVE-SuperPowers-Hermes-Program.md'
SP='Wellness-Services-Marketer-and-Manager-THRIVE-SuperPowers-Pack-v1.0'
ZIP=DL/'thrive-wellness-marketing-management-complete-edition.zip';PREFIX='THRIVE-Wellness-Marketing-Management-Complete-Edition/'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def ledger(path:Path)->dict[str,str]:
 out={}
 for line in path.read_text().splitlines():
  d,n=line.split('  ',1);out[n]=d
 return out
class ThriveReleaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.role=json.loads((PKG/'ROLE-PACK.json').read_text());cls.program=PROGRAM.read_text();cls.page=(LANE/'index.html').read_text();cls.home=(ROOT/'index.html').read_text();cls.admin=(ROOT/'hospital-clinic-administrators/index.html').read_text();cls.builder=(ROOT/'scripts/build-wellness-marketing-thrive.py').read_text()
 def test_source_archive_and_provenance_are_pinned(self):
  self.assertEqual(self.role['source_archive'],{'bytes':536136,'members':23,'sha256':'3561455a9147df173a284e5fcf1ee5dd26b73ef31ae3ca2ffca5c1383a88ff1a','supplied_name':'THRIVE-Wellness-Marketing-Management-Pack.zip'})
  self.assertEqual(len(self.role['source_files']),23);self.assertEqual(len({r['upstream_path'] for r in self.role['source_files']}),23);self.assertEqual(len({r['packaged_path'] for r in self.role['source_files']}),23)
  for r in self.role['source_files']:
   p=PKG/r['packaged_path'];self.assertEqual(p.stat().st_size,r['bytes']);self.assertEqual(sha(p),r['source_sha256']);self.assertRegex(r['upstream_sha256'],r'^[0-9a-f]{64}$');self.assertTrue(r['transformation'])
 def test_exact_package_inventory_and_dual_ledgers(self):
  files={p.relative_to(PKG).as_posix():p for p in PKG.rglob('*') if p.is_file()};self.assertEqual(len(files),26)
  published=ledger(PKG/'PACKAGE-CHECKSUMS.sha256');self.assertEqual(len(published),25);self.assertEqual(set(published),set(files)-{'PACKAGE-CHECKSUMS.sha256'})
  for n,d in published.items():self.assertEqual(sha(files[n]),d)
  upstream=ledger(PKG/'UPSTREAM-SHA256SUMS.txt');self.assertEqual(len(upstream),22)
  records={r['upstream_path']:r for r in self.role['source_files'] if r['upstream_path']!='SHA256SUMS.txt'};self.assertEqual(set(upstream),set(records))
  for n,d in upstream.items():self.assertEqual(records[n]['upstream_sha256'],d)
 def test_program_embeds_all_components_byte_for_byte(self):
  pat=re.compile(r'<!-- BEGIN COMPONENT: ([^|]+) \| SHA256: ([0-9a-f]{64}) -->\n(.*?)\n<!-- END COMPONENT: \1 -->',re.S);blocks=pat.findall(self.program);self.assertEqual(len(blocks),17)
  for rel,d,body in blocks:
   p=PKG/SP/rel.strip();self.assertTrue(p.is_file());self.assertEqual(sha(p),d);self.assertEqual(body.strip(),p.read_text().strip())
 def test_exact_activation_card_is_in_controlling_program(self):
  for phrase in ('exact combined **THRIVE Activation Card**','target Hermes environment and exact complete-program SHA-256','operator, organization/brand, active professional hat','17 component paths and verified hashes','24 powers `Available Inactive`','allowed and prohibited data, sources, wellness/health claims','supported, unsupported, blocked, or uncertain target capabilities','exact rollback, quarantine, resume, repair, export, delete, and THRIVE-only uninstall scope','Stop after displaying the card. Create no state','INSTALL THRIVE AFTER S0 — USE EXACT VERIFIED COMPONENT HASHES AND KEEP ALL POWERS AND AGENTS INACTIVE.','general request to “publish and install” is never approval','invalidates approval and requires a new card'):
   self.assertIn(phrase,self.program)
 def test_read_first_download_and_institutional_boundaries(self):
  text=(PKG/'00-READ-FIRST.md').read_text()
  for phrase in ('Downloading, selecting, opening, or unzipping this package does not install or activate anything','INSPECT THRIVE INSTALLER ONLY — CREATE NO STATE.','specified—not pre-passed','Private-workspace approval does not authorize organizational deployment','Human approval does not convert a categorically prohibited function into an allowed one'):
   self.assertIn(phrase,text)
 def test_manifest_counts_and_default_states(self):
  expected={'installation_status':'not_installed','install_on_download':False,'standalone_wellness_business_lane':True,'optional_superpowers_total':24,'optional_superpowers_active_after_install':0,'workflows_total':24,'templates_total':30,'schemas_total':18,'suggested_agents_total':10,'suggested_agents_active_after_install':0,'fixtures_adapters_total':10,'records_total':18,'person_level_data_allowed':False,'live_person_contact':False,'official_system_writes':False,'health_claim_release_authority':False}
  for k,v in expected.items():self.assertEqual(self.role[k],v,k)
  self.assertEqual(self.role['runtime_criteria'],{'publication_status':'specified_not_prepassed','s1':40,'s2':120,'total':160})
 def test_source_inventories_are_exact(self):
  tests=(PKG/SP/'tests/01-THRIVE-Release-and-Runtime-Tests.md').read_text();workflow=(PKG/SP/'workflows/01-THRIVE-Runnable-Workflows.md').read_text();templates=(PKG/SP/'templates/01-THRIVE-Functional-Templates.md').read_text();schemas=(PKG/SP/'workflows/03-THRIVE-Schemas-and-Agents.md').read_text()
  self.assertEqual(len(set(re.findall(r'RA-(?:[A-R]\d{2}|INT\d{2})',tests))),160);self.assertEqual(len(set(re.findall(r'WF-(\d{2})',workflow))),24);self.assertEqual(len(set(re.findall(r'TPL-(\d{2})',templates))),30);self.assertEqual(len(set(re.findall(r'AGT-(\d{2})',schemas))),10);self.assertEqual(len(re.findall(r'^### `https://nurse-ai-os\.local/schemas/wellness_thrive/',schemas,re.M)),18)
 def test_page_states_boundaries_without_overclaiming(self):
  for phrase in ('Standalone wellness-business lane','Downloading changes nothing','No clinical advice, manufactured evidence, sensitive targeting, or consequential action','The 160 criteria are specified, not pre-passed','Institutional use is a separate state','Hermes Agent is an external open-source runtime'):
   self.assertIn(phrase,self.page)
  for forbidden in ('clinically validated','hipaa compliant','guaranteed revenue','is institution-approved'):
   self.assertNotIn(forbidden,self.page.lower())
 def test_privacy_enhanced_videos_and_home_order(self):
  self.assertIn('youtube-nocookie.com/embed/Ndk5C78e7jQ',self.page);self.assertIn('youtube-nocookie.com/embed/xdlnYkMJQl4',self.admin)
  self.assertIn('youtube-nocookie.com/embed/Ndk5C78e7jQ',self.home);self.assertIn('youtube-nocookie.com/embed/xdlnYkMJQl4',self.home)
  self.assertNotIn('youtube.com/shorts/',self.page+self.admin+self.home)
  order=[self.home.index(f'class="{x}"') for x in ('home-resident-video','home-rt-video','home-discover-video','home-thrive-video','home-admin-lane')];self.assertEqual(order,sorted(order));self.assertLess(order[-1],self.home.index('<!-- ============ ROLE CARDS'))
 def test_steward_video_does_not_change_preview_state(self):
  for phrase in ('vision narrative, not evidence','runtime not implemented','Complete AI OS claim paused','institutional use not authorized','This is a specification, not software'):
   self.assertIn(phrase,self.admin)
  self.assertNotIn('Install safely',self.admin);self.assertNotIn('Activation Card',self.admin)
 def test_no_cross_population_registration_or_shared_state(self):
  setup=(ROOT/'setup-helper/setup-helper-model.mjs').read_text();post=(ROOT/'post-setup/downloads/manifest.json').read_text();self.assertNotIn('wellness_services_marketing_management',setup+post);self.assertNotIn('wellness_thrive',setup+post)
  for key in ('nursing_population_state_shared','medical_resident_population_state_shared','respiratory_care_population_state_shared','hospital_administration_population_state_shared','healthcare_research_population_state_shared'):self.assertFalse(self.role[key])
 def test_public_manifest_and_zip_checksum(self):
  public=json.loads((DL/'manifest.json').read_text());r=public['packages'][0];self.assertEqual(public['installation_status'],'not_installed');self.assertEqual(r['sha256'],sha(ZIP));self.assertEqual(r['bytes'],ZIP.stat().st_size);self.assertEqual((DL/'CHECKSUMS.sha256').read_text(),f'{sha(ZIP)}  {ZIP.name}\n')
 def test_zip_is_safe_exact_and_byte_identical(self):
  package={p.relative_to(PKG).as_posix():p for p in PKG.rglob('*') if p.is_file()}
  with zipfile.ZipFile(ZIP) as z:
   self.assertIsNone(z.testzip());self.assertEqual(len(z.infolist()),26);self.assertEqual({i.filename for i in z.infolist()},{PREFIX+n for n in package})
   for i in z.infolist():
    self.assertEqual(i.date_time,(2026,7,17,0,0,0));self.assertEqual(i.external_attr>>16,0o100644);name=i.filename[len(PREFIX):];self.assertEqual(z.read(i),package[name].read_bytes())
 def test_builder_reproduces_committed_bytes(self):
  before=sha(ZIP);module=runpy.run_path(str(ROOT/'scripts/build-wellness-marketing-thrive.py'),run_name='thrive_test');module['build']();self.assertEqual(sha(ZIP),before)
 def test_accessibility_sitemap_and_route(self):
  for page in (self.page,self.admin,self.home):self.assertIn('class="skip-link" href="#main-content"',page);self.assertIn('<main id="main-content" tabindex="-1">',page)
  self.assertIn('@media (prefers-reduced-motion: reduce)',(ROOT/'assets/nurse-ai.css').read_text());self.assertIn('https://nurse-ai-os.org/wellness-services-marketing-managers/',(ROOT/'sitemap.xml').read_text())
 def test_builder_pins_current_role_manifest(self):
  self.assertIn(f"'ROLE-PACK.json':'{sha(PKG/'ROLE-PACK.json')}'",self.builder);self.assertIn(f"'00-READ-FIRST.md':'{sha(PKG/'00-READ-FIRST.md')}'",self.builder)
if __name__=='__main__':unittest.main(verbosity=2)
