import re
import unittest
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import DictionaryObject


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
KEYS = ("en",) + LOCALES
SUFFIX = {"en": "", **{locale: f"-{locale}" for locale in LOCALES}}
TITLES = {
    "en": "Nurse AI OS™ Media Kit",
    "es": "Nurse AI OS — Dossier de prensa",
    "tl": "Nurse AI OS — Media brief sa Tagalog",
    "zh": "Nurse AI OS — 媒体资料包",
    "ar": "Nurse AI OS — الملف الإعلامي",
    "vi": "Nurse AI OS — Tóm tắt truyền thông tiếng Việt",
    "ru": "Nurse AI OS — Пресс-кит",
    "hi": "Nurse AI OS — मीडिया किट",
    "fr": "Nurse AI OS — Dossier de presse",
}
DISCLOSURES = {
    "es": "fuente canónica", "tl": "canonical source", "zh": "规范来源",
    "ar": "المصدر المرجعي", "vi": "nguồn chuẩn", "ru": "каноническим источником",
    "hi": "canonical source", "fr": "source canonique",
}
POSTURES = {
    "en": "shadow/observe-only", "es": "sombra/observación",
    "tl": "shadow/observe-only", "zh": "shadow/observe-only",
    "ar": "shadow/observe-only", "vi": "shadow/observe-only",
    "ru": "shadow/observe-only", "hi": "shadow/observe-only",
    "fr": "shadow/observe-only",
}


def source_path(key):
    return ROOT / "assets" / f"nurse-ai-os-media-packet{SUFFIX[key]}.md"


def pdf_path(key):
    return ROOT / "assets" / f"nurse-ai-os-media-packet{SUFFIX[key]}.pdf"


def walk_pdf_objects(value, seen=None):
    if seen is None:
        seen = set()
    try:
        obj = value.get_object()
    except Exception:
        obj = value
    marker = id(obj)
    if marker in seen:
        return
    seen.add(marker)
    yield obj
    if isinstance(obj, DictionaryObject):
        for child in obj.values():
            yield from walk_pdf_objects(child, seen)
    elif isinstance(obj, (list, tuple)):
        for child in obj:
            yield from walk_pdf_objects(child, seen)


