import hashlib
import json
import re
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
ABOUT_PAGES = (ROOT / "about.html",) + tuple(ROOT / locale / "about.html" for locale in LOCALES)
HOME_PAGES = (ROOT / "index.html",) + tuple(ROOT / locale / "index.html" for locale in LOCALES)
MEDIA_SOURCES = (ROOT / "assets" / "nurse-ai-os-media-packet.md",) + tuple(
    ROOT / "assets" / f"nurse-ai-os-media-packet-{locale}.md" for locale in LOCALES
)


class DirectiveV11WebsiteAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.harness = (ROOT / "governed-harness.html").read_text(encoding="utf-8")
        cls.architecture = (ROOT / "architecture-report.html").read_text(encoding="utf-8")
        cls.quiz_guide = (ROOT / "soul-quiz-guide.html").read_text(encoding="utf-8")
        cls.start = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.terms = (ROOT / "terms.html").read_text(encoding="utf-8")
        cls.privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        cls.licensing = (ROOT / "licensing.html").read_text(encoding="utf-8")
        cls.faq = (ROOT / "faq.html").read_text(encoding="utf-8")
        cls.personalize = (ROOT / "personalize.html").read_text(encoding="utf-8")

    def test_canonical_governed_environment_definition_and_three_public_states(self):
        required = (
            "governed professional environment",
            "Available now",
            "Capability-gated",
            "Formal-gate programs",
            "not an EHR",
            "not an autonomous clinician",
        )
        for phrase in required:
            self.assertIn(phrase.casefold(), self.home.casefold(), phrase)
        for retired in (
            "Now everyone in the hospital has an AI OS",
            "standalone ROUNDS lane",
            "standalone BREATHE lane",
            "standalone THRIVE lane",
        ):
            self.assertNotIn(retired.casefold(), self.home.casefold(), retired)

    def test_public_directive_page_is_complete_and_discoverable(self):
        path = ROOT / "directive.html"
        self.assertTrue(path.is_file())
        page = path.read_text(encoding="utf-8")
        required = (
            "NIN develops the profession and the ecosystem",
            "NAIO defines doctrine, standards, competence, and assurance",
            "Nurse AI OS provides the governed professional environment",
            "Florence-X plans, routes, coordinates, and evaluates the work",
            "EDENA determines what is permitted and enforces the controls",
            "Binding now",
            "Binding when capability exists",
            "Activated only through a formal gate",
            "Green", "Yellow", "Orange", "Red-P", "Red-E",
            "D0", "D1", "D2", "D3", "D4",
            "Observe", "Draft", "Recommend", "Prepare Action",
            "Act With Approval", "Constrained Autonomy",
            "Unrestricted Autonomy", "prohibited",
            "NAIO Conformant", "unavailable",
            "not legal advice",
        )
        for phrase in required:
            self.assertIn(phrase.casefold(), page.casefold(), phrase)
        self.assertEqual(page.count('<caption class="sr-only">'), 2)
        self.assertEqual(page.count('scope="col"'), 6)
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/directive.html"))
        self.assertIn('href="directive.html"', self.home)
        self.assertIn('href="directive.html"', (ROOT / "about.html").read_text(encoding="utf-8"))

    def test_harness_uses_directive_risk_data_and_action_semantics(self):
        for page_name, page in (("governed-harness", self.harness), ("architecture-report", self.architecture)):
            for retired in ("A0", "A1", "A2", "A3", "A4"):
                self.assertNotRegex(page, rf"\b{retired}\b", f"{page_name}: {retired}")
            for phrase in ("Red-P", "Red-E", "data class", "action mode"):
                self.assertIn(phrase.casefold(), page.casefold(), f"{page_name}: {phrase}")
        for phrase in (
            "Nurse AI OS is the governed professional environment",
            "Hermes currently provides a provisional, replaceable agent and memory substrate",
            "does not mechanically enforce every Florence-X or EDENA requirement",
        ):
            self.assertIn(phrase.casefold(), self.harness.casefold(), phrase)

    def test_architecture_report_is_historical_not_latest_or_conformant(self):
        for phrase in (
            "Pre-Directive",
            "historical implementation evidence",
            "not the current canonical architecture",
        ):
            self.assertIn(phrase.casefold(), self.architecture.casefold(), phrase)
        head_and_hero = self.architecture.split("</section>", 1)[0]
        self.assertNotIn("Latest Architecture Report", head_and_hero)
        self.assertNotIn("Latest verified architecture", head_and_hero)
        self.assertNotIn("Download the latest PDF", self.architecture)

    def test_architecture_report_displays_current_publication_digests(self):
        for label, artifact in (
            ("PDF", ROOT / "assets" / "nurse-ai-os-architecture-report.pdf"),
            ("Markdown", ROOT / "assets" / "nurse-ai-os-architecture-report.md"),
        ):
            match = re.search(
                rf"{label} SHA-256:\s*<code class=\"digest\">([0-9a-f]{{64}})</code>",
                self.architecture,
            )
            self.assertIsNotNone(match, label)
            assert match is not None
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), match.group(1), label)

    def test_homepage_operator_schema_has_one_person_without_nested_founder(self):
        for path in HOME_PAGES:
            text = path.read_text(encoding="utf-8")
            blocks = re.findall(
                r'<script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>\s*(.*?)\s*</script>',
                text,
                re.DOTALL | re.IGNORECASE,
            )
            self.assertTrue(blocks, path.relative_to(ROOT))
            graph = []
            for block in blocks:
                payload = json.loads(block)
                graph.extend(payload.get("@graph", [payload]))
            operator = [node for node in graph if node.get("@id") == "https://nurse-ai-os.org/#operator"]
            self.assertEqual(len(operator), 1, path.relative_to(ROOT))
            self.assertEqual(operator[0].get("@type"), "Person", path.relative_to(ROOT))
            self.assertNotIn("founder", operator[0], path.relative_to(ROOT))
            self.assertIn("jobTitle", operator[0], path.relative_to(ROOT))
            expected_about = "https://nurse-ai-os.org/about.html" if path == HOME_PAGES[0] else f"https://nurse-ai-os.org/{path.parent.name}/about.html"
            self.assertEqual(operator[0].get("url"), expected_about, path.relative_to(ROOT))
            websites = [node for node in graph if node.get("@type") == "WebSite"]
            self.assertEqual(len(websites), 1, path.relative_to(ROOT))
            self.assertEqual(
                websites[0].get("publisher"),
                {"@id": "https://nurse-ai-os.org/#operator"},
                path.relative_to(ROOT),
            )

    def test_website_alignment_workflow_covers_all_nested_html(self):
        workflow = (ROOT / ".github" / "workflows" / "website-alignment.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count('- "**/*.html"'), 2)
        self.assertNotIn('- "*.html"', workflow)
        scanner_pages = workflow.split("pages=(", 1)[1].split(")", 1)[0]
        self.assertIn("care-intelligence/index.html", scanner_pages)

    def test_care_intelligence_download_is_visibly_historical_and_docx_is_delinked(self):
        page = (ROOT / "care-intelligence" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Historical pre-Directive working paper",
            "predates NIN–NAIO Master Directive v1.1",
            "not presented as current architecture",
            "Historical PDF",
        ):
            self.assertIn(phrase, page, phrase)
        anchors = re.findall(
            r'<a\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            page,
            re.DOTALL | re.IGNORECASE,
        )
        normalized = [
            (unquote(urlsplit(unescape(href)).path).casefold(), unescape(re.sub(r"<[^>]+>", " ", body)))
            for href, body in anchors
        ]
        self.assertFalse(
            any(href.rstrip("/").endswith("care-intelligence-white-paper.docx") for href, _ in normalized)
        )
        pdf_links = [
            label for href, label in normalized
            if href.rstrip("/").endswith("care-intelligence-white-paper.pdf")
        ]
        self.assertEqual(len(pdf_links), 3)
        for label in pdf_links:
            self.assertRegex(label.casefold(), r"historical|pre-directive")

    def test_quiz_and_public_onboarding_use_current_scope_not_a0(self):
        self.assertNotRegex(self.quiz_guide, r"\bA0\b")
        for phrase in ("Green tier", "D0/D1", "Draft mode", "no external action"):
            self.assertIn(phrase.casefold(), self.quiz_guide.casefold(), phrase)
        self.assertNotIn("Green tier · D0/D1 only · Recommend mode", self.quiz_guide)
        self.assertIn("does not rank or propose a course of action", self.quiz_guide)
        for phrase in ("public Community experience", "D0/D1", "no PHI", "no external action"):
            self.assertIn(phrase.casefold(), self.start.casefold(), phrase)

    def test_personalization_uses_advisory_community_boundaries(self):
        for phrase in (
            "Apply the same Community boundaries to each profile",
            "available Community experience is D0/D1 and no-PHI",
            "user-applied instructions, not guaranteed host enforcement",
            "formal future tier requires separate authorization and implementation evidence",
        ):
            self.assertIn(phrase.casefold(), self.personalize.casefold(), phrase)
        self.assertNotIn("Every profile carries the same hard rules", self.personalize)
        self.assertNotIn("never, at any tier, PHI", self.personalize)

    def test_competency_framework_replaces_obsolete_fellowship_ladder_in_every_locale(self):
        retired = ("NAIO-C", "NAIO-A", "NAIO-F", "CAIOS")
        levels = (
            "Nurse AI Explorer",
            "Nurse AI Practitioner",
            "Nurse AI Workflow Specialist",
            "Nurse AI Agent Orchestrator",
            "Nurse AI Governance and Implementation Leader",
        )
        for path in ABOUT_PAGES:
            text = path.read_text(encoding="utf-8")
            for phrase in retired:
                self.assertNotIn(phrase, text, f"{path.relative_to(ROOT)}: {phrase}")
            for level in levels:
                self.assertIn(level, text, f"{path.relative_to(ROOT)}: {level}")
            self.assertIn("not licensure", text.casefold(), str(path.relative_to(ROOT)))

    def test_long_horizon_projects_are_explicitly_statused_in_every_locale(self):
        for path in ABOUT_PAGES:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                13,
                text.count('data-program-status="concept-research-proposal"'),
                str(path.relative_to(ROOT)),
            )
            self.assertIn("long-horizon research", text.casefold(), str(path.relative_to(ROOT)))
            self.assertIn("not an active program", text.casefold(), str(path.relative_to(ROOT)))
        localized_boundaries = {
            "es": "propuesta de investigación únicamente",
            "tl": "konsepto o panukalang pananaliksik lamang",
            "zh": "仅为概念或研究提案",
            "ar": "مفهوم أو مقترح بحثي فقط",
            "vi": "chỉ là khái niệm hoặc đề xuất nghiên cứu",
            "ru": "только концепция или исследовательское предложение",
            "hi": "केवल अवधारणा या शोध प्रस्ताव",
            "fr": "concept ou proposition de recherche uniquement",
        }
        for locale, boundary in localized_boundaries.items():
            text = (ROOT / locale / "about.html").read_text(encoding="utf-8")
            self.assertEqual(text.count(boundary), 13, locale)

    def test_every_about_page_has_the_full_secondary_language_navigation(self):
        labels = (
            "English", "Español", "Tagalog", "中文", "العربية",
            "Tiếng Việt", "Русский", "हिन्दी", "Français",
        )
        for path in ABOUT_PAGES:
            text = path.read_text(encoding="utf-8")
            head = text.split("</head>", 1)[0]
            language_nav = text.split('<nav class="language-nav"', 1)[1].split("</nav>", 1)[0]
            self.assertEqual(text.count('class="skip-link"'), 1, path)
            self.assertEqual(text.count('<main id="main-content" tabindex="-1">'), 1, path)
            self.assertEqual(text.count("</main>"), 1, path)
            self.assertEqual(head.count('rel="canonical"'), 1, path)
            self.assertEqual(head.count('rel="alternate"'), 10, path)
            for lang in ("en", "es", "tl", "zh-Hans", "ar", "vi", "ru", "hi", "fr", "x-default"):
                self.assertEqual(head.count(f'hreflang="{lang}"'), 1, f"{path}: {lang}")
            self.assertEqual(language_nav.count('class="language-chip'), 9, path)
            self.assertEqual(language_nav.count("is-active"), 1, path)
            self.assertEqual(language_nav.count('aria-current="page"'), 1, path)
            for label in labels:
                self.assertIn(label, language_nav, f"{path}: {label}")

    def test_nin_naio_firewall_and_participation_boundary_are_public(self):
        about = (ROOT / "about.html").read_text(encoding="utf-8")
        for phrase in (
            "Participation informs governance",
            "Formal governance authority follows published decision rights",
            "target governance model separates standards and assurance from commercial activity",
            "No separate NIN commercial entity or independent NAIO assurance body",
        ):
            self.assertIn(phrase.casefold(), about.casefold(), phrase)
        self.assertNotIn("participation creates governance", about.casefold())

    def test_public_legal_surfaces_use_current_service_and_artifact_specific_boundaries(self):
        for phrase in (
            "public Community personal-use experience",
            "not the formally gated Personal Edition",
            "D0/D1 only",
            "separately authorized Institutional or Sovereign environment",
        ):
            self.assertIn(phrase.casefold(), self.terms.casefold(), phrase)
        self.assertNotIn("no exceptions at any level of the program", self.terms.casefold())
        for phrase in (
            "artifact-specific",
            "existing license file",
            "Master Directive",
            "CC BY 4.0",
            "does not revoke or narrow prior rights",
            "open-core boundary is pending",
        ):
            self.assertIn(phrase.casefold(), self.licensing.casefold(), phrase)
        self.assertIn("D0/D1", self.privacy)
        self.assertIn("D2–D4", self.privacy)
        self.assertIn("artifact-specific", self.faq.casefold())
        self.assertNotIn("proprietary and all rights reserved", self.faq.casefold())
        self.assertNotIn("proprietary and all rights reserved", self.licensing.casefold())
        self.assertIn("Effective date: July 26, 2026", self.privacy)
        self.assertIn("Change record:", self.privacy)

    def test_current_offer_sheets_publish_required_boundaries(self):
        path = ROOT / "offers.html"
        self.assertTrue(path.is_file())
        page = path.read_text(encoding="utf-8")
        for phrase in (
            "Named buyer", "Evidence-based promise", "Prerequisites", "Deliverables",
            "Exclusions", "Acceptance criteria", "Customer responsibilities",
            "Data and EDENA ceiling", "Price", "Support", "Renewal and termination",
            "$0 forever", "$10 one time", "$29.90/year",
            "confirm availability before payment",
            "Interim operator", "Interim seller", "Robert Domondon",
            "Green Observe/Draft", "Yellow Recommend",
        ):
            self.assertIn(phrase.casefold(), page.casefold(), phrase)
        self.assertEqual(page.count('<caption class="sr-only">'), 3)
        self.assertEqual(page.count('scope="row"'), 36)
        self.assertIn('href="offers.html"', self.home)
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/offers.html"))

    def test_media_sources_carry_directive_definition_and_state_boundaries(self):
        for path in MEDIA_SOURCES:
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Directive v1.1",
                "governed professional environment",
                "Available now",
                "Capability-gated",
                "Formal-gate programs",
                "NAIO Conformant is unavailable",
            ):
                self.assertIn(phrase.casefold(), text.casefold(), f"{path.name}: {phrase}")
            self.assertNotIn("Ethical Design & Enablement for Nursing Augmentation", text)
            self.assertIn("Red-P/Red-E", text)
            self.assertNotIn("Master Directive is all-rights-reserved", text)
            self.assertIn("Existing Apache and CC BY grants", text)

    def test_unrecorded_naio_and_edena_expansions_are_not_public_claims(self):
        retired = (
            "Nurse AI Operating Intelligence",
            "Ethical Design & Enablement for Nursing Augmentation",
            "Diseño ético y habilitación para ampliar las capacidades de enfermería",
        )
        public_texts = [path for path in ROOT.rglob("*.html") if "node_modules" not in path.parts]
        public_texts.extend(MEDIA_SOURCES)
        for path in public_texts:
            text = path.read_text(encoding="utf-8")
            for phrase in retired:
                self.assertNotIn(phrase, text, f"{path.relative_to(ROOT)}: {phrase}")

    def test_certification_and_historical_sources_are_prospective_or_superseded(self):
        governance = (ROOT / "GOVERNANCE.md").read_text(encoding="utf-8")
        trademarks = (ROOT / "TRADEMARKS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        raw_architecture = (ROOT / "assets" / "governed-harness-2-architecture.md").read_text(encoding="utf-8")
        raw_harness = (ROOT / "naio-harness-v2" / "README.md").read_text(encoding="utf-8")
        self.assertIn("No official certification or badge program is currently launched", governance)
        self.assertIn("No official Nurse AI OS certification or badge program is currently launched", trademarks)
        self.assertIn("Historical pre-Directive Architecture Report", readme)
        self.assertNotIn("Latest Architecture Report", readme)
        for source in (raw_architecture, raw_harness):
            self.assertIn("Historical implementation evidence", source)
            self.assertIn("legacy", source.casefold())

    def test_pre_directive_article_is_not_presented_as_current_canonical_architecture(self):
        article = (ROOT / "article-evidence-nurse-ai-os.html").read_text(encoding="utf-8")
        self.assertIn("pre-Directive", article)
        self.assertIn("historical implementation evidence", article.casefold())
        self.assertIn('href="directive.html"', article)

    def test_switchboard_legacy_semantics_are_visibly_superseded(self):
        page = (ROOT / "switchboard" / "index.html").read_text(encoding="utf-8")
        registry = (ROOT / "switchboard" / "data" / "role-registry.json").read_text(encoding="utf-8")
        schema = (ROOT / "switchboard" / "schema" / "role-registry-entry.schema.json").read_text(encoding="utf-8")
        for phrase in (
            "Pre-Directive legacy preview semantics",
            "A0 is not a current Directive v1.1 action mode",
            "Green risk · D0/D1 · Observe mode · no external action",
            'href="../directive.html"',
        ):
            self.assertIn(phrase, page)
        self.assertIn('"directiveVersion": "1.1"', registry)
        self.assertIn('"legacySemantics"', registry)
        self.assertIn("Legacy pre-Directive preview field", schema)

    def test_mutable_architecture_publication_is_historical(self):
        source = (ROOT / "assets" / "nurse-ai-os-architecture-report.md").read_text(encoding="utf-8")
        self.assertIn("Pre-Directive Architecture Evidence", source)
        self.assertIn("not the current canonical architecture", source)
        self.assertIn("not current EDENA taxonomy", source)


if __name__ == "__main__":
    unittest.main()
