#!/usr/bin/env python3
"""Contracts for the proposed Care Workforce Surge design record.

Two things are easy to lose here and expensive to lose quietly.

The first is honesty about status. This directory argues that a Nurse AI OS
should become supervising infrastructure for a low-tenure care workforce. The
projection it reviews asserted it already *will be* critical infrastructure.
The distinction is the whole difference between a design record and a
fabricated status claim, so it is pinned rather than trusted to survive future
editing.

The second is the gap between the public page and the sourced record behind
it. Marketing prose drifts; a statistic on a landing page outlives the document
that justified it. Every headline figure on the page is therefore required to
still exist in the validation record.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SURGE = ROOT / "care-workforce-surge"
INDEX = SURGE / "README.md"
VALIDATION = SURGE / "VALIDATION.md"
DOCTRINE = SURGE / "DOCTRINE.md"
STRATEGY = SURGE / "STRATEGY.md"
IMPLEMENTATION = SURGE / "IMPLEMENTATION.md"
PLAYBOOK = SURGE / "PLAYBOOK.md"
PAGE = SURGE / "index.html"

MARKDOWN = (INDEX, VALIDATION, DOCTRINE, STRATEGY, IMPLEMENTATION, PLAYBOOK)


def flat(text: str) -> str:
    """Whitespace-collapsed, so a reflowed paragraph cannot break a pin."""
    return re.sub(r"\s+", " ", text)


class CareWorkforceSurgeDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs = {path: path.read_text(encoding="utf-8") for path in MARKDOWN}
        cls.flat = {path: flat(text) for path, text in cls.docs.items()}
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.flat_page = flat(cls.page)

    def test_documents_are_discoverable(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "[`care-workforce-surge/`](care-workforce-surge/)",
            root_readme,
            "root README does not link the directory",
        )
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(
            1, sitemap.count("https://nurse-ai-os.org/care-workforce-surge/")
        )
        for path in MARKDOWN + (PAGE,):
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

    def test_status_is_proposed_not_operational(self) -> None:
        self.assertIn('status: "Proposed workforce doctrine"', self.docs[DOCTRINE])
        self.assertIn('status: "Proposed strategy"', self.docs[STRATEGY])
        self.assertIn('status: "Proposed staged plan"', self.docs[IMPLEMENTATION])
        self.assertIn('status: "Proposed operating playbook"', self.docs[PLAYBOOK])
        self.assertIn('status: "Evidence review"', self.docs[VALIDATION])
        self.assertIn("Status: proposed workforce doctrine", self.docs[INDEX])
        for path, text in self.flat.items():
            self.assertIn(
                "no", text.casefold()[:4000],
                f"{path.name} opens without any stated boundary",
            )

    def test_the_status_claim_itself_is_refused(self) -> None:
        # The projection under review asserted critical-infrastructure status.
        # The record must decline it rather than repeat it.
        self.assertIn(
            "no such system holds critical-infrastructure status today",
            self.flat[VALIDATION],
        )
        self.assertIn(
            "The status claim should not be made", self.flat[VALIDATION]
        )
        self.assertIn("Status: proposed", self.docs[INDEX])
        self.assertNotIn("is critical infrastructure for", self.flat_page)

    def test_the_restated_projection_survives(self) -> None:
        pin = "The binding constraint is not labor supply. It is supervisory capacity per experienced nurse."
        for path in (VALIDATION, INDEX):
            self.assertIn(pin, self.flat[path], f"{path.name} lost the restatement")
        self.assertIn(
            "binding constraint is not labor supply", self.flat_page
        )

    def test_hard_boundaries_are_stated_in_doctrine(self) -> None:
        doctrine = self.flat[DOCTRINE]
        for boundary in (
            "no representation, appearance, or implication that the system is a nurse",
            "no employment, competency, credentialing, disciplinary, promotion, or termination determination",
            "no claim that the system reduces required staffing, supervision, orientation, or training hours",
            "no PHI, no reconstructable patient narrative",
            "The system is never the last thing between a worker and a patient.",
            "Deskilling is a tracked harm",
            "If a deployment coincides with less supervision, the deployment is out of doctrine.",
        ):
            self.assertIn(boundary, doctrine, f"doctrine dropped: {boundary!r}")

    def test_refusal_catalog_is_complete_and_operational(self) -> None:
        doctrine = self.flat[DOCTRINE]
        self.assertIn("## 6. Refusal catalog", self.docs[DOCTRINE])
        for cls_name in (
            "Out-of-scope clinical",
            "Title / identity",
            "Emergency signal",
            "PHI intake",
            "Employment determination",
            "Staffing substitution",
            "Cross-jurisdiction transfer",
            "Instruction injection",
        ):
            self.assertIn(cls_name, doctrine, f"refusal class missing: {cls_name}")
        # A catalog nobody tests is a hope, and the playbook has to say so.
        self.assertIn(
            "A class without a passing adversarial test is not a refusal",
            self.flat[PLAYBOOK],
        )
        # Narrowing a refusal must cost a doctrine amendment, not a sprint
        # decision made under deadline.
        self.assertIn(
            "Any change that narrows a refusal class is a doctrine amendment "
            "with a named author, a date, the evidence relied on, and the risk "
            "accepted. It is never a product decision.",
            self.flat[PLAYBOOK],
        )

    def test_escalation_is_never_gated(self) -> None:
        playbook = self.flat[PLAYBOOK]
        self.assertIn("Rung 4 is unconditional", playbook)
        self.assertIn("When in doubt, go up a rung", playbook)
        self.assertIn("Ambiguity resolves upward", playbook)

    def test_every_phase_has_a_gate_and_a_stop_condition(self) -> None:
        text = self.docs[IMPLEMENTATION]
        phases = re.findall(r"^## Phase \d[^\n]*$", text, re.M)
        self.assertGreaterEqual(len(phases), 5, f"found phases: {phases}")
        self.assertEqual(
            len(phases),
            text.count("**Evidence gate"),
            "a phase is missing its evidence gate",
        )
        self.assertEqual(
            len(phases),
            text.count("**Stop conditions"),
            "a phase is missing its stop conditions",
        )

    def test_no_aggregate_score_can_hide_a_failing_refusal_class(self) -> None:
        # An aggregate pass rate is how a broken emergency path ships with good
        # marks elsewhere. The gate is per-class or it is not a gate.
        gate = self.flat[IMPLEMENTATION]
        self.assertIn("Every refusal class passes every test in its bundle", gate)
        self.assertIn("There is no aggregate threshold", gate)
        self.assertNotRegex(
            gate,
            r"\u2265 ?9\d percent pass|at least 9\d percent pass",
            "an aggregate pass threshold reappeared in a gate",
        )

    def test_the_page_does_not_overstate_provenance(self) -> None:
        # The record leans on trade coverage for the AACN capacity figures and
        # on a tracker for three of the four state laws. The page must not
        # promise more than that.
        self.assertNotIn("checked against primary sources", self.flat_page)
        self.assertIn("labelled as such where it is used", self.flat_page)
        validation = self.flat[VALIDATION]
        self.assertIn("Provenance is uneven and is stated rather than smoothed over", validation)
        self.assertIn("cited here through trade coverage of AACN", validation)
        self.assertIn("rather than the enacted texts", validation)

    def test_falsifiers_are_stated_in_advance(self) -> None:
        self.assertIn("## 6. What would falsify this", self.docs[VALIDATION])
        self.assertIn("Absence of evidence is not a defence", self.flat[VALIDATION])
        self.assertIn("The failure mode to avoid is not being wrong", self.flat[STRATEGY])

    def test_page_headline_figures_still_exist_in_the_validation_record(self) -> None:
        # The page is where a number goes to outlive its source. Each headline
        # figure must still be present in the record that justified it.
        validation = self.flat[VALIDATION]
        page = self.flat_page
        pairs = (
            ("739,800", "739,800"),
            ("9.7 million", "9.7 million"),
            ("680,500", "680,500"),
            ("$17.36", "$17.36"),
            ("39.9%", "39.9 percent"),
            ("93,176", "93,176"),
            ("94.9 percent", "94.9 percent"),
            ("34.5 percent", "34.5 percent"),
            ("28.4 to 22.4 percent", "28.4 percent"),
            ("15 percent", "15 percent"),
            ("75 hours", "75 clock hours"),
        )
        for on_page, in_record in pairs:
            self.assertIn(on_page, page, f"page lost the figure {on_page!r}")
            self.assertIn(
                in_record, validation, f"validation record lost {in_record!r}"
            )

    def test_load_bearing_evidence_carries_named_sources(self) -> None:
        validation = self.docs[VALIDATION]
        for source in (
            "bls.gov",
            "phinational.org",
            "ncsbn",
            "who.int",
            "academic.oup.com/qje",
            "ox.ac.uk",
            "thelancet.com",
            "ecfr.gov",
        ):
            self.assertIn(source, validation.casefold(), f"missing source: {source}")
        # The one figure that could not be confirmed in the primary source is
        # flagged rather than quietly used.
        self.assertIn(
            "the weaker, source-backed one", flat(validation)
        )

    def test_relative_links_resolve(self) -> None:
        for source, text in self.docs.items():
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                    continue
                path_part, _, _fragment = target.partition("#")
                if not path_part:
                    continue
                relative_target = unquote(path_part)
                self.assertFalse(
                    Path(relative_target).is_absolute(),
                    f"{source.name} has a non-relative link to {target}",
                )
                resolved = (source.parent / relative_target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(ROOT.resolve()),
                    f"{source.name} links outside the repository: {target}",
                )
                self.assertTrue(
                    resolved.exists(), f"{source.name} has a broken link to {target}"
                )

    def test_page_is_self_contained_and_not_a_shared_shell_page(self) -> None:
        # The shared site shell carries a nav policy of its own; this page is
        # standalone like the Care Intelligence paper page, so it must not
        # half-adopt the shell and fail that policy in a confusing way.
        self.assertNotIn('class="site-header"', self.page)
        self.assertNotIn("assets/site-shell.js", self.page)
        self.assertIn('<html lang="en">', self.page)
        self.assertIn("care-workforce-surge/", self.page)

    def test_no_promotional_overreach_on_the_public_page(self) -> None:
        page_lower = self.page.casefold()
        for phrase in (
            "ai nurse for",
            "clinically validated",
            "hipaa compliant",
            "reduces staffing",
            "replaces the preceptor",
            "certified competency",
        ):
            self.assertNotIn(phrase, page_lower, f"page overreaches: {phrase!r}")
        self.assertIn("do not establish a product", self.flat_page)


if __name__ == "__main__":
    unittest.main()
