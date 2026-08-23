import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_CARD = ROOT / "robert-domondon" / "index.html"
LOCAL_SOVEREIGN_URL = (
    "https://nurse-ai-os-local-sovereign.robert981594.chatgpt.site/"
    "local-sovereign-systems"
)


class WebCardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self._current_anchor = None
        self._json_ld = False
        self.json_ld_text = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if tag == "a":
            self._current_anchor = {**attr_map, "text": []}
            self.anchors.append(self._current_anchor)
        if tag == "script" and attr_map.get("type") == "application/ld+json":
            self._json_ld = True

    def handle_endtag(self, tag):
        if tag == "a":
            self._current_anchor = None
        if tag == "script" and self._json_ld:
            self._json_ld = False

    def handle_data(self, data):
        if self._current_anchor is not None:
            self._current_anchor["text"].append(data)
        if self._json_ld:
            self.json_ld_text.append(data)


class RobertWebCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = WEB_CARD.read_text(encoding="utf-8")
        cls.parser = WebCardParser()
        cls.parser.feed(cls.html)

    def test_local_sovereign_link_is_visible_and_safe(self):
        matches = [
            anchor
            for anchor in self.parser.anchors
            if anchor.get("href") == LOCAL_SOVEREIGN_URL
        ]
        self.assertEqual(len(matches), 1)
        anchor = matches[0]
        self.assertEqual(anchor.get("target"), "_blank")
        self.assertEqual(anchor.get("rel"), "noopener noreferrer")
        self.assertIn("Local & Sovereign Systems", "".join(anchor["text"]))

    def test_local_sovereign_link_is_in_profile_metadata(self):
        metadata = json.loads("".join(self.parser.json_ld_text))
        self.assertIn(LOCAL_SOVEREIGN_URL, metadata["mainEntity"]["sameAs"])


if __name__ == "__main__":
    unittest.main()
