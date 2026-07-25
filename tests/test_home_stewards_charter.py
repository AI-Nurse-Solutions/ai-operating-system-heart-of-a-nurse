#!/usr/bin/env python3
"""Homepage product clarity, doctrine placement, scope, and accessibility checks."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
CSS = ROOT / "assets" / "nurse-ai.css"

MANDATORY_HERMES_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:must|required to|need to)\s+(?:download|install|use)\s+hermes\b",
        r"\byou\s+(?:are\s+)?required\s+to\s+(?:download|install|use)\s+hermes\b",
        r"\bhermes\s+(?:must|needs? to|is required to)\s+be\s+(?:downloaded|installed|used)\b",
        r"\bhermes\s+is\s+(?:required|mandatory)\b",
        r"\b(?:download|install|use)\s+hermes\s+(?:first|before)\b",
        r"\b(?:to|before you)\s+begin[^.]{0,40}\b(?:download|install|use)\b[^.]{0,20}\bhermes\b",
        r"\b(?:starting|getting started|beginning)\s+requires?\s+hermes\b",
    )
)

MATURITY_OVERCLAIM_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:already|currently|now)\s+enforces?\s+(?:every|all)\s+polic(?:y|ies)\s+(?:uniformly\s+)?across\b",
        r"\b(?:grants?|gives?|provides?|confers?)\b[^.]{0,80}\b(?:clinical|institutional)\b[^.]{0,30}\bauthority\b",
        r"\b(?:is|offers?|provides?)\s+(?:already\s+|now\s+|currently\s+)?(?:a\s+)?(?:complete|finished|fully enforceable)\s+standalone\s+(?:operating system|os)\b",
        r"\bchatgpt\b[^.]{0,80}\bclaude\b[^.]{0,80}\bhermes\b[^.]{0,100}\b(?:enforce|enforces|enforced)\b[^.]{0,40}\b(?:identically|uniformly|the same way)\b",
        r"\b(?:same|all|every)\s+polic(?:y|ies)\b[^.]{0,40}\b(?:is|are)\s+enforced\b[^.]{0,40}\b(?:every|all)\s+(?:host\s+)?(?:ai|tool)\b",
    )
)


def mandatory_hermes_claims(text: str) -> list[str]:
    """Return mandatory-Hermes phrases found in browser-first product copy."""
    return [match.group(0) for pattern in MANDATORY_HERMES_PATTERNS for match in pattern.finditer(text)]


def maturity_overclaims(text: str) -> list[str]:
    """Return claims that collapse developing or future capability into current fact."""
    return [match.group(0) for pattern in MATURITY_OVERCLAIM_PATTERNS for match in pattern.finditer(text)]


class HomeStewardsCharterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.home = HOME.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github" / "workflows" / "home-stewards-charter.yml").read_text(encoding="utf-8")

    def test_product_explanation_is_immediately_below_hero_before_charter(self) -> None:
        hero_end = self.home.index("</section>", self.home.index('class="hero"'))
        product = self.home.index('id="what-it-is"')
        charter = self.home.index('id="stewards-charter"')
        video = self.home.index("<!-- ============ HOMEPAGE SHORT ============ -->")
        self.assertLess(hero_end, product)
        self.assertLess(product, charter)
        self.assertLess(charter, video)
        product_section_start = self.home.rfind("<section", hero_end, product)
        between = self.home[hero_end:product_section_start]
        self.assertNotIn("<section", between)

    def test_hero_plainly_names_the_no_install_product(self) -> None:
        hero = self.home.split('class="hero"', 1)[1].split("</section>", 1)[0]
        required = (
            "A nurse-designed way to use the AI you already have",
            "Use ChatGPT or Claude with a nurse-built kit.",
            "guided prompts, practical templates, a local folder system, and a personal values-and-boundaries file",
            "Start in your browser—no new app or workplace connection required.",
            "No patient data.",
            "Hermes is optional later",
            "Free for nurses and nursing students during the 2026 founding year.",
        )
        for phrase in required:
            self.assertIn(phrase, hero)
        self.assertNotIn("personal AI assistant for your life", hero)

    def test_product_explanation_precedes_charter_and_names_privacy_boundary(self) -> None:
        charter = self.home.index('id="stewards-charter"')
        product = self.home.index('id="what-it-is"')
        self.assertLess(product, charter)
        product_region = self.home[product:charter]
        for phrase in (
            "A kit for the AI you already have, not a new chatbot.",
            "Your SOUL file",
            "Your workflow kit",
            "Your safety rules",
            "You do not need Hermes to begin.",
            "free, open-source desktop AI agent from Nous Research",
            "Files in the Starter Kit stay on your device unless you choose to paste or upload them",
            "handled under that provider's privacy and data settings",
            'href="#how-it-works">See the no-install steps →</a>',
        ):
            self.assertIn(phrase, product_region)

    def test_os_name_is_bounded_by_today_emerging_and_direction(self) -> None:
        product = self.home.index('id="what-it-is"')
        charter = self.home.index('id="stewards-charter"')
        product_region = self.home[product:charter]
        required = (
            "Why call it an OS?",
            "Today · The practical product",
            "primarily a sophisticated configuration and workflow package for AI tools you already have",
            "Emerging · The technical layer",
            "real policy artifacts, schemas, tests, verification systems, evidence controls, and Florence-X orchestration components",
            "they do not create uniform enforcement inside every host AI today",
            "Direction · The fuller OS",
            "a portable, enforceable, nurse-governed control layer for AI work",
            "It is not yet a finished standalone operating system.",
        )
        for phrase in required:
            self.assertIn(phrase, product_region)

        self.assertEqual([], maturity_overclaims(self.home))
        adversarial_probes = (
            "Nurse AI OS already enforces every policy uniformly across ChatGPT, Claude, and Hermes and grants nurses clinical and institutional authority.",
            "Nurse AI OS is already a finished standalone OS.",
            "ChatGPT, Claude, and Hermes all enforce the governance layer identically.",
            "The same policies are enforced in every host AI.",
        )
        for probe in adversarial_probes:
            self.assertTrue(maturity_overclaims(probe), probe)

    def test_core_setup_is_browser_first_and_hermes_is_last_and_optional(self) -> None:
        setup = self.home.split('id="how-it-works"', 1)[1].split("</section>", 1)[0]
        soul = setup.index("Take the SOUL Quiz")
        browser = setup.index("Open ChatGPT or Claude")
        starter = setup.index("Download the Starter Kit")
        workflow = setup.index("Run one useful workflow")
        hermes = setup.index("Optional: add Hermes later")
        self.assertEqual([soul, browser, starter, workflow, hermes], sorted([soul, browser, starter, workflow, hermes]))
        self.assertIn("The core setup works in ChatGPT or Claude.", setup)
        self.assertIn("not because Nurse AI OS requires it", setup)
        self.assertIn('href="assets/nurse-ai-os-starter-kit.zip"', setup)
        starting_prompt = "This is my personal values-and-boundaries file. Use it as context for this conversation. Tell me what you understood about what matters to me, how I want help, and what I will never delegate. I will correct anything you misunderstood."
        first_workflow_prompt = "Ask me one question: “What is the one personal, learning, or career task weighing on you today?” Then suggest three specific ways you can help me plan, organize, draft, or learn. Do not use patient data or make clinical decisions. Wait for me to choose."
        self.assertIn(starting_prompt, setup)
        self.assertIn(first_workflow_prompt, setup)
        self.assertNotIn('href="start-here.html"', setup)

        core = (self.home[self.home.index('id="what-it-is"'):self.home.index('id="stewards-charter"')] + setup).lower()
        self.assertEqual([], mandatory_hermes_claims(core))

        adversarial_probes = (
            "Hermes must be installed before you begin.",
            "You are required to use Hermes.",
            "To begin, download and install Hermes.",
            "Starting requires Hermes.",
        )
        for probe in adversarial_probes:
            self.assertTrue(mandatory_hermes_claims(probe), probe)

    def test_homepage_avoids_autonomous_and_false_privacy_promises(self) -> None:
        forbidden = (
            "personal AI assistant for your life",
            "private folder system",
            "personal AI operating system",
            "certification plan runs itself",
            "rules that protect your license and your patients",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, self.home)

    def test_charter_preserves_foundational_doctrine_and_commitment(self) -> None:
        required = (
            "The Steward’s Charter",
            "Why Nurse AI OS Exists",
            "The question is what kind of nurses we choose to become because of it.",
            "technology should strengthen human judgment, never replace it.",
            "No algorithm carries that responsibility. No machine holds a license. No model bears moral accountability.",
            "Agents propose. Humans judge. Nurses steward.",
            "Nurses should not merely adapt to the future. We should help build it.",
            "We intend to become them.",
            "Where Nightingale meets neural net.",
        )
        for phrase in required:
            self.assertIn(phrase, self.home)

    def test_all_eight_commitments_are_present(self) -> None:
        commitments = (
            "Put people before technology.",
            "Preserve human dignity in every interaction.",
            "Exercise clinical judgment with humility and accountability.",
            "Use AI transparently, ethically, and safely.",
            "Remain lifelong learners in a changing world.",
            "Share knowledge generously and strengthen one another.",
            "Lead with courage when others hesitate.",
            "Leave healthcare — and the world — better than we found it.",
        )
        for commitment in commitments:
            self.assertIn(f"<li>{commitment}</li>", self.home)

    def test_charter_is_accessible_and_explicitly_separate_from_admin_steward(self) -> None:
        self.assertIn('<section class="stewards-charter" id="stewards-charter" aria-labelledby="stewards-charter-title">', self.home)
        self.assertIn('<h2 id="stewards-charter-title">', self.home)
        self.assertIn('aria-label="The Steward’s Commitment"', self.home)
        self.assertIn("This founding Charter belongs to Nurse AI OS and its nursing community.", self.home)
        self.assertIn("It is separate from the STEWARD governance preview for hospital and clinic administrators.", self.home)
        charter_region = self.home.split('id="stewards-charter"', 1)[1].split("<!-- ============ HOMEPAGE SHORT", 1)[0]
        self.assertNotIn("hospital-clinic-administrators/", charter_region)

    def test_charter_has_dedicated_responsive_design_rules(self) -> None:
        for selector in (
            ".stewards-charter",
            ".charter-shell",
            ".charter-covenant",
            ".charter-doctrine",
            ".charter-commitments",
            ".charter-scope-note",
        ):
            self.assertIn(selector, self.css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", self.css)
        self.assertIn(".charter-commitments { grid-template-columns: 1fr; }", self.css)

    def test_charter_ci_scans_real_public_files(self) -> None:
        self.assertIn("cp index.html /tmp/home-charter-public/index.html", self.workflow)
        self.assertIn("cp assets/nurse-ai.css /tmp/home-charter-public/assets/nurse-ai.css", self.workflow)
        self.assertIn("scan-public-healthcare-artifacts.py /tmp/home-charter-public", self.workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
