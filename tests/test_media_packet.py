import hashlib
import re
import unittest
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
    from pypdf.generic import DictionaryObject, NameObject
    PYPDF_AVAILABLE = True
except ModuleNotFoundError:  # Other lane workflows do not install media-only dependencies.
    class _MissingPypdf:
        metadata: Any
        pages: Any
        trailer: Any

        def __init__(self, *args, **kwargs):
            raise RuntimeError("pypdf is unavailable")

    PdfReader = DictionaryObject = NameObject = _MissingPypdf
    PYPDF_AVAILABLE = False


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
KEYS = ("en",) + LOCALES
HTML_KEYS = ("ar", "hi")
PDF_KEYS = tuple(key for key in KEYS if key not in HTML_KEYS)
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
DONT_SAY_MARKERS = {
    "en": "do not say", "es": "no diga", "tl": "huwag sabihing",
    "zh": "请勿使用", "ar": "لا تقولوا", "vi": "không nên nói",
    "ru": "не следует говорить", "hi": "न कहें", "fr": "à ne pas dire",
}
OVERCLAIMS = {
    "en": ("safe for phi", "clinically validated", "hipaa-compliant", "institutionally approved"),
    "es": ("seguro para phi", "validado clínicamente"),
    "tl": ("ligtas para sa phi", "clinically validated"),
    "zh": ("对 phi 安全", "临床验证"),
    "ar": ("آمن للـ phi", "تم التحقق سريري"),
    "vi": ("an toàn cho phi", "được xác thực lâm sàng"),
    "ru": ("безопасен для phi", "клинически подтвержд"),
    "hi": ("phi के लिए सुरक्षित", "clinically validated"),
    "fr": ("sans danger pour les phi", "validé cliniquement"),
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


def positive_claim_text(text, marker):
    kept = []
    skipping = False
    for line in text.casefold().splitlines():
        if marker.casefold() in line:
            skipping = True
            continue
        if skipping and line.lstrip().startswith("#"):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept)


def pdf_name_tokens(value):
    names = set()
    for obj in walk_pdf_objects(value):
        if isinstance(obj, NameObject):
            names.add(str(obj))
        elif isinstance(obj, DictionaryObject):
            names.update(str(name) for name in obj.keys())
            names.update(str(child) for child in obj.values() if isinstance(child, NameObject))
    return names


