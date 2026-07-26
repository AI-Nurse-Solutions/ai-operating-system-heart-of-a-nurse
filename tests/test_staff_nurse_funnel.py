#!/usr/bin/env python3
"""Conversion, privacy, governance, and media contracts for the staff-nurse funnel."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "staff-nurse.html"
SCRIPT = ROOT / "assets" / "staff-nurse-funnel.js"
CSS = ROOT / "assets" / "nurse-ai.css"
PATHWAYS = ROOT / "pathways.html"
ECOSYSTEM = ROOT / "explore-ecosystem.html"
HOME = ROOT / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "website-alignment.yml"


class StaffNurseFunnelTests(unittest.TestCase):
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
        hero = self.page.split('class="staff-hero"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "For staff / bedside nurses",
            "Your shift ends. The mental load does not.",
            "Build my Off-Shift Practice Card",
            "Free Staff Nurse Community Preview — personal use",
            "No account",
            "No download",
            "No patient data",
        ):
            self.assertIn(phrase, hero)
        self.assertNotIn("Take the SOUL Quiz", hero)
        self.assertNotIn("Hermes", hero)
        header = self.page.split("<header", 1)[1].split("</header>", 1)[0]
        self.assertNotIn('class="brand" href=', header)
        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.page, re.I
        )
        self.assertGreaterEqual(len(primary_links), 2)
        self.assertEqual({"#off-shift-card-builder"}, set(primary_links))

    def test_social_preview_uses_absolute_reviewed_image_metadata(self) -> None:
        image_url = "https://nurse-ai-os.org/assets/img/staff-after-shift-pause.jpg"
        self.assertIn(f'<meta property="og:image" content="{image_url}">', self.page)
        self.assertIn(f'<meta name="twitter:image" content="{image_url}">', self.page)
        self.assertIn('<meta property="og:image:width" content="1024">', self.page)
        self.assertIn('<meta property="og:image:height" content="576">', self.page)

    def test_first_use_builder_precedes_pain_media_and_advanced_setup(self) -> None:
        credibility_end = self.page.index("</section>", self.page.index("staff-credibility"))
        builder = self.page.index('id="off-shift-card-builder"')
        pain = self.page.index('id="staff-pain-points"')
        media = self.page.index('class="staff-photo-card"')
        advanced = self.page.index('id="staff-advanced-path"')
        self.assertLess(credibility_end, builder)
        self.assertLess(builder, pain)
        self.assertLess(builder, media)
        self.assertLess(media, advanced)

    def test_builder_is_closed_choice_browser_local_and_provider_boundary_is_adjacent(self) -> None:
        builder = self.page.split('id="off-shift-card-builder"', 1)[1].split(
            "</section>", 1
        )[0]
        for token in (
            'id="staff-focus"',
            'id="staff-energy"',
            'id="staff-style"',
            'id="staff-review"',
            'id="staff-practice-card"',
            'id="copy-staff-practice-card"',
            'aria-live="polite"',
            "stay in this page’s memory",
            "This site does not receive or store them",
            "the content leaves nurse-ai-os.org",
            "privacy, retention, training, account, and data-use settings apply",
            'href="privacy.html"',
        ):
            self.assertIn(token, builder)
        controls = builder.split('<form class="staff-config-panel"', 1)[1].split(
            "</form>", 1
        )[0]
        self.assertNotIn('<input type="text"', controls)
        self.assertNotIn("<textarea", controls)
        self.assertIn('src="assets/staff-nurse-funnel.js"', self.page)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "localStorage",
            "sessionStorage",
            "indexedDB",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_practice_card_front_loads_staff_specific_nonclinical_contract(self) -> None:
        for phrase in (
            "No patient data or PHI",
            "No patient stories, even if names are removed",
            "No colleague, staff, or third-party identifiers",
            "No employer-confidential information, personnel records, schedules, staffing data, incident reports, or restricted organizational material",
            "No credentials, secrets, or restricted records",
            "Do not diagnose, triage, make patient-specific decisions, write chart content, or direct clinical care",
            "Do not make staffing, employment, disciplinary, performance, legal, labor, or regulatory decisions",
            "Do not connect to an EHR, scheduling system, employer system, or clinical workflow",
            "public sources I name or select",
            "Proposed next step",
            "personal-use Draft support",
            "require my human review",
        ):
            self.assertIn(phrase.casefold(), self.script.casefold(), phrase)
        self.assertNotIn("recommend", self.script.casefold())
        self.assertIn("Built into your card", self.page)

    def test_configurator_exposes_four_staff_controls_and_bounded_options(self) -> None:
        for control in ("staff-focus", "staff-energy", "staff-style", "staff-review"):
            self.assertIn(f'id="{control}"', self.page)
            self.assertIn(f'getElementById("{control}")', self.script)
        for option in (
            "After-shift reset",
            "Learning and certification",
            "Portfolio and career growth",
            "Professional communication",
            "Shared-governance preparation",
            "Personal organization",
            "5 minutes · depleted",
            "15 minutes · steady",
            "30 minutes · focused",
            "One step at a time",
            "Direct checklist",
            "Coaching questions first",
            "Source-first",
            "Draft one artifact, then stop",
            "Assumptions and gaps",
            "Human decision checkpoint",
            "Source check before use",
        ):
            self.assertIn(option, self.page + self.script)

    def test_free_preview_and_complete_edition_boundary_are_explicit(self) -> None:
        for phrase in (
            "$0",
            "No credit card",
            "not the Staff Nurse and Quality Contributor Complete Edition",
            "not an activated SHIFT build kit",
            "not an institutional deployment",
            "does not provide clinical, staffing, employment, or organizational authority",
            "does not connect to employer systems",
            "does not make an AI provider private or compliant",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)
        self.assertNotIn("HIPAA-compliant", self.page)
        self.assertNotIn("protects your license", self.page.casefold())
        self.assertNotIn("institution-ready", self.page.casefold())
        self.assertEqual(1, self.page.count("Complete Edition"))
        self.assertNotIn("Complete Edition", self.page.split("</head>", 1)[0])

    def test_pain_points_are_specific_without_outcome_promises(self) -> None:
        pain = self.page.split('id="staff-pain-points"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "Your days off become catch-up days",
            "Professional growth competes with recovery",
            "One ‘quick’ message becomes another hour of context",
            "Generic AI does not know where the bedside boundary is",
            "Your voice in shared governance starts after the shift",
        ):
            self.assertIn(phrase, pain)
        for overclaim in (
            "reduce burnout",
            "prevent burnout",
            "save hours",
            "eliminate documentation",
            "improve patient outcomes",
            "prevent errors",
            "reduce turnover",
            "reclaim your time",
        ):
            self.assertNotIn(overclaim, self.page.casefold())

    def test_evidence_note_is_qualified_and_linked_to_primary_sources(self) -> None:
        for url in (
            "https://www.ncsbn.org/news/ncsbn-research-highlights-small-steps-toward-nursing-workforce-recovery-burnout-and-staffing-challenges-persist",
            "https://www.cdc.gov/niosh/work-hour-training-for-nurses/longhours/mod2/01.html",
            "https://www.nursingworld.org/globalassets/practiceandpolicy/nursing-excellence/ana-position-statements/the-ethical-use-of-artificial-intelligence-in-nursing-practice_bod-approved-12_20_22.pdf",
        ):
            self.assertIn(url, self.page)
        for phrase in (
            "2024 National Nursing Workforce Study",
            "39.9% of RNs",
            "intent to leave the workforce or retire within five years",
            "reducing time for family and non-work responsibilities",
            "adjunct to—not replacements for—nursing knowledge and skill",
            "do not establish that every staff nurse has the same experience",
            "do not validate this preview",
            "do not prove reductions in workload, burnout, fatigue, errors, or turnover",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)

    def test_photorealistic_assets_are_stable_accessible_and_truthfully_labeled(self) -> None:
        images = (
            (
                "assets/img/staff-after-shift-pause.jpg",
                "Staff nurse seated alone in a quiet break room after shift, holding an unmarked mug.",
            ),
            (
                "assets/img/staff-career-growth.jpg",
                "Staff nurse working alone at a home desk with blank cards and unmarked books.",
            ),
            (
                "assets/img/staff-shared-governance-prep.jpg",
                "Staff nurse arranging blank cards alone in an empty meeting room.",
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

    def test_advanced_shift_path_is_late_optional_and_truthful(self) -> None:
        advanced = self.page.split('id="staff-advanced-path"', 1)[1].split(
            "</section>", 1
        )[0]
        for phrase in (
            "Optional advanced path",
            "United States only",
            "self-install Hermes build kit",
            "Downloading or unzipping changes nothing",
            "not operational—build required",
            "all twenty optional SHIFT SuperPowers remain inactive",
            "explicit approval",
            "does not authorize clinical, staffing, employment, quality, legal, labor, or institutional deployment",
        ):
            self.assertIn(phrase.casefold(), advanced.casefold(), phrase)
        self.assertIn("post-setup/#choose-role", advanced)

    def test_route_is_integrated_without_replacing_current_homepage_audience(self) -> None:
        for surface in (self.pathways, self.ecosystem, self.home):
            self.assertIn('href="staff-nurse.html"', surface)
        self.assertIn("For nurse leaders and nurse educators", self.home)
        self.assertIn('href="#workbench"', self.home)
        self.assertIn("Free Staff Nurse Community Preview", self.pathways)
        self.assertIn("Build your Off-Shift Practice Card", self.ecosystem)

    def test_sitemap_ci_shell_and_package_scripts_own_the_route(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        shell = (ROOT / "assets" / "site-shell.js").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/staff-nurse.html"))
        for path in (
            "assets/staff-nurse-funnel.js",
            "assets/img/staff-after-shift-pause.jpg",
            "assets/img/staff-career-growth.jpg",
            "assets/img/staff-shared-governance-prep.jpg",
            "tests/test_staff_nurse_funnel.py",
            "tests/test_staff_nurse_browser.mjs",
        ):
            self.assertGreaterEqual(self.workflow.count(path), 2, path)
        scanned = self.workflow.split("pages=(", 1)[1]
        for path in (
            "staff-nurse.html",
            "assets/staff-nurse-funnel.js",
            "pathways.html",
        ):
            self.assertIn(path, scanned)
        self.assertIn('"staff-nurse.html": true', shell)
        self.assertIn("test:staff-nurse-browser", package)

    def test_schema_accessibility_and_late_language_links_are_complete(self) -> None:
        self.assertIn(
            '<link rel="canonical" href="https://nurse-ai-os.org/staff-nurse.html">',
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
        self.assertEqual("https://nurse-ai-os.org/staff-nurse.html", schema["url"])
        self.assertTrue(schema["isAccessibleForFree"])

    def test_staff_styles_are_responsive_and_scoped(self) -> None:
        for token in (
            ".staff-nurse-funnel",
            ".staff-hero",
            ".staff-practice-card-preview",
            ".staff-focus-grid",
            ".staff-pain-grid",
            ".staff-photo-grid",
            ".staff-provider-boundary",
            ".staff-footer-languages",
            "@media (max-width: 620px)",
        ):
            self.assertIn(token, self.css)
        self.assertRegex(
            self.css,
            r"\.staff-provider-boundary a\s*\{[^}]*color:\s*var\(--navy-800\)",
        )


if __name__ == "__main__":
    unittest.main()
