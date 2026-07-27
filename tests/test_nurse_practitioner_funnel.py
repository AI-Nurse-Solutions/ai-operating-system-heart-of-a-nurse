#!/usr/bin/env python3
"""Conversion, privacy, governance, and media contracts for the NP funnel."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "nurse-practitioner.html"
SCRIPT = ROOT / "assets" / "nurse-practitioner-funnel.js"
CSS = ROOT / "assets" / "nurse-ai.css"
PATHWAYS = ROOT / "pathways.html"
ECOSYSTEM = ROOT / "explore-ecosystem.html"
HOME = ROOT / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "website-alignment.yml"


class NursePractitionerFunnelTests(unittest.TestCase):
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
        hero = self.page.split('class="np-hero"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "For nurse practitioners",
            "You already use AI. Now make it answer to your practice.",
            "Build my Personal AI Practice Card",
            "Free NP Community Preview — personal use",
            "No account",
            "No download",
            "No patient data",
        ):
            self.assertIn(phrase, hero)
        self.assertNotIn("Take the SOUL Quiz", hero)
        self.assertNotIn("Download WINGS", hero)
        header = self.page.split("<header", 1)[1].split("</header>", 1)[0]
        self.assertNotIn('class="brand" href=', header)
        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.page, re.I
        )
        self.assertGreaterEqual(len(primary_links), 2)
        self.assertEqual({"#practice-card-builder"}, set(primary_links))

    def test_social_preview_uses_absolute_reviewed_image_metadata(self) -> None:
        image_url = (
            "https://nurse-ai-os.org/assets/img/np-intentional-practice.jpg"
        )
        self.assertIn(
            f'<meta property="og:image" content="{image_url}">', self.page
        )
        self.assertIn(
            f'<meta name="twitter:image" content="{image_url}">', self.page
        )

    def test_first_use_builder_precedes_pain_media_field_notes_and_advanced_setup(self) -> None:
        credibility_end = self.page.index("</section>", self.page.index("np-credibility"))
        builder = self.page.index('id="practice-card-builder"')
        pain = self.page.index('id="np-pain-points"')
        media = self.page.index('class="np-photo-card"')
        field_notes = self.page.index('id="field-notes"')
        advanced = self.page.index('id="np-advanced-path"')
        self.assertLess(credibility_end, builder)
        self.assertLess(builder, pain)
        self.assertLess(builder, media)
        self.assertLess(builder, field_notes)
        self.assertLess(field_notes, advanced)

    def test_builder_is_closed_choice_browser_local_and_provider_boundary_is_adjacent(self) -> None:
        builder = self.page.split('id="practice-card-builder"', 1)[1].split(
            "</section>", 1
        )[0]
        for token in (
            'id="np-focus"',
            'id="np-style"',
            'id="np-evidence"',
            'id="np-review"',
            'id="np-practice-card"',
            'id="copy-np-practice-card"',
            'aria-live="polite"',
            "stay in this page’s memory",
            "the content leaves nurse-ai-os.org",
            "privacy, retention, training, account, and data-use settings apply",
            'href="privacy.html"',
        ):
            self.assertIn(token, builder)
        controls = builder.split('<form class="np-config-panel"', 1)[1].split(
            "</form>", 1
        )[0]
        self.assertNotIn('<input type="text"', controls)
        self.assertNotIn("<textarea", controls)
        self.assertIn('src="assets/nurse-practitioner-funnel.js"', self.page)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "localStorage",
            "sessionStorage",
            "indexedDB",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_practice_card_front_loads_nonclinical_personal_use_contract(self) -> None:
        for phrase in (
            "No patient data or PHI",
            "No patient stories, even if names are removed",
            "No employer-confidential information",
            "No credentials, secrets, or restricted records",
            "Do not diagnose, prescribe, triage, code, bill, or make patient-specific decisions",
            "Do not connect to an EHR, employer system, or clinical workflow",
            "public sources I name or select",
            "Proposed next check",
            "Label uncertainty",
            "require my human review",
            "Personal-use Draft support only",
        ):
            self.assertIn(phrase.casefold(), self.script.casefold(), phrase)
        self.assertNotIn("approved public sources", self.script.casefold())
        self.assertNotIn("Recommended next check", self.script)
        self.assertIn("Built into your card", self.page)

    def test_configurator_exposes_four_personal_controls_and_bounded_options(self) -> None:
        for control in ("np-focus", "np-style", "np-evidence", "np-review"):
            self.assertIn(f'id="{control}"', self.page)
            self.assertIn(f'getElementById("{control}")', self.script)
        for option in (
            "Professional writing and communication",
            "Evidence and learning",
            "Teaching and mentorship",
            "Leadership and project preparation",
            "Personal organization",
            "Nurse-led entrepreneurship",
            "Concise first",
            "Socratic challenge",
            "Source-first",
            "Reflective coach",
            "Known / Assumed / Unknown / Decide",
            "Assumption ledger",
            "Citation placeholders",
            "Challenge my reasoning",
        ):
            self.assertIn(option, self.page + self.script)

    def test_free_preview_and_formal_personal_edition_boundary_are_explicit(self) -> None:
        for phrase in (
            "$0",
            "No credit card",
            "not the formally activated Personal Edition described in Directive v1.1",
            "not an institutional deployment",
            "does not provide clinical authority",
            "does not connect to employer systems",
            "does not make an AI provider private or compliant",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)
        self.assertNotIn("HIPAA-compliant", self.page)
        self.assertNotIn("protects your license", self.page.casefold())
        self.assertNotIn("institution-ready", self.page.casefold())
        self.assertEqual(1, self.page.count("Personal Edition"))
        self.assertNotIn("Personal Edition", self.page.split("</head>", 1)[0])

    def test_pain_points_are_specific_without_promising_burnout_or_workload_reduction(self) -> None:
        pain = self.page.split('id="np-pain-points"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "You rebuild the same context in every new chat",
            "The answer sounds polished before it is trustworthy",
            "Your prompts work until the stakes change",
            "After-hours work becomes invisible work",
            "Your best method lives in your head",
        ):
            self.assertIn(phrase, pain)
        for overclaim in (
            "reduce burnout",
            "save hours",
            "eliminate documentation",
            "improve patient outcomes",
            "increase revenue",
        ):
            self.assertNotIn(overclaim, self.page.casefold())

    def test_field_note_invitation_is_optional_honest_and_privacy_bounded(self) -> None:
        notes = self.page.split('id="field-notes"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "Optional field note",
            "What I tried",
            "What worked",
            "What failed or felt wrong",
            "What I changed",
            "What I will test next",
            "not a testimonial",
            "does not authorize quotation, attribution, publication, testimonial, or research use",
            "separate, specific consent",
            "Thought leadership begins with an inspectable practice record—not a claim of expertise",
        ):
            self.assertIn(phrase, notes)
        self.assertIn("mailto:robert@nurse-ai-os.org", notes)
        self.assertIn("credential%2C%20secret%2C%20or%20restricted%20information", notes)
        privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("If you send an optional field note", privacy)
        self.assertIn("testimonial use, publication, or research use", privacy)
        self.assertIn("separate, specific consent", privacy)
        self.assertIn("Effective date: July 26, 2026", privacy)

    def test_research_note_is_qualified_and_linked_to_current_sources(self) -> None:
        for url in (
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11339127/",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11534919/",
        ):
            self.assertIn(url, self.page)
        for phrase in (
            "37 purposively selected nurse practitioners",
            "five tertiary institutions in Dhaka, Bangladesh",
            "education and training",
            "ethical and regulatory issues",
            "documentation burden",
            "workflow fragmentation",
            "work outside work",
            "not a U.S. prevalence estimate",
            "do not establish that every NP has the same experience",
            "do not validate this preview",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)

    def test_photorealistic_assets_are_stable_accessible_and_truthfully_labeled(self) -> None:
        images = (
            (
                "assets/img/np-intentional-practice.jpg",
                "Nurse practitioner seated alone in a private office, pausing beside a laptop and notebook.",
            ),
            (
                "assets/img/np-after-hours-fragmentation.jpg",
                "Nurse practitioner working alone at a desk after hours with several blank planning materials.",
            ),
            (
                "assets/img/np-personal-configuration.jpg",
                "Nurse practitioner arranging blank color-coded cards beside a laptop in a private workspace.",
            ),
        )
        for src, alt in images:
            self.assertIn(f'src="{src}"', self.page)
            self.assertIn(f'alt="{alt}"', self.page)
            tag = re.search(rf'<img[^>]+src="{re.escape(src)}"[^>]*>', self.page)
            self.assertIsNotNone(tag, src)
            assert tag is not None
            markup = tag.group(0)
            self.assertIn('width="1344"', markup)
            self.assertIn('height="768"', markup)
            self.assertIn('loading="lazy"', markup)
            asset = ROOT / src
            self.assertTrue(asset.is_file(), src)
            self.assertTrue(asset.read_bytes().startswith(b"\xff\xd8\xff"), src)
        self.assertEqual(3, self.page.count("Synthetic photograph:"))
        self.assertNotIn(".hermes/desktop-attachments", self.page)

    def test_advanced_wings_path_is_late_optional_and_truthful(self) -> None:
        advanced = self.page.split('id="np-advanced-path"', 1)[1].split(
            "</section>", 1
        )[0]
        for phrase in (
            "Optional advanced path",
            "United States only",
            "self-install Hermes build kit",
            "Downloading or unzipping changes nothing",
            "not operational—build required",
            "explicit approval",
            "does not authorize clinical, organizational, billing, legal, prescribing, credentialing, or institutional deployment",
        ):
            self.assertIn(phrase.casefold(), advanced.casefold(), phrase)
        self.assertIn("post-setup/#choose-role", advanced)

    def test_route_is_integrated_without_replacing_current_homepage_audience(self) -> None:
        for surface in (self.pathways, self.ecosystem, self.home):
            self.assertIn('href="nurse-practitioner.html"', surface)
        self.assertIn("For nurse leaders and nurse educators", self.home)
        self.assertIn('href="#workbench"', self.home)
        self.assertIn("Free NP Community Preview", self.pathways)
        self.assertIn("Build your Personal AI Practice Card", self.ecosystem)

    def test_sitemap_ci_shell_and_package_scripts_own_the_route(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        shell = (ROOT / "assets" / "site-shell.js").read_text(encoding="utf-8")
        self.assertEqual(
            1, sitemap.count("https://nurse-ai-os.org/nurse-practitioner.html")
        )
        for path in (
            "assets/nurse-practitioner-funnel.js",
            "assets/img/np-intentional-practice.jpg",
            "assets/img/np-after-hours-fragmentation.jpg",
            "assets/img/np-personal-configuration.jpg",
            "tests/test_nurse_practitioner_funnel.py",
            "tests/test_nurse_practitioner_browser.mjs",
        ):
            self.assertGreaterEqual(self.workflow.count(path), 2, path)
        scanned = self.workflow.split("pages=(", 1)[1]
        for path in (
            "nurse-practitioner.html",
            "assets/nurse-practitioner-funnel.js",
            "pathways.html",
        ):
            self.assertIn(path, scanned)
        self.assertIn('"nurse-practitioner.html": true', shell)
        self.assertIn("test:nurse-practitioner-browser", package)

    def test_schema_accessibility_and_late_language_links_are_complete(self) -> None:
        self.assertIn(
            '<link rel="canonical" href="https://nurse-ai-os.org/nurse-practitioner.html">',
            self.page,
        )
        self.assertIn('<main id="main-content" tabindex="-1">', self.page)
        self.assertIn('class="skip-link" href="#main-content"', self.page)
        self.assertEqual(1, len(re.findall(r"<h1\b", self.page, re.I)))
        self.assertIn('aria-label="Primary navigation"', self.page)
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
        self.assertEqual(
            "https://nurse-ai-os.org/nurse-practitioner.html", schema["url"]
        )
        self.assertTrue(schema["isAccessibleForFree"])

    def test_np_styles_are_responsive_and_scoped(self) -> None:
        for token in (
            ".np-personal-funnel",
            ".np-hero",
            ".np-practice-card-preview",
            ".np-config-grid",
            ".np-pain-grid",
            ".np-photo-grid",
            ".np-provider-boundary",
            ".np-footer-languages",
            "@media (max-width: 620px)",
        ):
            self.assertIn(token, self.css)
        self.assertRegex(
            self.css,
            r"\.np-provider-boundary a\s*\{[^}]*color:\s*var\(--navy-800\)",
        )


if __name__ == "__main__":
    unittest.main()
