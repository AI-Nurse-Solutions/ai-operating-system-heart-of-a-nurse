#!/usr/bin/env python3
"""Conversion and governance contracts for the leader/educator front door."""

from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
ECOSYSTEM = ROOT / "explore-ecosystem.html"
SCRIPT = ROOT / "assets" / "leader-educator-home.js"
CSS = ROOT / "assets" / "nurse-ai.css"
HERO_IMAGE = ROOT / "assets" / "nurse-leader-planning.jpg"
FOUNDER_IMAGE = ROOT / "assets" / "robert-domondon-founder.jpg"


class HomepageMediaParser(HTMLParser):
    """Collect figure class tokens and image attributes from homepage HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.figure_classes: list[set[str]] = []
        self.images: dict[str, dict[str, str | None]] = {}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "figure":
            self.figure_classes.append(set((attributes.get("class") or "").split()))
        elif tag == "img":
            source = attributes.get("src")
            if source is not None:
                self.images[source] = attributes


class LeaderEducatorHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.home = HOME.read_text(encoding="utf-8")
        cls.ecosystem = ECOSYSTEM.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
        cls.css = CSS.read_text(encoding="utf-8")

    def test_front_door_names_one_audience_and_one_immediate_outcome(self) -> None:
        hero = self.home.split('class="leader-educator-hero"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "For nurse leaders and nurse educators",
            "Get one leadership or teaching task off your plate in five minutes.",
            "Try a 5-minute workflow",
            "No patient data",
            "You review every result",
        ):
            self.assertIn(phrase, hero)
        self.assertNotIn("Take the SOUL Quiz", hero)
        self.assertNotIn("Hermes", hero)

    def test_primary_action_is_the_workbench_and_is_repeated(self) -> None:
        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.home, re.I
        )
        self.assertGreaterEqual(len(primary_links), 2)
        self.assertEqual({"#workbench"}, set(primary_links))
        nav = self.home.split('<div class="nav-links">', 1)[1].split("</div>", 1)[0]
        self.assertEqual(1, nav.count('class="nav-cta"'))
        self.assertIn('href="#workbench"', nav)

    def test_workbench_is_real_browser_local_functionality(self) -> None:
        for token in (
            'id="workflow-role"',
            'id="workflow-task"',
            'id="workflow-prompt"',
            'id="copy-workflow"',
            'aria-live="polite"',
            'src="assets/leader-educator-home.js"',
        ):
            self.assertIn(token, self.home)
        for task in (
            "leader-huddle",
            "leader-meeting",
            "leader-improvement",
            "educator-lesson",
            "educator-discussion",
            "educator-rubric",
        ):
            self.assertIn(task, self.script)
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage"):
            self.assertNotIn(forbidden, self.script)
        self.assertIn("navigator.clipboard.writeText", self.script)
        self.assertIn("No patient data", self.script)
        self.assertIn("human review", self.script)
        self.assertIn('taskSelect.textContent = ""', self.script)
        self.assertIn("copyButton.focus()", self.script)

    def test_workbench_retains_a_safe_no_javascript_default(self) -> None:
        workbench = self.home.split('id="workbench"', 1)[1].split("</section>", 1)[0]
        for token in (
            '<option value="leader-huddle">',
            '<option value="leader-meeting">',
            '<option value="leader-improvement">',
            "You are my drafting assistant for a 15-minute staff huddle.",
            "<noscript>",
            "the default staff-huddle workflow remains available to copy",
        ):
            self.assertIn(token, workbench)

    def test_first_value_precedes_personalization_and_download(self) -> None:
        workbench = self.home.index('id="workbench"')
        progression = self.home.index('id="progression"')
        soul = self.home.index('href="soul-quiz.html"')
        starter = self.home.index('href="assets/nurse-ai-os-starter-kit.zip"')
        self.assertLess(workbench, progression)
        self.assertLess(workbench, soul)
        self.assertLess(workbench, starter)
        for phrase in ("Visitor", "User", "Steward", "Visitors try", "Users keep", "Stewards shape"):
            self.assertIn(phrase, self.home)

    def test_supplied_images_replace_only_the_image_placeholders(self) -> None:
        parser = HomepageMediaParser()
        parser.feed(self.home)
        placeholder_figures = [
            classes
            for classes in parser.figure_classes
            if "media-placeholder" in classes
        ]
        self.assertEqual(
            [{"media-placeholder", "media-placeholder-video"}],
            placeholder_figures,
        )
        self.assertIn("45-second demonstration video placeholder", self.home)
        self.assertIn("Asset needed: real workflow from selection through human review.", self.home)
        self.assertNotIn("Hero image placeholder", self.home)
        self.assertNotIn("Robert Domondon portrait placeholder", self.home)
        for image, source, expected_attributes in (
            (
                HERO_IMAGE,
                "assets/nurse-leader-planning.jpg",
                {
                    "width": "625",
                    "height": "390",
                    "alt": "A nurse leader prepares a presentation with a tablet in front of a data dashboard.",
                    "decoding": "async",
                    "fetchpriority": "high",
                },
            ),
            (
                FOUNDER_IMAGE,
                "assets/robert-domondon-founder.jpg",
                {
                    "width": "720",
                    "height": "900",
                    "alt": "Robert Domondon, ICU nurse and founder of Nurse AI OS, holding a tablet.",
                    "loading": "lazy",
                    "decoding": "async",
                },
            ),
        ):
            self.assertTrue(image.is_file())
            self.assertGreater(image.stat().st_size, 10_000)
            self.assertLess(image.stat().st_size, 200_000)
            self.assertIn(source, parser.images)
            image_attributes = parser.images[source]
            self.assertEqual(source, image_attributes["src"])
            for attribute, expected in expected_attributes.items():
                self.assertEqual(expected, image_attributes.get(attribute))
        self.assertNotIn("<iframe", self.home)
        self.assertNotIn("testimonial", self.home.casefold())
        self.assertNotIn("measured nurse outcomes", self.home.casefold())

    def test_current_ecosystem_page_is_preserved_and_discoverable(self) -> None:
        self.assertTrue(ECOSYSTEM.is_file())
        self.assertIn("Explore the Nurse AI OS Ecosystem", self.ecosystem)
        self.assertIn("The Steward\u2019s Charter", self.ecosystem)
        self.assertIn("<!-- ============ HOMEPAGE SHORT ============ -->", self.ecosystem)
        self.assertIn('href="explore-ecosystem.html"', self.home)
        self.assertIn("https://www.youtube-nocookie.com/embed/", self.ecosystem)
        self.assertIn('title="Nurse AI OS — watch" loading="lazy"', self.ecosystem)
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/explore-ecosystem.html"))

    def test_legacy_ecosystem_deep_links_follow_the_preserved_page(self) -> None:
        expected_links = {
            "setup.html": "explore-ecosystem.html#how-it-works",
            "start-here.html": "explore-ecosystem.html#how-it-works",
            "hermes-downloads/index.html": "../explore-ecosystem.html#how-it-works",
            "pathways.html": "explore-ecosystem.html#founding-year",
            "hermes-masterclass.html": "explore-ecosystem.html#founding-year",
            "ai-mentors.html": "explore-ecosystem.html#community",
        }
        for relative_path, link in expected_links.items():
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(f'href="{link}"', text, relative_path)

        retired = (
            'href="index.html#how-it-works"',
            'href="../index.html#how-it-works"',
            'href="index.html#founding-year"',
            'href="index.html#community"',
        )
        for relative_path in expected_links:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            for link in retired:
                self.assertNotIn(link, text, relative_path)

    def test_directive_maturity_and_product_boundaries_remain_visible(self) -> None:
        for phrase in (
            "governed professional environment",
            "Available now",
            "Capability-gated",
            "Formal-gate programs",
            "not an EHR",
            "not an autonomous clinician",
            "You do not need Hermes to begin",
            "Downloading the ZIP does not install or activate anything",
            'href="directive.html"',
        ):
            self.assertIn(phrase.casefold(), self.home.casefold(), phrase)

    def test_operator_schema_and_accessibility_landmarks_are_preserved(self) -> None:
        blocks = re.findall(
            r'<script\b(?=[^>]*\btype=["\']application/ld\+json["\'])[^>]*>\s*(.*?)\s*</script>',
            self.home,
            re.DOTALL | re.IGNORECASE,
        )
        graph = []
        for block in blocks:
            payload = json.loads(block)
            graph.extend(payload.get("@graph", [payload]))
        operator = [node for node in graph if node.get("@id") == "https://nurse-ai-os.org/#operator"]
        websites = [node for node in graph if node.get("@type") == "WebSite"]
        self.assertEqual(1, len(operator))
        self.assertEqual(1, len(websites))
        self.assertEqual({"@id": "https://nurse-ai-os.org/#operator"}, websites[0]["publisher"])
        for token in (
            'class="skip-link" href="#main-content"',
            '<main id="main-content" tabindex="-1">',
            '<nav class="nav-bar" aria-label="Primary navigation">',
            '<fieldset>',
            '<legend>',
        ):
            self.assertIn(token, self.home)
        for selector in (
            ".leader-educator-hero",
            ".workflow-workbench",
            ".media-placeholder",
            ".progression-grid",
        ):
            self.assertIn(selector, self.css)


if __name__ == "__main__":
    unittest.main()
