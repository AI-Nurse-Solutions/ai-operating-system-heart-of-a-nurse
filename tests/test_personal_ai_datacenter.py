import json
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "personal-ai-datacenter" / "index.html"
WEB_CARD = ROOT / "robert-domondon" / "index.html"
RESOURCES = ROOT / "resources.html"
SITEMAP = ROOT / "sitemap.xml"
PUBLIC_URL = "https://nurse-ai-os.org/personal-ai-datacenter/"
IMAGE_DIR = ROOT / "assets" / "img" / "personal-ai-datacenter"
EXPECTED_IMAGES = {
    "2x-rtx5090-open.webp",
    "2x-rtxpro6000-enclosed.webp",
    "2x-rtxpro6000-open.webp",
    "4x-rtx5090-enclosed.webp",
    "4x-rtxpro6000-enclosed.webp",
    "4x-rtxpro6000-open.webp",
    "8x-rtx5090-open.webp",
    "8x-rtx5090-rack.webp",
}
EXPECTED_BUILDS = {
    "dual-rtx5090",
    "dual-rtxpro6000",
    "quad-rtx5090",
    "quad-rtxpro6000",
    "eight-rtx5090",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self.images = []
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
        if tag == "img":
            self.images.append(attr_map)
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


class PersonalAIDatacenterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.webcard = WEB_CARD.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")
        cls.parser = PageParser()
        cls.parser.feed(cls.html)

    def test_page_structure_and_metadata(self):
        self.assertEqual(self.parser.main_count, 1)
        self.assertEqual(self.parser.h1_count, 1)
        self.assertIn("main-content", self.parser.ids)
        self.assertIn('class="skip-link"', self.html)
        metadata = json.loads("".join(self.parser.json_ld_text))
        self.assertEqual(metadata["@type"], "CollectionPage")
        self.assertEqual(metadata["url"], PUBLIC_URL)

    def test_all_five_builds_and_eight_drawings_are_present(self):
        self.assertTrue(EXPECTED_BUILDS.issubset(self.parser.ids))
        page_images = {
            Path(image.get("src", "")).name
            for image in self.parser.images
            if "personal-ai-datacenter" in image.get("src", "")
        }
        self.assertEqual(page_images, EXPECTED_IMAGES)
        for filename in EXPECTED_IMAGES:
            path = IMAGE_DIR / filename
            self.assertTrue(path.is_file(), filename)
            self.assertGreater(path.stat().st_size, 50_000, filename)
        for image in self.parser.images:
            if "personal-ai-datacenter" in image.get("src", ""):
                self.assertTrue(image.get("alt", "").strip())
                self.assertTrue(image.get("width"))
                self.assertTrue(image.get("height"))

    def test_specifications_are_marked_as_concepts_not_build_instructions(self):
        for phrase in (
            "Draft specifications",
            "Not a validated BOM, build guide, or purchase recommendation",
            "Do not build from this page alone",
            "not proof that reference cards fit or operate safely",
            "require professional design",
            "Personal and Community Nurse AI OS remain no-PHI and nonclinical",
        ):
            self.assertIn(phrase, self.html)

    def test_original_unsupported_marketing_claims_are_not_republished(self):
        for phrase in (
            "Fable 5",
            "No one can switch you off",
            "Inference becomes free",
            "unlimited tokens",
            "Your business is their training data",
        ):
            self.assertNotIn(phrase, self.html)

    def test_gpu_memory_and_bandwidth_are_qualified(self):
        self.assertIn("not a single pooled memory space", self.html)
        self.assertIn("32 GB GDDR7 and 1,792 GB/s", self.html)
        self.assertIn("96 GB GDDR7 ECC", self.html)
        self.assertIn("Multi-GPU model support", self.html)
        self.assertIn("Manufacturer references", self.html)

    def test_webcard_resource_hub_and_sitemap_link_the_gallery(self):
        self.assertIn(f'href="{PUBLIC_URL}"', self.webcard)
        self.assertIn("Personal AI Datacenter Designs", self.webcard)
        self.assertIn('href="personal-ai-datacenter/"', self.resources)
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
