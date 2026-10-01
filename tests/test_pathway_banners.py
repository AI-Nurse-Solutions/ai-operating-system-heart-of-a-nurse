"""Local, noncredentialing near-top banner contracts."""
from pathlib import Path
from html.parser import HTMLParser
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Images(HTMLParser):
    def __init__(self): super().__init__(); self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img': self.images.append(dict(attrs))
class PathwayBannerTests(unittest.TestCase):
    def test_both_banners_are_local_sized_and_accessible(self):
        for lane in ['ally','physician']:
            text=(ROOT/(lane+'.html')).read_text(); parser=Images();parser.feed(text)
            found=[im for im in parser.images if im.get('src')=='assets/img/'+lane+'-welcome-banner.webp']
            self.assertEqual(len(found),1);im=found[0]
            self.assertGreater(len(im['alt']),40)
            self.assertEqual((im['width'],im['height']),('1024','427'))
            self.assertEqual(im['fetchpriority'],'high');self.assertEqual(im['loading'],'eager')
            raw=(ROOT/im['src']).read_bytes()
            self.assertEqual(raw[:4],b'RIFF');self.assertEqual(raw[8:12],b'WEBP');self.assertLess(len(raw),100000)
    def test_banner_is_after_heading_before_intro_and_cta(self):
        for lane in ['ally','physician']:
            s=(ROOT/(lane+'.html')).read_text()
            self.assertLess(s.index('</h1>'),s.index('id="'+lane+'-banner"'))
            self.assertLess(s.index('id="'+lane+'-banner"'),s.index('class="button" href="'+lane+'-soul-quiz.html">'))
            self.assertEqual(s.count('class="pathway-banner"'),1)
            self.assertIn('AI-generated illustration',s)
    def test_banner_asset_and_suite_changes_trigger_ci(self):
        s=(ROOT/'.github/workflows/website-alignment.yml').read_text()
        for token in ['assets/img/ally-welcome-banner.webp','assets/img/physician-welcome-banner.webp','tests/test_pathway_banners.py']:
            self.assertEqual(s.count('"'+token+'"'),2)
if __name__=='__main__':unittest.main()