@unittest.skipUnless(PYPDF_AVAILABLE, "requires hash-pinned media PDF dependencies")
class MediaPacketReleaseTests(unittest.TestCase):
    def test_all_language_sources_and_publication_artifacts_have_current_claims(self):
        for key in KEYS:
            source = source_path(key)
            self.assertTrue(source.is_file(), source)
            if key in HTML_KEYS:
                self.assertTrue((ROOT / f"media-{key}.html").is_file())
                self.assertFalse(pdf_path(key).exists(), f"{key}: PDF must remain unpublished while logical text is unreliable")
            else:
                self.assertTrue(pdf_path(key).is_file(), pdf_path(key))
            text = source.read_text(encoding="utf-8")
            for token in ("ChatGPT", "Claude", "Hermes", "Florence-X", "2026"):
                self.assertIn(token, text, f"{key}: {token}")
            price_tokens = ("10 $US", "29,90 $US") if key == "fr" else ("$10", "$29.90")
            for token in price_tokens:
                self.assertIn(token, text, f"{key}: {token}")
            self.assertIn(POSTURES[key], text, key)
            self.assertGreater(len(text), 2000, key)
            if key != "en":
                self.assertIn(DISCLOSURES[key], text, key)
            claim_text = positive_claim_text(text, DONT_SAY_MARKERS[key])
            for phrase in (*OVERCLAIMS["en"], *OVERCLAIMS[key]):
                self.assertNotIn(phrase.casefold(), claim_text, f"{key}: unsupported positive claim {phrase!r}")

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
        for key in PDF_KEYS:
            reader = PdfReader(pdf_path(key))
            metadata = reader.metadata
            self.assertEqual(metadata.title, TITLES[key], key)
            self.assertEqual(metadata.author, "Robert Domondon", key)
            self.assertIsNone(metadata.get("/CreationDate"), key)
            self.assertIsNone(metadata.get("/ModDate"), key)
            expected_digest = hashlib.sha256(source_path(key).read_bytes()).hexdigest()
            self.assertEqual(metadata.get("/SourceSHA256"), expected_digest, f"{key}: stale source/PDF pair")
            self.assertIn("/StructTreeRoot", reader.trailer["/Root"], f"{key}: untagged PDF")
            self.assertGreaterEqual(len(reader.pages), 2, key)
            self.assertLessEqual(len(reader.pages), 15, key)
            extracted = " ".join((page.extract_text() or "") for page in reader.pages)
            self.assertNotIn("\x00", extracted, f"{key}: corrupt logical text")
            self.assertIn("Nurse AI OS", extracted, key)
            self.assertIn("ChatGPT", extracted, key)
            self.assertIn("Claude", extracted, key)
            self.assertIn("Hermes", extracted, key)
            if key == "zh":
                source_cjk = re.findall(r"[\u3400-\u9fff]", source_path(key).read_text(encoding="utf-8"))
                extracted_cjk = re.findall(r"[\u3400-\u9fff]", extracted)
                self.assertEqual(len(extracted_cjk), len(source_cjk), "zh: incomplete CJK logical text")
                self.assertGreater(len(extracted), 2200, key)
            else:
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
            names = pdf_name_tokens(reader.trailer)
            for forbidden in ("/JavaScript", "/JS", "/Launch", "/GoToR", "/SubmitForm", "/ImportData",
                              "/EmbeddedFiles", "/OpenAction", "/AcroForm", "/RichMedia", "/Movie", "/Sound"):
                self.assertNotIn(forbidden, names, f"{key}: {forbidden}")

    def test_active_content_scanner_rejects_action_values(self):
        launch_action = DictionaryObject({NameObject("/S"): NameObject("/Launch")})
        javascript_action = DictionaryObject({NameObject("/S"): NameObject("/JavaScript")})
        self.assertIn("/Launch", pdf_name_tokens(launch_action))
        self.assertIn("/JavaScript", pdf_name_tokens(javascript_action))

    def test_accessible_html_publications_are_bound_to_their_sources(self):
        expected_root = {"ar": '<html lang="ar" dir="rtl">', "hi": '<html lang="hi" dir="ltr">'}
        for key in HTML_KEYS:
            page = (ROOT / f"media-{key}.html").read_text(encoding="utf-8")
            digest = hashlib.sha256(source_path(key).read_bytes()).hexdigest()
            self.assertIn(f'<meta name="source-sha256" content="{digest}">', page)
            self.assertIn(expected_root[key], page)
            if key == "hi":
                self.assertIn('content="Nurse AI OS का सुलभ हिंदी मीडिया संक्षेप।"', page)
            for token in ("Nurse AI OS", "ChatGPT", "Claude", "Hermes", "Florence-X", "$29.90"):
                self.assertIn(token, page)
            self.assertNotIn(f"nurse-ai-os-media-packet-{key}.pdf", page)

    def test_media_center_advertises_exact_complete_inventory(self):
        page = (ROOT / "media.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("https://nurse-ai-os.org/media.html"), 1)
        self.assertEqual(sitemap.count("https://nurse-ai-os.org/media-ar.html"), 1)
        self.assertEqual(sitemap.count("https://nurse-ai-os.org/media-hi.html"), 1)
        self.assertIn("The English packet is the canonical source", page)
        self.assertIn("have not received professional native-language editorial certification", page)
        for key in KEYS:
            suffix = SUFFIX[key]
            expected_count = 2 if key == "en" else 1
            self.assertEqual(page.count(f'assets/nurse-ai-os-media-packet{suffix}.md'), expected_count, key)
            if key in PDF_KEYS:
                self.assertEqual(page.count(f'assets/nurse-ai-os-media-packet{suffix}.pdf'), expected_count, key)
            else:
                self.assertNotIn(f'assets/nurse-ai-os-media-packet{suffix}.pdf', page)
                self.assertEqual(page.count(f'href="media-{key}.html"'), 1)
        self.assertIn("does not preserve reliable Devanagari copy/search text", page)
        self.assertIn("لا يحافظ على نص عربي موثوق للنسخ والبحث", page)
        self.assertEqual(page.count('class="nav-cta" href="soul-quiz.html"'), 1)
        self.assertIn('<a class="skip-link" href="#main-content">', page)
        self.assertIn('<main id="main-content">', page)
        self.assertIn(".status-table{min-width:680px}", page)
        self.assertNotIn(".status-table thead{position:absolute", page)

    def test_every_about_page_has_one_bounded_current_media_card(self):
        expected = {"en": "assets/nurse-ai-os-media-packet.pdf", **{
            locale: f"../assets/nurse-ai-os-media-packet-{locale}.pdf" for locale in LOCALES
        }}
        expected["ar"] = "../media-ar.html"
        expected["hi"] = "../media-hi.html"
        for key in KEYS:
            path = ROOT / ("about.html" if key == "en" else f"{key}/about.html")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("<!-- ============ MEDIA KIT ============ -->"), 1, key)
            self.assertEqual(text.count(expected[key]), 1, key)
            target = 'href="media.html"' if key == "en" else 'href="../media.html"'
            self.assertEqual(text.count(target), 1, key)

    def test_about_pages_bound_naio_authority(self):
        retired = (
            "Governance authority", "Autoridad de gobernanza", "Governance authority",
            "治理机构", "مرجعية الحوكمة", "Cơ quan quản trị", "Центр управления",
            "गवर्नेंस प्राधिकरण", "Autorité de gouvernance", "FAA of healthcare AI",
            "FAA de la IA sanitaria", "FAA ng healthcare AI", "医疗 AI 航管局",
            "FAA</bdi> للذكاء", "FAA của AI", "аналогом FAA", "हेल्थकेयर AI का FAA", "FAA de l’IA",
        )
        for key in KEYS:
            path = ROOT / ("about.html" if key == "en" else f"{key}/about.html")
            text = path.read_text(encoding="utf-8")
            for phrase in retired:
                self.assertNotIn(phrase, text, f"{key}: retired authority framing")
            self.assertIn("boundary-note", text, key)
            self.assertEqual(text.count('class="zone orange"'), 1, key)

    def test_counter_labels_use_current_media_kit_name(self):
        retired = ("Media packets", "Paquetes de medios", "媒体包（全语言）", "الحزم الإعلامية", "Gói truyền thông", "медиапакеты", "Dossiers médias")
        for key in KEYS:
            path = ROOT / ("index.html" if key == "en" else f"{key}/index.html")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count('id="stat-media"'), 1, key)
            for phrase in retired:
                self.assertNotIn(phrase, text, f"{key}: {phrase}")

    def test_workflow_and_dependencies_are_immutably_pinned(self):
        workflow = (ROOT / ".github/workflows/media-packet.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"actions/checkout@[0-9a-f]{40}")
        self.assertRegex(workflow, r"actions/setup-python@[0-9a-f]{40}")
        self.assertRegex(workflow, r"actions/setup-node@[0-9a-f]{40}")
        self.assertNotRegex(workflow, r"actions/(?:checkout|setup-python|setup-node)@v\d")
        renderer_text = (ROOT / "scripts/render-media-pdf.sh").read_text(encoding="utf-8")
        self.assertIn("mcr.microsoft.com/playwright@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48",
                      renderer_text)
        for flag in ("--user", "--env HOME=/tmp", "--network=none", "--read-only",
                     "--security-opt no-new-privileges", "--cap-drop=ALL"):
            self.assertIn(flag, renderer_text)
        self.assertIn('"playwright-core": "1.61.1"', (ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("npm ci --ignore-scripts", workflow)
        self.assertIn("tagged: true", (ROOT / "scripts/render-media-pdf.mjs").read_text(encoding="utf-8"))
        self.assertEqual(workflow.count('git ls-files --error-unmatch -- "${artifacts[@]}"'), 1)
        self.assertEqual(workflow.count('python tools/build-pdfs.py "${targets[@]}"'), 2)
        for artifact in (
            "assets/nurse-ai-os-media-packet.pdf", "assets/nurse-ai-os-media-packet-es.pdf",
            "assets/nurse-ai-os-media-packet-tl.pdf", "assets/nurse-ai-os-media-packet-zh.pdf",
            "assets/nurse-ai-os-media-packet-vi.pdf", "assets/nurse-ai-os-media-packet-ru.pdf",
            "assets/nurse-ai-os-media-packet-fr.pdf", "media-ar.html", "media-hi.html",
        ):
            self.assertIn(artifact, workflow)
        requirements = (ROOT / "scripts/requirements-media-pdf.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(2, len(requirements))
        for line in requirements:
            self.assertRegex(line, r"^[A-Za-z]+==[0-9.]+ --hash=sha256:[0-9a-f]{64}$")

    def test_removed_inaccessible_pdfs_are_not_publicly_referenced(self):
        for path in ROOT.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            for key in HTML_KEYS:
                self.assertNotIn(f"nurse-ai-os-media-packet-{key}.pdf", text, str(path))

    def test_builder_declares_every_media_target_and_stable_metadata(self):
        text = (ROOT / "tools" / "build-pdfs.py").read_text(encoding="utf-8")
        for key in ("media", "media-es", "media-tl", "media-zh", "media-ar", "media-vi", "media-ru", "media-hi", "media-fr"):
            self.assertRegex(text, rf'"{re.escape(key)}"\s*:', key)
        for phrase in ("canonicalize_pdf", "writer._info = None", "writer._ID = None", "os.replace(canonical, out)",
                       '"/SourceSHA256": source_digest', "def build_html", "os.replace(temporary, out)"):
            self.assertIn(phrase, text)
        self.assertNotIn('"assets/nurse-ai-os-media-packet-hi.pdf"', text)
        self.assertNotIn('"assets/nurse-ai-os-media-packet-ar.pdf"', text)
        self.assertNotIn("fonts.googleapis.com", text)
        for relative in ("assets/fonts/NotoSansSC-Media.woff2", "assets/fonts/OFL-NotoSansSC.txt"):
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 4000, relative)


if __name__ == "__main__":
    unittest.main()
