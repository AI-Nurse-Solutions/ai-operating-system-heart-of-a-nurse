"""Educational media is opt-in, noncredentialing and not an installation attestation."""
import unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
VIDEOS=[('6HU_HOOPS9c','https://youtu.be/6HU_HOOPS9c'),('ZDnmq7MB14E','https://youtube.com/shorts/ZDnmq7MB14E?si=CGGGf0d6G86Y28Y0'),('InXb8EN9Hcs','https://youtube.com/shorts/InXb8EN9Hcs?si=N9SRW4gG1yuNYCye'),('W1eOXb-l2EI','https://youtu.be/W1eOXb-l2EI?si=hHzXVvy47_sVtZRi'),('0MDiFVbgR6U','https://youtu.be/0MDiFVbgR6U?si=f_GE2CHb9K-7Uw-1')]
class Elements(HTMLParser):
 def __init__(self):super().__init__();self.buttons=[];self.links=[];self.frames=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='button' and 'data-video' in d:self.buttons.append(d)
  if tag=='a':self.links.append(d)
  if tag=='iframe':self.frames.append(d)
class PhysicianVideoTests(unittest.TestCase):
 def test_exact_media_and_direct_fallback_links(self):
  p=Elements();p.feed((ROOT/'physician.html').read_text())
  self.assertEqual([b['data-video'] for b in p.buttons],[v[0] for v in VIDEOS])
  for _,url in VIDEOS:
   self.assertTrue(any(l.get('href')==url and l.get('rel')=='noopener noreferrer' for l in p.links))
 def test_no_youtube_player_before_explicit_click(self):
  text=(ROOT/'physician.html').read_text();p=Elements();p.feed(text)
  self.assertEqual(p.frames,[])
  for token in ['www.youtube-nocookie.com/embed/','addEventListener(\'click\'','strict-origin-when-cross-origin','No autoplay','loading a player contacts YouTube']:
   self.assertIn(token,text)
 def test_illustrations_do_not_attest_runtime_controls(self):
  text=(ROOT/'physician.html').read_text()
  for token in ['illustrative and educational','not credential verification','Local Hermes does not mean offline inference','A workspace folder is not a sandbox','SOUL readback is not enforced governance','file:// does not prove network isolation','not a current hardware specification','physician-setup.html','Nurse practitioners are a distinct profession']:
   self.assertIn(token,text)
if __name__=='__main__':unittest.main()
