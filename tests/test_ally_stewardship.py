"""Public ally pathway contracts; no clinical or runtime validation claims."""
import unittest, zipfile
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
PAGES = ['ally.html', 'ally-soul-quiz.html', 'ally-setup.html', 'ally-stewardship.html']
MEMBERS = ['AGENT-COMPANION-GUIDE.md','HANDOFF-PROMPT.txt','README.md','SETUP-CHEATSHEET.md','STEWARDSHIP-CHARTER.md','dashboard.html','mission-control.html','stewardship-ceremony.html']
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=[]
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if 'id' in data: self.ids.append(data['id'])
        if tag=='a' and 'href' in data: self.links.append(data['href'])
class AllyStewardshipTests(unittest.TestCase):
    def test_local_links_and_unique_ids(self):
        for path in [ROOT/p for p in PAGES]+list((ROOT/'ally-starter').glob('*.html')):
            parser=Links(); parser.feed(path.read_text())
            self.assertEqual(len(parser.ids),len(set(parser.ids)))
            for href in parser.links:
                if href.startswith(('http:','https:','mailto:')): continue
                relative,_,anchor=href.partition('#'); target=path.parent/relative if relative else path
                self.assertTrue(target.is_file(),(path,href))
                if anchor:
                    other=Links();other.feed(target.read_text());self.assertIn(anchor,other.ids)
    def test_archive_exact_inventory_and_source_bytes(self):
        with zipfile.ZipFile(ROOT/'downloads/ally-starter-package.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.namelist(),['ally-starter/'+n for n in MEMBERS])
            for n in MEMBERS:self.assertEqual(z.read('ally-starter/'+n),(ROOT/'ally-starter'/n).read_bytes())
    def test_download_source_parity(self):
        for published,source in [('ally-setup-cheatsheet.md','SETUP-CHEATSHEET.md'),('ally-stewardship-charter.md','STEWARDSHIP-CHARTER.md'),('ally-agent-companion-guide.md','AGENT-COMPANION-GUIDE.md')]:
            self.assertEqual((ROOT/'downloads'/published).read_bytes(),(ROOT/'ally-starter'/source).read_bytes())
    def test_mission_and_credential_boundaries(self):
        charter=(ROOT/'ally-starter/STEWARDSHIP-CHARTER.md').read_text()
        for phrase in ['scale good','artificial general intelligence','not a replacement','voluntary','not runtime enforcement','public sources and synthetic examples','professional certification']:
            self.assertIn(phrase,charter)
        for name in PAGES:
            text=(ROOT/name).read_text()
            self.assertIn('ally-stewardship.html',text)
            self.assertNotIn('localStorage',text);self.assertNotIn('sessionStorage',text)
    def test_certificate_is_commemorative_and_literal_text(self):
        text=(ROOT/'ally-stewardship.html').read_text()
        for phrase in ['Commemorative only','not a professional credential','self-declared','No institutional signature','identity','membership','clinical authority','reportValidity()','textContent=','cert.hidden=true']:
            self.assertIn(phrase,text)
        self.assertIn('id="pledge" type="checkbox" required',text)
        self.assertIn('id="certificate" class="certificate" hidden',text)
    def test_quiz_preserves_self_description_and_review_only_posture(self):
        text=(ROOT/'ally-soul-quiz.html').read_text()
        for phrase in ['Credentials verified: false','A0 / no action','No management authority is claimed','No business ownership is claimed','Charter acceptance is voluntary and has not been recorded','service','partnership']:
            self.assertIn(phrase,text)
    def test_pathway_pages_are_in_the_sitemap(self):
        import xml.etree.ElementTree as ET
        tree=ET.parse(ROOT/'sitemap.xml')
        routes=[node.text for node in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        for page in PAGES:self.assertEqual(routes.count('https://nurse-ai-os.org/'+page),1)
    def test_offline_tools_have_no_network_or_automatic_storage(self):
        for name in ['dashboard.html','mission-control.html','stewardship-ceremony.html']:
            text=(ROOT/'ally-starter'/name).read_text()
            for forbidden in ['fetch(', 'XMLHttpRequest','localStorage','sessionStorage','<script src=', 'https://']:
                self.assertNotIn(forbidden,text)
    def test_scoped_homepage_preservation(self):
        import hashlib, re
        # Frozen origin/main homepage baseline; no git executable or mutable HEAD needed.
        current=(ROOT/'index.html').read_text()
        stripped=re.sub(r'<!-- ALLY PATHWAY START -->.*?<!-- ALLY PATHWAY END -->\n\n','',current,flags=re.S)
        self.assertEqual(hashlib.sha256(stripped.encode()).hexdigest(),"de7c4cac84ed9abe222e9e2833a79634ce6f37a8eae06e72d19a8f19016d4adf")
        self.assertIn('id="ally-stewardship-pathway"',current)
    def test_ci_coverage(self):
        text=(ROOT/'.github/workflows/website-alignment.yml').read_text()
        for token in ['tests/test_ally_stewardship.py','ally-starter/**','downloads/ally-*']:
            self.assertEqual(text.count('"'+token+'"'),2)
        self.assertIn('--label ALLY_PATHWAY',text)
    def test_ally_specific_welcome_and_safety(self):
        landing=(ROOT/'ally.html').read_text()
        for phrase in ['allied health','purpose over hype','more capable','data control','not proof of ethical conduct','open to everyone']:
            self.assertIn(phrase,landing)
        for path in [ROOT/p for p in PAGES]+list((ROOT/'ally-starter').glob('*')):
            text=path.read_text()
            self.assertNotIn('physician',text.lower())
            self.assertIn('qualified human review',text)
            self.assertIn('not automatic sovereignty',text)
    def test_quiz_acknowledgments_and_plain_language(self):
        text=(ROOT/'ally-soul-quiz.html').read_text()
        for token in ['id="credentials" type="checkbox" required','id="responsible" type="checkbox" required','id="safe" type="checkbox" required','not proof of ethical conduct','not a test to pass']:
            self.assertIn(token,text)
        self.assertNotIn('score=',text)
    def test_handoff_preserves_state_and_exact_scope(self):
        text=(ROOT/'ally-starter/HANDOFF-PROMPT.txt').read_text()
        for token in ['untrusted reference material','not executable instructions','Do not run installers','replace my existing SOUL or configuration','Do not infer business ownership or management authority','affected files, data destinations, costs, permissions, tests, and rollback','Stop for my explicit approval before making any changes','not installation or action permission']:
            self.assertIn(token,text)
    def test_canonical_dates_and_generic_package(self):
        import xml.etree.ElementTree as ET
        tree=ET.parse(ROOT/'sitemap.xml');ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for page in PAGES:
            self.assertIn('rel="canonical" href="https://nurse-ai-os.org/'+page+'"',(ROOT/page).read_text())
            nodes=[n for n in tree.findall('s:url',ns) if n.find('s:loc',ns).text=='https://nurse-ai-os.org/'+page]
            self.assertEqual(nodes[0].find('s:lastmod',ns).text,'2026-09-30')
        readme=(ROOT/'ally-starter/README.md').read_text()
        for token in ['does NOT contain your personalized quiz result','unsaved notes are lost','not Hermes native dashboard','No automatic acceptance storage']:
            self.assertIn(token,readme)
if __name__=='__main__': unittest.main()
