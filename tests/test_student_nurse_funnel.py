#!/usr/bin/env python3
"""Conversion, learning-integrity, privacy, and governance contracts for the student funnel."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "student-nurse.html"
SCRIPT = ROOT / "assets" / "student-nurse-funnel.js"
CSS = ROOT / "assets" / "nurse-ai.css"
PATHWAYS = ROOT / "pathways.html"


class StudentNurseFunnelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
        cls.script = SCRIPT.read_text(encoding="utf-8") if SCRIPT.exists() else ""
        cls.css = CSS.read_text(encoding="utf-8")
        cls.pathways = PATHWAYS.read_text(encoding="utf-8")

    def test_route_names_one_audience_literal_outcome_and_primary_action(self) -> None:
        self.assertTrue(PAGE.is_file())
        hero = self.page.split('class="student-nurse-hero"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "For student nurses",
            "Turn one confusing nursing topic into a study map—without handing over the thinking.",
            "Get the study-map prompt",
            "Tutor, never crutch",
            "School policy controls",
        ):
            self.assertIn(phrase, hero)
        for overclaim in ("five-minute", "five minutes", "Build a 5-minute study map"):
            self.assertNotIn(overclaim.casefold(), self.page.casefold())
        self.assertNotIn("Take the SOUL Quiz", hero)
        self.assertNotIn("Hermes", hero)
        header = self.page.split("<header", 1)[1].split("</header>", 1)[0]
        self.assertNotIn('class="brand" href=', header)

        primary_links = re.findall(
            r'<a class="btn btn-primary" href="([^"]+)"', self.page, re.I
        )
        self.assertGreaterEqual(len(primary_links), 2)
        self.assertEqual({"#study-workbench"}, set(primary_links))

    def test_workbench_is_the_first_post_credibility_value_section(self) -> None:
        credibility_end = self.page.index("</section>", self.page.index("leader-credibility"))
        workbench = self.page.index('id="study-workbench"')
        alternatives = self.page.index('id="other-workflows"')
        how_it_works = self.page.index('id="how-it-works"')
        self.assertLess(credibility_end, workbench)
        self.assertLess(workbench, alternatives)
        self.assertLess(alternatives, how_it_works)
        between = self.page[credibility_end:workbench]
        self.assertNotIn("student-task-grid", between)
        self.assertIn("<details", self.page[alternatives:how_it_works])

    def test_workbench_is_browser_local_and_provider_boundary_is_adjacent(self) -> None:
        workbench = self.page.split('id="study-workbench"', 1)[1].split(
            "</section>", 1
        )[0]
        for token in (
            'id="student-task"',
            'id="student-prompt"',
            'id="copy-student-workflow"',
            'aria-live="polite"',
            "Your task choice and generated prompt stay in this page’s memory",
            "the content leaves nurse-ai-os.org",
            "privacy, retention, training, account, and data-use settings apply",
            'href="privacy.html"',
        ):
            self.assertIn(token, workbench)
        self.assertIn('src="assets/student-nurse-funnel.js"', self.page)
        self.assertNotIn("fonts.googleapis.com", self.page)
        self.assertNotIn("fonts.gstatic.com", self.page)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "localStorage",
            "sessionStorage",
            "indexedDB",
        ):
            self.assertNotIn(forbidden, self.script)

    def test_all_six_prompts_front_load_the_same_draft_only_safety_contract(self) -> None:
        tasks = (
            "student-study-map",
            "student-socratic",
            "student-week-plan",
            "student-exam-review",
            "student-clinical-reflection",
            "student-integrity-check",
        )
        for task in tasks:
            self.assertIn(task, self.script)
        self.assertEqual(6, self.script.count("prompt: safetyContract +"))
        for phrase in (
            "No patient data",
            "No student-identifying data",
            "Do not answer graded work",
            "Do not make clinical decisions",
            "Draft-only learning support",
            "stop and ask faculty",
            "Mark claims that need verification",
            "human review",
        ):
            self.assertIn(phrase.casefold(), self.script.casefold(), phrase)
        self.assertIn("Built into every prompt", self.page)

    def test_prompts_do_not_rank_priorities_grant_permission_or_unlock_answers(self) -> None:
        for forbidden in (
            "Clearly Allowed Based on What I Provided",
            "Do not reveal a complete answer unless",
            "prioritized review table",
            "plan that prioritizes",
            "stop/go checklist",
        ):
            self.assertNotIn(forbidden.casefold(), self.script.casefold(), forbidden)
        for required in (
            "Preserve my priority order; do not rank",
            "Never decide or label the use as allowed, approved, compliant, or prohibited",
            "Policy Points I Reported—Not Independently Verified",
            "Never provide submit-ready prose",
        ):
            self.assertIn(required.casefold(), self.script.casefold(), required)

    def test_clipboard_paths_are_fail_safe_and_have_executable_regression_coverage(self) -> None:
        self.assertIn('typeof document.execCommand !== "function"', self.script)
        self.assertIn("catch (error)", self.script)
        self.assertIn("Automatic copy was blocked", self.script)
        browser_test = ROOT / "tests" / "test_student_nurse_browser.mjs"
        self.assertTrue(browser_test.is_file())
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        self.assertIn("test:student-nurse-browser", package)

    def test_linked_student_pathway_is_current_bounded_and_non_launched(self) -> None:
        student_section = self.pathways.split('id="student"', 1)[1].split(
            'id="staff"', 1
        )[0]
        for phrase in (
            "Get the student study prompt",
            "Draft-only learning support",
            "Concepts—not launched products",
            "no launch date",
            "no active clinical workflow",
            "no-PHI",
        ):
            self.assertIn(phrase.casefold(), student_section.casefold(), phrase)
        for forbidden in (
            "Coming July 27",
            "aggregated friction themes",
            "SBAR handoff helper",
            "Get notified at launch",
            "You cannot break this",
            "roadmap-student.jpg",
            "assets/30-day-roadmap.pdf",
            "School / program",
        ):
            self.assertNotIn(forbidden.casefold(), student_section.casefold(), forbidden)

    def test_first_value_precedes_personalization_download_and_optional_setup(self) -> None:
        workbench = self.page.index('id="study-workbench"')
        progression = self.page.index('id="student-progression"')
        soul = self.page.index('href="soul-quiz.html"')
        starter = self.page.index('href="assets/nurse-ai-os-starter-kit.zip"')
        advanced = self.page.index("student-advanced-setup")
        self.assertLess(workbench, progression)
        self.assertLess(workbench, soul)
        self.assertLess(workbench, starter)
        self.assertLess(progression, advanced)
        for phrase in (
            "Visitor",
            "Learner",
            "Steward",
            "Downloading or unzipping changes nothing",
            "See the optional advanced setup",
        ):
            self.assertIn(phrase, self.page)
        for jargon in (
            "Implementation Activation Card",
            "capability-gated",
            "formal gate",
            "Florence-X",
            "EDENA",
            "governed FUTURE",
            "D0/D1",
        ):
            self.assertNotIn(jargon.casefold(), self.page.casefold(), jargon)

    def test_academic_integrity_and_authority_boundaries_are_visible(self) -> None:
        for phrase in (
            "Academic integrity",
            "Never submit AI output as your own work",
            "Follow your syllabus, instructor guidance, and school AI policy",
            "No patient names, charts, screenshots, or clinical records",
            "does not replace faculty, preceptors, approved sources, or your judgment",
            "does not decide what is clinically correct",
            "This page and AI do not decide whether AI use is allowed",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)
        self.assertNotIn("clinical-ready", self.page.casefold())
        self.assertNotIn("guarantee", self.page.casefold())
        self.assertNotIn("testimonial", self.page.casefold())

    def test_proof_is_truthfully_labeled_as_structure_not_effectiveness(self) -> None:
        self.assertNotIn("roadmap-student.jpg", self.page)
        self.assertNotIn("AI handles the data and busywork", self.page)
        self.assertNotIn("<iframe", self.page)
        for phrase in (
            "What the prompt asks for",
            "expected output structure",
            "not evidence of improved grades or learning outcomes",
            "You do the thinking",
        ):
            self.assertIn(phrase.casefold(), self.page.casefold(), phrase)

    def test_student_illustrations_are_stable_accessible_and_truthfully_labeled(self) -> None:
        images = (
            (
                "assets/img/student-recall-study-map.jpg",
                "Illustration of a nursing student writing from memory beside an unlabeled concept map on a laptop.",
            ),
            (
                "assets/img/student-source-verification.jpg",
                "Illustration of a student comparing an abstract laptop draft with open study materials and marking corrections by hand.",
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
        self.assertEqual(self.page.count("Synthetic illustration:"), 2)
        self.assertNotIn(".hermes/desktop-attachments", self.page)

    def test_route_is_discoverable_without_changing_homepage_audience(self) -> None:
        ecosystem = (ROOT / "explore-ecosystem.html").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="student-nurse.html"', self.pathways)
        self.assertIn('href="student-nurse.html"', ecosystem)
        self.assertIn('href="student-nurse.html"', home)
        self.assertIn("Get the student study prompt", ecosystem)
        self.assertNotIn("studying takes less of your life", ecosystem)
        self.assertIn("For nurse leaders and nurse educators", home)
        self.assertIn('href="#workbench"', home)
        self.assertNotIn('href="resources.html"', self.page)

    def test_sitemap_ci_and_public_scanner_own_route_prompts_and_pathway(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "website-alignment.yml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            1, sitemap.count("https://nurse-ai-os.org/student-nurse.html")
        )
        self.assertEqual(2, workflow.count('"**/*.html"'))
        for path in (
            "assets/student-nurse-funnel.js",
            "assets/img/student-recall-study-map.jpg",
            "assets/img/student-source-verification.jpg",
            "tests/test_student_nurse_funnel.py",
            "tests/test_student_nurse_browser.mjs",
        ):
            self.assertGreaterEqual(workflow.count(path), 2, path)
        scanned = workflow.split("pages=(", 1)[1]
        for path in ("student-nurse.html", "assets/student-nurse-funnel.js", "pathways.html"):
            self.assertIn(path, scanned)

    def test_schema_accessibility_metadata_and_late_language_links_are_complete(self) -> None:
        self.assertIn(
            '<link rel="canonical" href="https://nurse-ai-os.org/student-nurse.html">',
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
        self.assertEqual("https://nurse-ai-os.org/student-nurse.html", schema["url"])
        self.assertTrue(schema["isAccessibleForFree"])

    def test_student_styles_are_responsive_and_scoped(self) -> None:
        for token in (
            ".student-nurse-funnel",
            ".student-nurse-hero-grid",
            ".student-proof-card",
            ".student-prompt-safety",
            ".student-provider-boundary",
            ".student-task-catalog",
            ".student-integrity-grid",
            ".student-footer-languages",
            "@media (max-width: 620px)",
        ):
            self.assertIn(token, self.css)


if __name__ == "__main__":
    unittest.main()
