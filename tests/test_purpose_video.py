"""Purpose keynote is opt-in and precedes the main SOUL quiz invitation."""
from pathlib import Path
from html.parser import HTMLParser
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Elements(HTMLParser):
    def __init__(self):super().__init__();self.buttons=[];self.links=[];self.frames=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='button':self.buttons.append(d)
        if tag=='a':self.links.append(d)
        if tag=='iframe':self.frames.append(d)
class PurposeVideoTests(unittest.TestCase):
    def test_keynote_is_featured_before_primary_quiz_on_both_pages(self):
        for lane in ['ally','physician']:
            s=(ROOT/(lane+'.html')).read_text();p=Elements();p.feed(s)
            self.assertEqual(len([b for b in p.buttons if b.get('data-video')=='6HU_HOOPS9c']),1)
            self.assertLess(s.index('id="why-nurse-ai-os"'),s.index('class="button" href="'+lane+'-soul-quiz.html"'))
            self.assertIn('Before you answer the SOUL quiz',s)
            self.assertTrue(any(a.get('href')=='https://youtu.be/6HU_HOOPS9c' and a.get('rel')=='noopener noreferrer' for a in p.links))
    def test_privacy_and_purpose_vs_installed_claims(self):
        for lane in ['ally','physician']:
            s=(ROOT/(lane+'.html')).read_text();p=Elements();p.feed(s)
            self.assertEqual(p.frames,[])
            for term in ['No autoplay','not an automatically installed program','not guarantees','separate approval','Setup, costs, permissions','not technical enforcement','family information','synthetic examples']:
                self.assertIn(term,s)
            self.assertIn(lane+'-setup.html',s)
    def test_new_suite_triggers_ci(self):
        s=(ROOT/'.github/workflows/website-alignment.yml').read_text()
        self.assertEqual(s.count('"tests/test_purpose_video.py"'),2)
if __name__=='__main__':unittest.main()
