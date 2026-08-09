#!/usr/bin/env python3
"""Publication and governance contracts for the LM Studio Bionic options guide."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "guides" / "nurse-ai-os-lm-studio-bionic" / "index.html"
HOME = ROOT / "index.html"
RESOURCES = ROOT / "resources.html"
SITEMAP = ROOT / "sitemap.xml"
CSS = ROOT / "assets" / "nurse-ai.css"
WORKFLOW = ROOT / ".github" / "workflows" / "website-alignment.yml"


class LmStudioBionicGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else ""
        cls.home = HOME.read_text(encoding="utf-8")
        cls.resources = RESOURCES.read_text(encoding="utf-8")
        cls.sitemap = SITEMAP.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_guide_is_a_separate_canonical_public_page(self) -> None:
        self.assertTrue(GUIDE.is_file())
        for token in (
            "<!DOCTYPE html>",
            '<html lang="en">',
            "Run Nurse AI OS Privately with LM Studio Bionic",
            'name="description"',
            'rel="canonical" href="https://nurse-ai-os.org/guides/nurse-ai-os-lm-studio-bionic/"',
            'class="skip-link" href="#main-content"',
            '<main id="main-content" tabindex="-1">',
            '<nav class="nav-bar" aria-label="Primary navigation">',
        ):
            self.assertIn(token, self.guide)

    def test_homepage_nav_restores_requested_routes_without_redundant_anchors(self) -> None:
        nav = self.home.split('<div class="nav-links">', 1)[1].split("</div>", 1)[0]
        for href in (
            "explore-ecosystem.html",
            "resources.html",
            "about.html",
            "https://hermes-agent.nousresearch.com/",
            "soul-quiz.html",
        ):
            self.assertEqual(1, nav.count(f'href="{href}"'), href)
        self.assertNotIn('href="#leader-walkthrough"', nav)
        self.assertNotIn('href="#workbench"', nav)
        self.assertEqual(1, nav.count('class="nav-cta"'))

    def test_resources_and_sitemap_own_the_guide_route(self) -> None:
        self.assertEqual(1, self.resources.count('href="guides/nurse-ai-os-lm-studio-bionic/"'))
        self.assertIn("Private &amp; on-premises AI options", self.resources)
        self.assertIn("LM Link preview", self.resources)
        self.assertEqual(
            1,
            self.sitemap.count("https://nurse-ai-os.org/guides/nurse-ai-os-lm-studio-bionic/"),
        )
        for route in (
            "https://nurse-ai-os.org/",
            "https://nurse-ai-os.org/resources.html",
            "https://nurse-ai-os.org/guides/nurse-ai-os-lm-studio-bionic/",
        ):
            self.assertRegex(
                self.sitemap,
                rf"<loc>{re.escape(route)}</loc><lastmod>\d{{4}}-\d{{2}}-\d{{2}}</lastmod>",
            )

    def test_public_safety_workflow_scans_the_nested_guide_route(self) -> None:
        scanner_pages = self.workflow.split("pages=(", 1)[1].split(")", 1)[0]
        guide_path = "guides/nurse-ai-os-lm-studio-bionic/index.html"
        self.assertEqual(1, scanner_pages.count(guide_path))
        self.assertEqual(2, self.workflow.count('- "**/*.html"'))

    def test_three_paths_are_distinct_and_cloud_is_not_called_on_premises(self) -> None:
        for phrase in (
            "Local on this computer",
            "Remote through LM Link",
            "LM Studio Secure Cloud",
            "LM Link is in preview",
            "Secure Cloud is hosted processing, not on-premises processing",
            "Zero Data Retention",
        ):
            self.assertIn(phrase, self.guide)
        self.assertNotRegex(
            self.guide,
            re.compile(r"Secure Cloud.{0,80}(?:is|as) on-premises", re.I | re.S),
        )

    def test_implementation_and_healthcare_boundaries_are_explicit(self) -> None:
        for phrase in (
            "does not install, connect, activate, or authorize anything",
            "Nurse AI OS is not automatically connected to Bionic, LM Studio, or LM Link",
            "Bionic is a separate application from the standard LM Studio app",
            "does not by itself make a system HIPAA-compliant",
            "No PHI",
            "not permission to send PHI",
            "business associate agreement",
            "security, legal, privacy, procurement, and governance review",
            "no autonomous diagnosis, triage, treatment, or charting",
            "does not determine competence, grading, hiring, discipline, credentialing, or clinical authority",
            "human review",
            "institutional deployment requires separate approval",
        ):
            self.assertIn(phrase.casefold(), self.guide.casefold(), phrase)

    def test_page_contains_practical_decision_and_pilot_sections(self) -> None:
        for heading in (
            "Choose the model path before the model",
            "Three small-scale patterns",
            "Use cases that fit a bounded pilot",
            "Do not use this path for",
            "Prepare the environment",
            "Pilot launch checklist",
            "Start with one low-risk workflow",
            "Primary sources",
        ):
            self.assertIn(heading, self.guide)
        self.assertIn("http://localhost:1234", self.guide)
        self.assertIn('type="checkbox" disabled', self.guide)
        self.assertIn('class="guide-table-wrap"', self.guide)
        self.assertGreaterEqual(self.guide.count('scope="col"'), 4)

    def test_primary_source_links_are_present_and_external_links_are_safe(self) -> None:
        required = (
            "https://lmstudio.ai/docs/bionic",
            "https://lmstudio.ai/docs/bionic/models",
            "https://lmstudio.ai/link",
            "https://lmstudio.ai/docs/app/offline",
            "https://lmstudio.ai/docs/lmlink/basics/faq",
            "https://lmstudio.ai/docs/developer/core/lmlink",
            "https://lmstudio.ai/blog/introducing-lm-studio-bionic",
            "https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html",
            "https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html",
        )
        for url in required:
            self.assertIn(f'href="{url}"', self.guide)
        external = re.findall(r'<a\b[^>]*href="https://[^"]+"[^>]*>', self.guide)
        self.assertGreaterEqual(len(external), len(required))
        for anchor in external:
            self.assertIn('target="_blank"', anchor)
            self.assertIn('rel="noopener"', anchor)

    def test_styles_are_scoped_responsive_and_overflow_safe(self) -> None:
        for selector in (
            "body.local-ai-guide",
            ".guide-path-grid",
            ".guide-table-wrap",
            ".guide-checklist",
            ".guide-source-list",
        ):
            self.assertIn(selector, self.css)
        self.assertIn("overflow-x: auto", self.css)
        self.assertIn("@media (max-width: 760px)", self.css)


if __name__ == "__main__":
    unittest.main()
