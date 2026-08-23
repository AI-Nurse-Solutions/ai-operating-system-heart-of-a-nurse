import json
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "local-sovereign-systems" / "index.html"
WEB_CARD = ROOT / "robert-domondon" / "index.html"
RESOURCES = ROOT / "resources.html"
SITEMAP = ROOT / "sitemap.xml"
PUBLIC_URL = "https://nurse-ai-os.org/local-sovereign-systems/"
SOURCE_URLS = {
    "https://www.iea.org/reports/energy-and-ai/executive-summary",
    "https://www.eia.gov/todayinenergy/detail.php?id=66744",
    "https://blog.cloudflare.com/18-november-2025-outage/",
    "https://www.eesi.org/articles/view/data-centers-and-water-consumption",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self.ids = set()
        self.main_count = 0
        self.h1_count = 0
        self._json_ld = False
        self.json_ld_text = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if attr_map.get("id"):
            self.ids.add(attr_map["id"])
        if tag == "a":
            self.anchors.append(attr_map)
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.h1_count += 1
        if tag == "script" and attr_map.get("type") == "application/ld+json":
            self._json_ld = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._json_ld = False

    def handle_data(self, data):
        if self._json_ld:
            self.json_ld_text.append(data)


class LocalSovereignSystemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.webcard = WEB_CARD.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")
        cls.parser = PageParser()
        cls.parser.feed(cls.html)

    def test_public_page_and_accessibility_structure_exist(self):
        self.assertTrue(PAGE.is_file())
        self.assertEqual(self.parser.main_count, 1)
        self.assertEqual(self.parser.h1_count, 1)
        self.assertIn("main-content", self.parser.ids)
        self.assertIn('class="skip-link"', self.html)
        self.assertIn(PUBLIC_URL, self.html)

    def test_public_status_and_healthcare_boundaries_are_adjacent(self):
        required = (
            "Public educational guide · No login · No PHI",
            "Community and Personal Edition remain no-PHI and nonclinical",
            "Local deployment alone does not establish HIPAA compliance",
            "local AI is not an emergency or clinical continuity system",
            "It does not inherit licensure",
        )
        for phrase in required:
            self.assertIn(phrase, self.html)

    def test_environmental_claims_include_context_and_caveats(self):
        for phrase in (
            "415 → 945 TWh",
            "local is not automatically greener",
            "Hyperscale systems may be more efficient per request",
            "should not be converted into a universal “water per AI prompt” claim",
        ):
            self.assertIn(phrase, self.html)

    def test_source_ledger_and_structured_metadata_agree(self):
        hrefs = {anchor.get("href") for anchor in self.parser.anchors}
        self.assertTrue(SOURCE_URLS.issubset(hrefs))
        metadata = json.loads("".join(self.parser.json_ld_text))
        self.assertEqual(metadata["@type"], "TechArticle")
        self.assertEqual(metadata["url"], PUBLIC_URL)
        self.assertEqual(set(metadata["citation"]), SOURCE_URLS)

    def test_webcard_points_to_public_route_without_login_language(self):
        self.assertIn(f'href="{PUBLIC_URL}"', self.webcard)
        self.assertIn("Local &amp; Sovereign Systems", self.webcard)
        self.assertNotIn("ChatGPT sign-in", self.webcard)
        self.assertNotIn("chatgpt.site", self.webcard)

    def test_resource_hub_and_sitemap_discover_the_page(self):
        self.assertIn('href="local-sovereign-systems/"', self.resources)
        root = ET.parse(SITEMAP).getroot()
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = set()
        for node in root.findall("s:url", namespace):
            location = node.find("s:loc", namespace)
            if location is not None and location.text:
                urls.add(location.text)
        self.assertIn(PUBLIC_URL, urls)

    def test_local_links_resolve(self):
        for anchor in self.parser.anchors:
            href = anchor.get("href", "")
            if not href or href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (PAGE.parent / href.split("#", 1)[0]).resolve()
            if href.endswith("/"):
                target = target / "index.html"
            self.assertTrue(target.exists(), f"missing local target: {href}")


if __name__ == "__main__":
    unittest.main()
