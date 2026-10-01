"""Public physician pathway contracts; no clinical or runtime validation claims."""
import unittest, zipfile
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
PAGES = ['physician.html', 'physician-soul-quiz.html', 'physician-setup.html', 'physician-stewardship.html']
MEMBERS = ['AGENT-COMPANION-GUIDE.md','HANDOFF-PROMPT.txt','README.md','SETUP-CHEATSHEET.md','STEWARDSHIP-CHARTER.md','dashboard.html','mission-control.html','stewardship-ceremony.html']
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=[]
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if 'id' in data: self.ids.append(data['id'])
        if tag=='a' and 'href' in data: self.links.append(data['href'])
class PhysicianStewardshipTests(unittest.TestCase):
    def test_local_links_and_unique_ids(self):
        for path in [ROOT/p for p in PAGES]+list((ROOT/'physician-starter').glob('*.html')):
            parser=Links(); parser.feed(path.read_text())
            self.assertEqual(len(parser.ids),len(set(parser.ids)))
            for href in parser.links:
                if href.startswith(('http:','https:','mailto:')): continue
                relative,_,anchor=href.partition('#'); target=path.parent/relative if relative else path
                self.assertTrue(target.is_file(),(path,href))
                if anchor:
                    other=Links();other.feed(target.read_text());self.assertIn(anchor,other.ids)
    def test_archive_exact_inventory_and_source_bytes(self):
        with zipfile.ZipFile(ROOT/'downloads/physician-starter-package.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.namelist(),['physician-starter/'+n for n in MEMBERS])
            for n in MEMBERS:self.assertEqual(z.read('physician-starter/'+n),(ROOT/'physician-starter'/n).read_bytes())
    def test_download_source_parity(self):
        for published,source in [('physician-setup-cheatsheet.md','SETUP-CHEATSHEET.md'),('physician-stewardship-charter.md','STEWARDSHIP-CHARTER.md'),('physician-agent-companion-guide.md','AGENT-COMPANION-GUIDE.md')]:
            self.assertEqual((ROOT/'downloads'/published).read_bytes(),(ROOT/'physician-starter'/source).read_bytes())
    def test_mission_and_credential_boundaries(self):
        charter=(ROOT/'physician-starter/STEWARDSHIP-CHARTER.md').read_text()
        for phrase in ['scale good','artificial general intelligence','not a replacement','voluntary','not runtime enforcement','public sources and synthetic examples','professional certification']:
            self.assertIn(phrase,charter)
        for name in PAGES:
            text=(ROOT/name).read_text()
            self.assertIn('physician-stewardship.html',text)
            self.assertNotIn('localStorage',text);self.assertNotIn('sessionStorage',text)
    def test_certificate_is_commemorative_and_literal_text(self):
        text=(ROOT/'physician-stewardship.html').read_text()
        for phrase in ['Commemorative only','not a professional credential','self-declared','No institutional signature','identity','membership','clinical authority','reportValidity()','textContent=','cert.hidden=true']:
            self.assertIn(phrase,text)
        self.assertIn('id="pledge" type="checkbox" required',text)
        self.assertIn('id="certificate" class="certificate" hidden',text)
    def test_quiz_preserves_self_description_and_review_only_posture(self):
        text=(ROOT/'physician-soul-quiz.html').read_text()
        for phrase in ['Credentials verified: false','A0 / no action','No management authority is claimed','No business ownership is claimed','Charter acceptance is voluntary and has not been recorded','service','partnership']:
            self.assertIn(phrase,text)
    def test_pathway_pages_are_in_the_sitemap(self):
        import xml.etree.ElementTree as ET
        tree=ET.parse(ROOT/'sitemap.xml')
        routes=[node.text for node in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        for page in PAGES:self.assertEqual(routes.count('https://nurse-ai-os.org/'+page),1)
    def test_offline_tools_have_no_network_or_automatic_storage(self):
        for name in ['dashboard.html','mission-control.html','stewardship-ceremony.html']:
            text=(ROOT/'physician-starter'/name).read_text()
            for forbidden in ['fetch(', 'XMLHttpRequest','localStorage','sessionStorage','<script src=', 'https://']:
                self.assertNotIn(forbidden,text)
if __name__=='__main__': unittest.main()
