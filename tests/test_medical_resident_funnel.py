#!/usr/bin/env python3
"""Conversion, privacy, governance, and media contracts for the medical-resident funnel."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "medical-resident.html"
SCRIPT = ROOT / "assets" / "medical-resident-funnel.js"
CSS = ROOT / "assets" / "nurse-ai.css"
PATHWAYS = ROOT / "pathways.html"
ECOSYSTEM = ROOT / "explore-ecosystem.html"
HOME = ROOT / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "website-alignment.yml"


class MedicalResidentFunnelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
        cls.script = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
        cls.css = CSS.read_text(encoding="utf-8")
        cls.pathways = PATHWAYS.read_text(encoding="utf-8")
        cls.ecosystem = ECOSYSTEM.read_text(encoding="utf-8")
        cls.home = HOME.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_route_names_one_audience_offer_and_literal_primary_action(self) -> None:
        self.assertTrue(PAGE.is_file())
        hero = self.page.split('class="resident-hero"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "For medical residents",
            "Every rotation changes the map. Your boundaries should not.",
            "Build my Resident Learning Practice Card",
            "Free Medical Resident Community Preview — personal use",
            "No account",
            "No download",
            "No patient or program data",
        ):
            self.assertIn(phrase, hero)
        self.assertNotIn("Take the SOUL Quiz", hero)
        self.assertNotIn("Hermes", hero)
        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.page, re.I
        )
        self.assertGreaterEqual(len(primary_links), 2)
        self.assertEqual({"#resident-card-builder"}, set(primary_links))

    def test_social_preview_uses_absolute_reviewed_image_metadata(self) -> None:
        image_url = "https://nurse-ai-os.org/assets/img/resident-rotation-learning.jpg"
        self.assertIn(f'<meta property="og:image" content="{image_url}">', self.page)
        self.assertIn(f'<meta name="twitter:image" content="{image_url}">', self.page)
        self.assertIn('<meta property="og:image:width" content="1024">', self.page)
        self.assertIn('<meta property="og:image:height" content="576">', self.page)

    def test_first_use_builder_precedes_pain_media_and_advanced_setup(self) -> None:
        credibility_end = self.page.index("</section>", self.page.index("resident-credibility"))
        builder = self.page.index('id="resident-card-builder"')
        pain = self.page.index('id="resident-pressure"')
        media = self.page.index('class="resident-photo-card"')
        advanced = self.page.index('id="resident-advanced-path"')
        self.assertLess(credibility_end, builder)
        self.assertLess(builder, pain)
        self.assertLess(builder, media)
        self.assertLess(media, advanced)

    def test_builder_is_closed_choice_browser_local_and_provider_boundary_is_adjacent(self) -> None:
        builder = self.page.split('id="resident-card-builder"', 1)[1].split(
            "</section>", 1
        )[0]
        for token in (
            'id="resident-focus"',
            'id="resident-capacity"',
            'id="resident-style"',
            'id="resident-review"',
            'id="resident-practice-card"',
            'id="copy-resident-practice-card"',
            'aria-live="polite"',
            "stay in this page’s memory",
            "This site does not receive or store them",
            "the content leaves nurse-ai-os.org",
            "privacy, retention, training, account, and data-use settings apply",
            'href="privacy.html"',
        ):
            self.assertIn(token, builder)
        controls = builder.split('<div class="resident-config-panel"', 1)[1].split(
            "</div>", 1
        )[0]
        self.assertNotIn('<input type="text"', controls)
        self.assertNotIn("<textarea", controls)
        self.assertIn('src="assets/medical-resident-funnel.js"', self.page)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "localStorage",
            "sessionStorage",
            "indexedDB",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_practice_card_front_loads_resident_specific_safety_and_authority_contract(self) -> None:
        for phrase in (
            "No patient data or PHI",
            "No patient cases, case narratives, or identifiable stories, even if names are removed",
            "No EHR, sign-out, chart, consult, handoff, schedule, or incident content",
            "No faculty, colleague, learner, or third-party identifiers",
            "No evaluations, personnel records, or confidential program material",
            "No protected exam questions, recalled test content, or restricted educational material",
            "Do not diagnose, triage, choose treatment, make patient-specific decisions, write chart content, or direct care",
            "Do not determine competence, entrustment, supervision level, procedural authorization, duty-hour compliance, program standing, or credentialing",
            "Do not replace faculty supervision, program policy, institutional policy, or resident reasoning",
            "public, synthetic, or personally authored nonconfidential material",
            "personal-use educational Draft support",
            "require my human review",
            "Proposed next step",
        ):
            self.assertIn(phrase.casefold(), self.script.casefold(), phrase)
        self.assertNotIn("recommend", self.script.casefold())
        self.assertIn("Built into your card", self.page)

    def test_configurator_exposes_four_resident_controls_and_bounded_options(self) -> None:
        for control in ("resident-focus", "resident-capacity", "resident-style", "resident-review"):
            self.assertIn(f'id="{control}"', self.page)
            self.assertIn(f'getElementById("{control}")', self.script)
        for option in (
            "Rotation learning plan",
            "Board and knowledge review",
            "Journal club preparation",
            "Teaching preparation",
            "Feedback reflection",
            "Career and portfolio",
            "10 minutes · low capacity",
            "25 minutes · focused",
            "45 minutes · deep work",
            "Socratic questions",
            "Structured outline",
            "Source-first synthesis",
            "Challenge my assumptions",
            "Draft one artifact, then stop",
            "Source verification checkpoint",
            "Supervisor or policy checkpoint",
            "Human review before use",
        ):
            self.assertIn(option, self.page + self.script)

    def test_free_preview_and_rounds_boundary_are_explicit(self) -> None:
        for phrase in (
            "$0",
            "No credit card",
            "not the ROUNDS Medical Resident Complete AI OS",
            "not an activated ROUNDS build kit",
            "not a residency program or institutional deployment",
            "does not provide clinical, educational, evaluative, supervisory, credentialing, or organizational authority",
            "does not connect to hospital or program systems",
            "does not make an AI provider private or compliant",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)
        self.assertNotIn("HIPAA-compliant", self.page)
        self.assertNotIn("protects your license", self.page.casefold())
        self.assertNotIn("residency-ready", self.page.casefold())

    def test_pressure_points_are_specific_without_outcome_promises(self) -> None:
        pressure = self.page.split('id="resident-pressure"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "Every rotation restarts the context",
            "Learning competes with recovery",
            "Feedback can feel bigger than the next question",
            "Generic AI blurs learning with clinical authority",
            "Scholarship and career work fragment across the year",
        ):
            self.assertIn(phrase, pressure)
        for overclaim in (
            "reduce burnout",
            "prevent burnout",
            "save hours",
            "improve exam scores",
            "improve patient outcomes",
            "prevent errors",
            "guarantee a fellowship",
            "reclaim your time",
        ):
            self.assertNotIn(overclaim, self.page.casefold())

    def test_evidence_note_is_qualified_and_linked_to_primary_sources(self) -> None:
        for url in (
            "https://www.acgme.org/globalassets/pfassets/programrequirements/2025-reformatted-requirements/cprresidency_2025_reformatted.pdf",
            "https://www.aamc.org/about-us/mission-areas/medical-education/principles-ai-use",
        ):
            self.assertIn(url, self.page)
        for phrase in (
            "graded authority and responsibility",
            "appropriate faculty supervision and conditional independence",
            "human judgment remains essential",
            "learner assessment and program evaluation",
            "do not validate this preview",
            "do not prove improvements in learning, exam performance, workload, wellbeing, clinical care, or career outcomes",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)

    def test_photorealistic_assets_are_stable_accessible_and_truthfully_labeled(self) -> None:
        images = (
            (
                "assets/img/resident-rotation-learning.jpg",
                "Medical resident studying alone at a quiet desk with unmarked books and a blank notebook.",
            ),
            (
                "assets/img/resident-journal-club.jpg",
                "Medical resident preparing alone in an empty conference room with blank papers and an unreadable laptop screen.",
            ),
            (
                "assets/img/resident-career-prep.jpg",
                "Medical resident organizing a personal portfolio alone at a home desk with blank cards.",
            ),
        )
        for src, alt in images:
            self.assertIn(f'src="{src}"', self.page)
            self.assertIn(f'alt="{alt}"', self.page)
            tag = re.search(rf'<img[^>]+src="{re.escape(src)}"[^>]*>', self.page)
            self.assertIsNotNone(tag, src)
            assert tag is not None
            markup = tag.group(0)
            self.assertIn('width="1024"', markup)
            self.assertIn('height="576"', markup)
            self.assertIn('loading="lazy"', markup)
            asset = ROOT / src
            self.assertTrue(asset.is_file(), src)
            self.assertTrue(asset.read_bytes().startswith(b"\xff\xd8\xff"), src)
        self.assertEqual(3, self.page.count("Synthetic photograph:"))
        self.assertNotIn(".hermes/desktop-attachments", self.page)
        self.assertNotIn("fal.media", self.page)

    def test_advanced_rounds_path_is_late_optional_separate_and_truthful(self) -> None:
        advanced = self.page.split('id="resident-advanced-path"', 1)[1].split(
            "</section>", 1
        )[0]
        for phrase in (
            "Optional advanced path",
            "standalone adjacent clinical lane",
            "self-install Hermes build kit",
            "Downloading or unzipping changes nothing",
            "not operational—build required",
            "24 optional SuperPowers remain inactive",
            "explicit approval",
            "does not authorize clinical care, supervision, evaluation, credentialing, GME administration, or institutional deployment",
        ):
            self.assertIn(phrase.casefold(), advanced.casefold(), phrase)
        self.assertIn('href="medical-residents/"', advanced)

    def test_route_is_integrated_without_replacing_rounds_or_homepage_audience(self) -> None:
        for surface in (self.pathways, self.ecosystem, self.home):
            self.assertIn('href="medical-resident.html"', surface)
        self.assertIn("For nurse leaders and nurse educators", self.home)
        self.assertIn('href="#workbench"', self.home)
        self.assertIn('href="medical-residents/"', self.ecosystem)
        self.assertIn("Medical Resident Community Preview", self.pathways)
        self.assertIn("Resident Learning Practice Card", self.ecosystem)

    def test_sitemap_ci_shell_and_package_scripts_own_the_route(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        shell = (ROOT / "assets" / "site-shell.js").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/medical-resident.html"))
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/medical-residents/"))
        for path in (
            "assets/medical-resident-funnel.js",
            "assets/img/resident-rotation-learning.jpg",
            "assets/img/resident-journal-club.jpg",
            "assets/img/resident-career-prep.jpg",
            "tests/test_medical_resident_funnel.py",
            "tests/test_medical_resident_browser.mjs",
        ):
            self.assertGreaterEqual(self.workflow.count(path), 2, path)
        scanned = self.workflow.split("pages=(", 1)[1]
        for path in (
            "medical-resident.html",
            "assets/medical-resident-funnel.js",
            "pathways.html",
        ):
            self.assertIn(path, scanned)
        self.assertIn('"medical-resident.html": true', shell)
        self.assertIn("test:medical-resident-browser", package)

    def test_schema_accessibility_and_late_language_links_are_complete(self) -> None:
        self.assertIn(
            '<link rel="canonical" href="https://nurse-ai-os.org/medical-resident.html">',
            self.page,
        )
        self.assertIn('<main id="main-content" tabindex="-1">', self.page)
        self.assertIn('class="skip-link" href="#main-content"', self.page)
        self.assertEqual(1, len(re.findall(r"<h1\b", self.page, re.I)))
        self.assertIn('aria-label="Primary navigation"', self.page)
        title = re.search(r"<title>(.*?)</title>", self.page, re.I | re.S)
        self.assertIsNotNone(title)
        self.assertLessEqual(len(title.group(1)), 70)
        self.assertNotIn("<form", self.page.casefold())
        self.assertIn('role="group" aria-label="Resident Learning Practice Card controls"', self.page)
        asides = re.findall(r"<aside\b[^>]*>", self.page, re.I)
        self.assertTrue(asides)
        for aside in asides:
            self.assertRegex(aside, r'aria-(?:label|labelledby)="[^"]+"')
        language_nav = self.page.index('aria-label="Explore Nurse AI OS in other languages"')
        self.assertGreater(language_nav, self.page.index("</main>"))
        footer_language_block = self.page[language_nav:].split("</nav>", 1)[0]
        self.assertEqual(9, len(re.findall(r"<a\b", footer_language_block)))
        blocks = re.findall(
            r'<script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>\s*(.*?)\s*</script>',
            self.page,
            re.DOTALL | re.IGNORECASE,
        )
        self.assertEqual(1, len(blocks))
        schema = json.loads(blocks[0])
        self.assertEqual("WebPage", schema["@type"])
        self.assertEqual("https://nurse-ai-os.org/medical-resident.html", schema["url"])
        self.assertTrue(schema["isAccessibleForFree"])

    def test_resident_styles_are_responsive_and_scoped(self) -> None:
        for token in (
            ".medical-resident-funnel",
            ".resident-hero",
            ".resident-practice-card-preview",
            ".resident-focus-grid",
            ".resident-pressure-grid",
            ".resident-photo-grid",
            ".resident-provider-boundary",
            ".resident-footer-languages",
            "@media (max-width: 620px)",
        ):
            self.assertIn(token, self.css)
        self.assertRegex(
            self.css,
            r"\.resident-provider-boundary a\s*\{[^}]*color:\s*var\(--navy-800\)",
        )


if __name__ == "__main__":
    unittest.main()
