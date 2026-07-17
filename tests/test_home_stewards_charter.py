#!/usr/bin/env python3
"""Homepage placement, doctrine, scope, and accessibility checks for the Steward's Charter."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
CSS = ROOT / "assets" / "nurse-ai.css"


class HomeStewardsCharterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.home = HOME.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.workflow = (ROOT / ".github" / "workflows" / "home-stewards-charter.yml").read_text(encoding="utf-8")

    def test_charter_is_immediately_below_hero_before_video_content(self) -> None:
        hero_end = self.home.index("</section>", self.home.index('class="hero"'))
        charter = self.home.index('id="stewards-charter"')
        video = self.home.index("<!-- ============ HOMEPAGE SHORT ============ -->")
        self.assertLess(hero_end, charter)
        self.assertLess(charter, video)
        charter_section_start = self.home.rfind("<section", hero_end, charter)
        between = self.home[hero_end:charter_section_start]
        self.assertNotIn("<section", between)

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
