#!/usr/bin/env python3
"""Contracts for the proposed NIN Nurse Formation doctrine and playbook."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FORMATION = ROOT / "nurse-formation"
INDEX = FORMATION / "README.md"
DOCTRINE = FORMATION / "DOCTRINE.md"
PLAYBOOK = FORMATION / "PLAYBOOK.md"


class NurseFormationDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.doctrine = DOCTRINE.read_text(encoding="utf-8")
        cls.playbook = PLAYBOOK.read_text(encoding="utf-8")
        # Prose pins are compared against whitespace-collapsed text so a
        # reflowed paragraph cannot silently break a doctrine contract.
        cls.flat_index = re.sub(r"\s+", " ", cls.index)
        cls.flat_doctrine = re.sub(r"\s+", " ", cls.doctrine)
        cls.flat_playbook = re.sub(r"\s+", " ", cls.playbook)

    def test_documents_are_discoverable_and_honest_about_status(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("NIN Nurse Formation doctrine and playbook", root_readme)
        self.assertIn("[`nurse-formation/`](nurse-formation/)", root_readme)
        self.assertIn(
            "Status: proposed education doctrine and operating playbook", self.index
        )
        self.assertIn("does not establish a curriculum", self.index)
        self.assertIn('status: "Proposed education doctrine"', self.doctrine)
        self.assertIn('status: "Proposed operating playbook"', self.playbook)
        self.assertIn(
            "capabilities remain inactive until built and verified", self.playbook
        )

    def test_relative_markdown_links_resolve(self) -> None:
        for source in (INDEX, DOCTRINE, PLAYBOOK):
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative_target = unquote(target.split("#", 1)[0])
                self.assertFalse(
                    Path(relative_target).is_absolute(),
                    f"{source.relative_to(ROOT)} has a non-relative link to {target}",
                )
                resolved = (source.parent / relative_target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(ROOT.resolve()),
                    f"{source.relative_to(ROOT)} links outside the repository: {target}",
                )
                self.assertTrue(
                    resolved.exists(),
                    f"{source.relative_to(ROOT)} has a broken link to {target}",
                )

    def test_doctrine_preserves_the_formation_maxims(self) -> None:
        for required in (
            "Agents coach. Learners commit. Educators judge. Institutions credential. Nurses steward.",
            "The struggle is the curriculum. AI may scaffold the struggle; it must never perform it.",
            "Formation over efficiency: the product of nursing education is the nurse, not the assignment.",
            "AI never grades alone, and it never gates a career.",
            "Practice happens on patient-shaped data with no patients in it.",
            "Learner privacy is not a lesser privacy.",
        ):
            self.assertIn(required, self.flat_doctrine)

    def test_doctrine_preserves_human_evaluative_authority(self) -> None:
        for required in (
            "No AI output may be the sole basis",
            "grade, progression, remediation, professionalism, discipline, competency, entrustment,",
            "AI is formative by default and summative never alone",
            "no AI-detector output may be the sole basis for a misconduct finding",
            "a consequential debrief is led by a human educator",
            "It may not ratify",
        ):
            self.assertIn(required, self.flat_doctrine)

    def test_doctrine_preserves_the_five_formation_rules(self) -> None:
        for required in (
            "Rule 1 — First commitment",
            "Rule 2 — Visible reasoning",
            "Rule 3 — The practice field",
            "Rule 4 — Human evaluative authority",
            "Rule 5 — The questioned tool",
            "commit-then-compare",
            "Who was in the training data? Who was",
            "Overrides and near misses are learning signals, not user failure",
        ):
            self.assertIn(required, self.flat_doctrine)

    def test_doctrine_preserves_edena_and_privacy_boundaries(self) -> None:
        for required in (
            "Green, Yellow, Orange, Red-P (prohibited), and Red-E",
            "Unrestricted autonomy is prohibited",
            "ambiguity narrows",
            "EDENA-STUDENT-MODE",
            "EDENA-JUDGMENT-VISIBILITY",
            "EDENA-PRIVATE-REFLECTION",
            "EDENA-ZONE-MIGRATION",
            "NIN–NAIO Master",
            "human-in-the-loop system",
            "reviewable, overridable, and traceable",
        ):
            self.assertIn(required, self.flat_doctrine)

    def test_embedding_map_stays_honest_about_enforcement_status(self) -> None:
        self.assertIn("reference implementation evidence", self.index)
        self.assertIn(
            "it is not a curriculum, an approved program, or an operating education service",
            self.index,
        )
        self.assertIn(
            "That evidence supports the direction and activates nothing.",
            self.flat_doctrine,
        )
        self.assertIn(
            "None exists until built, tested, and verified", self.flat_doctrine
        )
        self.assertIn("EDENA-EDUCATOR-AUTHORITY", self.doctrine)
        self.assertIn(
            "Planned enforcement (design intentions, not yet implemented)",
            self.doctrine,
        )

    def test_playbook_preserves_adoption_order_and_deferrals(self) -> None:
        for required in (
            "No step automatically grants the next state",
            "no AI output may be the sole basis for a grade",
            "program may require of learners a literacy its faculty have not begun",
            "formative uses only — nothing summative touches AI in the pilot",
            "No gate may be skipped because a tool is popular, free, or already licensed elsewhere",
            "A sighting is a contribution, never a complaint on the reporter's record",
            "Explicit deferrals",
            "automated proctoring, gaze tracking, or emotion inference",
            "PHI or D3/D4 processing",
            "Designed, documented, implemented, tested, committed, merged, deployed, and live-verified are distinct states",
        ):
            self.assertIn(required, self.flat_playbook)

    def test_claims_discipline_matches_bounded_language(self) -> None:
        for banned_claim_context in (
            "licensure or examination success",
            "clinical competence, readiness, or entrustment",
            "clinical-hour equivalence",
            "causal learning improvement",
        ):
            self.assertIn(banned_claim_context, self.flat_doctrine)
            self.assertIn(banned_claim_context.split(",")[0], self.flat_playbook)
        self.assertIn(
            "must never be represented as evidence of learning", self.flat_doctrine
        )


if __name__ == "__main__":
    unittest.main()