class MediaPacketReleaseTests(unittest.TestCase):
    def test_all_language_source_pdf_pairs_exist_and_have_current_claims(self):
        for key in KEYS:
            source = source_path(key)
            pdf = pdf_path(key)
            self.assertTrue(source.is_file(), source)
            self.assertTrue(pdf.is_file(), pdf)
            text = source.read_text(encoding="utf-8")
            for token in ("ChatGPT", "Claude", "Hermes", "Florence-X", "$10", "$29.90", "2026"):
                self.assertIn(token, text, f"{key}: {token}")
            self.assertIn(POSTURES[key], text, key)
            self.assertGreater(len(text), 2000, key)
            if key != "en":
                self.assertIn(DISCLOSURES[key], text, key)

    def test_canonical_source_carries_exact_product_pricing_and_authority_boundaries(self):
        text = source_path("en").read_text(encoding="utf-8")
        required = (
            "browser-first kit", "No separate application or Hermes installation is required to begin",
            "$0, free forever", "$10 one time", "$29.90 per year",
            "September 15–17, 2026", "December 31, 2026",
            "That date does not end the free core", "shadow/observe-only",
            "does not guarantee that ChatGPT, Claude, Hermes, or another host will enforce every instruction identically",
            "or a finished standalone operating system", "not a claim of HIPAA certification",
            "do not prove clinical effectiveness, regulatory compliance, institutional authorization, or patient outcomes",
        )
        for phrase in required:
            self.assertIn(phrase.casefold(), text.casefold(), phrase)
        retired = (
            "free for nurses and nursing students during the founding year",
            "five governed self-install Hermes build kits",
            "the orchestration control plane for governed AI-agent workforces",
            "the risk-classification and gating layer every task runs under",
        )
        for phrase in retired:
            self.assertNotIn(phrase.casefold(), text.casefold(), phrase)

    def test_pdf_metadata_text_links_pages_and_active_content(self):
        for key in KEYS:
            reader = PdfReader(pdf_path(key))
            metadata = reader.metadata
            self.assertEqual(metadata.title, TITLES[key], key)
            self.assertEqual(metadata.author, "Robert Domondon", key)
            self.assertIsNone(metadata.get("/CreationDate"), key)
            self.assertIsNone(metadata.get("/ModDate"), key)
            self.assertGreaterEqual(len(reader.pages), 2, key)
            self.assertLessEqual(len(reader.pages), 15, key)
            extracted = " ".join((page.extract_text() or "") for page in reader.pages)
            self.assertIn("Nurse AI OS", extracted, key)
            self.assertIn("ChatGPT", extracted, key)
            self.assertIn("Claude", extracted, key)
            self.assertIn("Hermes", extracted, key)
            self.assertGreater(len(extracted), 2500, key)
            links = 0
            for page in reader.pages:
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                self.assertAlmostEqual(width, 612, delta=1, msg=key)
                self.assertAlmostEqual(height, 792, delta=1, msg=key)
                for annot_ref in page.get("/Annots", []):
                    annot = annot_ref.get_object()
                    action = annot.get("/A")
                    if action and action.get("/S") == "/URI":
                        links += 1
                for font_ref in page["/Resources"].get("/Font", {}).values():
                    font = font_ref.get_object()
                    subtype = font.get("/Subtype")
                    if subtype == "/Type3":
                        self.assertTrue(font.get("/CharProcs"), f"{key}: Type3 font lacks glyph programs")
                        continue
                    candidate = font
                    if subtype == "/Type0":
                        descendants = font.get("/DescendantFonts", [])
                        self.assertTrue(descendants, f"{key}: Type0 font lacks descendants")
                        candidate = descendants[0].get_object()
                    descriptor_ref = candidate.get("/FontDescriptor")
                    descriptor = descriptor_ref.get_object() if descriptor_ref else None
                    self.assertTrue(
                        descriptor and any(descriptor.get(name) is not None for name in ("/FontFile", "/FontFile2", "/FontFile3")),
                        f"{key}: font lacks an embedded program",
                    )
            self.assertGreaterEqual(links, 7, key)
            names = {str(name) for obj in walk_pdf_objects(reader.trailer) if isinstance(obj, DictionaryObject) for name in obj.keys()}
            for forbidden in ("/JavaScript", "/JS", "/Launch", "/EmbeddedFiles", "/OpenAction", "/AcroForm"):
                self.assertNotIn(forbidden, names, f"{key}: {forbidden}")

    def test_media_center_advertises_exact_complete_inventory(self):
        page = (ROOT / "media.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("https://nurse-ai-os.org/media.html"), 1)
        self.assertIn("The English packet is the canonical source", page)
        self.assertIn("have not received professional native-language editorial certification", page)
        for key in KEYS:
            suffix = SUFFIX[key]
            expected_count = 2 if key == "en" else 1
            self.assertEqual(page.count(f'assets/nurse-ai-os-media-packet{suffix}.pdf'), expected_count, key)
            self.assertEqual(page.count(f'assets/nurse-ai-os-media-packet{suffix}.md'), expected_count, key)
        self.assertEqual(page.count('class="nav-cta" href="soul-quiz.html"'), 1)

    def test_every_about_page_has_one_bounded_current_media_card(self):
        expected = {"en": "assets/nurse-ai-os-media-packet.pdf", **{
            locale: f"../assets/nurse-ai-os-media-packet-{locale}.pdf" for locale in LOCALES
        }}
        for key in KEYS:
            path = ROOT / ("about.html" if key == "en" else f"{key}/about.html")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("<!-- ============ MEDIA KIT ============ -->"), 1, key)
            self.assertEqual(text.count(expected[key]), 1, key)
            target = 'href="media.html"' if key == "en" else 'href="../media.html"'
            self.assertEqual(text.count(target), 1, key)

    def test_counter_labels_use_current_media_kit_name(self):
        retired = ("Media packets", "Paquetes de medios", "媒体包（全语言）", "الحزم الإعلامية", "Gói truyền thông", "медиапакеты", "Dossiers médias")
        for key in KEYS:
            path = ROOT / ("index.html" if key == "en" else f"{key}/index.html")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count('id="stat-media"'), 1, key)
            for phrase in retired:
                self.assertNotIn(phrase, text, f"{key}: {phrase}")

    def test_builder_declares_every_media_target_and_canonicalization(self):
        text = (ROOT / "tools" / "build-pdfs.py").read_text(encoding="utf-8")
        for key in ("media", "media-es", "media-tl", "media-zh", "media-ar", "media-vi", "media-ru", "media-hi", "media-fr"):
            self.assertRegex(text, rf'"{re.escape(key)}"\s*:', key)
        for phrase in ("canonicalize_pdf", "writer._info = None", "writer._ID = None", "os.replace(canonical, out)"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
