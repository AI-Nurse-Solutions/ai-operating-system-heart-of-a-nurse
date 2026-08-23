#!/usr/bin/env python3
"""Contracts for the proposed three-lane build order.

Three things in this directory are easy to lose and expensive to lose quietly.

The first is the status boundary. A plan that names segments, artifacts, prices,
and ninety-day cycles reads like a company that has customers. It has none, and
every document has to keep saying so.

The second is the discipline the whole record exists to impose: build one lane
per cycle. The pressure to satisfy all three archetypes at once is exactly the
pressure that produced the proof gap, and it will arrive as a reasonable-sounding
edit ("Cycle 1 also covers the learner"). It is pinned instead.

The third is the set of gates and falsifiers. Evidence thresholds written before
the work are load-bearing; evidence thresholds edited after the results are
decoration. The specific numbers, the not-evidence list, and the falsifiers are
therefore fixed here, where moving one is a visible act rather than a quiet one.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANES = ROOT / "three-lanes"
INDEX = LANES / "README.md"
SEGMENTS = LANES / "SEGMENTS.md"
STRATEGY = LANES / "STRATEGY.md"
IMPLEMENTATION = LANES / "IMPLEMENTATION.md"
EVIDENCE = LANES / "EVIDENCE.md"
PLAYBOOK = LANES / "PLAYBOOK.md"
PAGE = LANES / "index.html"

MARKDOWN = (INDEX, SEGMENTS, STRATEGY, IMPLEMENTATION, EVIDENCE, PLAYBOOK)


def flat(text: str) -> str:
    """Whitespace-collapsed, so a reflowed paragraph cannot break a pin."""
    return re.sub(r"\s+", " ", text)


class ThreeLaneDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs = {path: path.read_text(encoding="utf-8") for path in MARKDOWN}
        cls.flat = {path: flat(text) for path, text in cls.docs.items()}
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.flat_page = flat(cls.page)

    def test_documents_are_discoverable(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "[`three-lanes/`](three-lanes/)",
            root_readme,
            "root README does not link the directory",
        )
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(1, sitemap.count("https://nurse-ai-os.org/three-lanes/"))
        for path in MARKDOWN + (PAGE,):
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

    def test_status_is_proposed_not_operational(self) -> None:
        self.assertIn('status: "Proposed segmentation"', self.docs[SEGMENTS])
        self.assertIn('status: "Proposed strategy"', self.docs[STRATEGY])
        self.assertIn('status: "Proposed staged plan"', self.docs[IMPLEMENTATION])
        self.assertIn('status: "Proposed measurement plan"', self.docs[EVIDENCE])
        self.assertIn('status: "Proposed operating playbook"', self.docs[PLAYBOOK])
        self.assertIn("Status: proposed segmentation", self.docs[INDEX])
        for path, text in self.flat.items():
            self.assertIn(
                "They do not establish"
                if path is INDEX
                else "creates no"
                if "creates no" in text
                else "It reports no",
                text,
                f"{path.name} opens without a stated boundary",
            )

    def test_no_customer_or_pilot_is_implied(self) -> None:
        # A plan with dates and prices reads as a business with revenue.
        for path, text in self.flat.items():
            for overclaim in (
                "our customers",
                "customers have",
                "in production",
                "clinically validated",
                "HIPAA compliant",
                "institutionally authorized",
            ):
                self.assertNotIn(
                    overclaim, text.casefold(), f"{path.name} claims: {overclaim!r}"
                )
        self.assertIn("No date in the plan commits any person to perform work", self.flat[INDEX])
        self.assertIn("No date in the plan commits any person to perform work", self.flat_page)

    def test_one_lane_per_cycle_survives(self) -> None:
        pin = (
            "Interview and observe all three archetypes continuously. "
            "Build exactly one lane per 90-day cycle."
        )
        self.assertIn(pin, self.flat[STRATEGY], "the operating rule was lost")
        self.assertIn("Build exactly one lane per 90-day cycle", self.flat_page)
        self.assertIn("Three lanes of listening. One lane of building", self.flat[INDEX])

    def test_the_build_order_is_manager_first(self) -> None:
        order = "Cycle 1: Manager  →  Cycle 2: Certification Learner  →  Cycle 3: Builder–Organizer"
        self.assertIn(order, self.docs[STRATEGY])
        self.assertIn(
            "Manager → Certification Learner → Builder–Organizer", self.docs[INDEX]
        )
        # Each cycle is conditional, not calendared.
        self.assertIn(
            "Begins only if the Cycle 1 gate passes", self.flat[IMPLEMENTATION]
        )
        self.assertIn(
            "Begins only if the Cycle 2 gate passes", self.flat[IMPLEMENTATION]
        )

    def test_the_learner_split_is_preserved(self) -> None:
        segments = self.flat[SEGMENTS]
        self.assertIn("The Learner is two markets, not one", segments)
        self.assertIn("The certification learner is the buildable learner", segments)
        # Prelicensure is research-only, and the non-goals are refusals.
        strategy = self.flat[STRATEGY]
        self.assertIn("There is no direct-to-student build in this plan", strategy)
        for non_goal in (
            "Completing graded assignments",
            "Generating exam-bank substitutes",
            "Ingesting or reasoning over clinical-rotation patient information",
            "Claiming competence",
            "Replacing faculty supervision",
            "Implying completion of accredited clinical or simulation hours",
        ):
            self.assertIn(non_goal, strategy, f"prelicensure non-goal dropped: {non_goal!r}")

    def test_five_roles_are_separated_for_every_segment(self) -> None:
        segments = self.docs[SEGMENTS]
        for role in ("**User**", "**Buyer**", "**Beneficiary**", "**Approver**", "**Steward**"):
            self.assertIn(role, segments, f"role separation dropped: {role}")
        for segment in (
            "**Manager**",
            "**Certification learner**",
            "**Builder–Organizer**",
            "**Prelicensure learner**",
        ):
            self.assertIn(segment, segments, f"segment missing from role table: {segment}")
        self.assertIn(
            "The person who loves the product is frequently not the person who pays for it",
            self.flat[SEGMENTS],
        )

    def test_cross_cutting_roles_are_not_lanes(self) -> None:
        segments = self.flat[SEGMENTS]
        self.assertIn("Cross-cutting roles that are not lanes", segments)
        self.assertIn("not in a separate lane", segments)
        self.assertIn("Their participation is compensated", segments)
        # Executive buyers are not the Manager persona.
        self.assertIn("are approvers and buyers, not daily users", segments)

    def test_governance_ceiling_holds_in_every_lane(self) -> None:
        strategy = self.flat[STRATEGY]
        self.assertIn(
            "D0/D1 data, Green/Yellow risk, Observe/Draft/Recommend action, "
            "with Recommend beginning at Yellow",
            strategy,
        )
        for prohibition in (
            "no PHI",
            "no employment or competency determination about a named person",
            "no clinical decision support",
        ):
            self.assertIn(prohibition, strategy, f"prohibition dropped: {prohibition!r}")
        self.assertIn(
            "A lane that needs one of these to be useful is not ready", strategy
        )
        # Institution-specific work is Yellow even with no PHI — the easiest
        # rule to relax, and the one that keeps the Manager lane honest.
        for path in (SEGMENTS, STRATEGY, IMPLEMENTATION):
            self.assertIn(
                "Yellow", self.flat[path], f"{path.name} lost the risk tier"
            )
        self.assertIn(
            "Institution-specific work is Yellow even without PHI", self.flat[SEGMENTS]
        )
        self.assertIn(
            "Institution-specific work is Yellow even without PHI",
            self.flat[IMPLEMENTATION],
        )

    def test_one_canonical_edena_tier_system(self) -> None:
        # A simplified display may project the canon; it may never be a second
        # tier system maintained beside it.
        strategy = self.flat[STRATEGY]
        self.assertIn("Green, Yellow, Orange, Red-P, Red-E", self.flat[IMPLEMENTATION])
        self.assertIn(
            "never a second tier system maintained in parallel", self.flat[IMPLEMENTATION]
        )
        self.assertIn("One canonical EDENA policy source", self.flat[IMPLEMENTATION])
        self.assertIn("public ceiling", strategy)

    def test_the_packet_keeps_its_differentiating_sections(self) -> None:
        plan = self.flat[IMPLEMENTATION]
        for section in (
            "Baseline and missing information",
            "Staff-burden assessment",
            "Stop and escalation conditions",
            "Unresolved concerns",
            "Decision owner and action owner",
        ):
            self.assertIn(section, plan, f"packet section dropped: {section!r}")
        self.assertIn("What is unknown is listed, not filled in", plan)
        self.assertIn("Dissent survives to the reviewer intact", plan)
        self.assertIn("Two named humans; never the system", plan)
        # The schema is frozen for the cycle; scope creep is the failure mode.
        self.assertIn("The schema does not grow mid-cycle", plan)

    def test_the_intake_refuses_at_the_door(self) -> None:
        plan = self.flat[IMPLEMENTATION]
        for refusal in (
            "PHI or any reconstructable patient narrative",
            "identifiable staff performance, discipline, or attendance data",
            "rights-encumbered content",
            "requests for clinical decision support",
            "requests to determine, score, or rank a named person",
        ):
            self.assertIn(refusal, plan, f"refusal dropped: {refusal!r}")
        self.assertIn("A refusal is not a dead end", plan)
        # And a refusal explains itself in the user's terms.
        self.assertIn(
            "this names an identifiable staff member's performance", self.flat[PLAYBOOK]
        )

    def test_the_spine_is_named_so_later_lanes_stay_cheap(self) -> None:
        strategy = self.flat[STRATEGY]
        for component in (
            "Intake contract",
            "Refusal set",
            "Source and rights ledger",
            "Section engine",
            "Uncertainty and provenance display",
            "Human correction and override record",
            "Session record",
            "Evaluation harness",
        ):
            self.assertIn(component, strategy, f"spine component dropped: {component!r}")
        self.assertIn(
            "Extended per lane, never weakened per lane", strategy,
            "the refusal set must not be relaxed to make a lane work",
        )

    def test_gate_thresholds_are_fixed_and_conjunctive(self) -> None:
        evidence = self.flat[EVIDENCE]
        self.assertIn(
            "A gate passes only if **every** condition holds", self.docs[EVIDENCE]
        )
        self.assertIn(
            "Partial passage is failure with a re-plan, not a reason to proceed carefully",
            evidence,
        )
        for threshold in (
            "At least **six** packets",
            "accepted with **less rework than that approver",
            "At least **three** partners returned with a second real problem, unprompted",
            "At least **one** paid engagement or a signed pilot commitment with a date",
            "At least **fifteen** stored evaluation cases",
        ):
            self.assertIn(
                threshold.replace("**", ""),
                evidence.replace("**", ""),
                f"gate threshold moved or dropped: {threshold!r}",
            )

    def test_the_second_problem_is_the_headline_signal(self) -> None:
        pin = "They bring a second real problem without being asked."
        self.assertIn(pin, self.flat[EVIDENCE])
        self.assertIn(pin, self.flat[INDEX])
        self.assertIn("second real problem without being asked", self.flat_page)

    def test_vanity_signals_are_named_as_non_evidence(self) -> None:
        evidence = self.flat[EVIDENCE]
        self.assertIn("Signals that are not evidence", evidence)
        for signal in (
            "Sign-ups",
            "Positive reactions after a demonstration",
            "Time on task",
            "A pilot discussed but unscheduled",
            "Founder-run sessions producing good artifacts",
            "Reviewer approval of an authoritative-looking packet",
        ):
            self.assertIn(signal, evidence, f"non-evidence signal dropped: {signal!r}")

    def test_the_planted_omission_test_survives_with_its_ethics(self) -> None:
        evidence = self.flat[EVIDENCE]
        self.assertIn("known material omission", evidence)
        # Disclosed in advance, and never on a live institutional decision —
        # the two conditions that keep this a study method rather than a trick.
        self.assertIn("disclosed to design partners in advance", evidence)
        self.assertIn(
            "never run on an artifact that will drive a real institutional decision",
            evidence,
        )
        self.assertIn("disclosed to design partners in advance", self.flat_page)

    def test_reliance_and_deskilling_are_measured_not_assumed(self) -> None:
        evidence = self.flat[EVIDENCE]
        self.assertIn("The unassisted check", evidence)
        self.assertIn("never as a score", evidence)
        self.assertIn(
            "never used in any determination about a person", evidence
        )
        self.assertIn("The confidence trap", evidence)
        self.assertIn(
            "Confidence rising while unassisted performance flattens is a harm signal",
            evidence,
        )
        self.assertIn("Patient outcomes are not measured", evidence)

    def test_the_sponsored_learner_boundary_is_a_data_model_rule(self) -> None:
        for path in (SEGMENTS, IMPLEMENTATION, EVIDENCE):
            self.assertIn(
                "sponsor", self.flat[path].casefold(),
                f"{path.name} lost the sponsorship boundary",
            )
        self.assertIn(
            "Enforced in the data model, defaulted closed", self.flat[IMPLEMENTATION]
        )
        self.assertIn(
            "closed to sponsors by default and by data model", self.flat[EVIDENCE]
        )

    def test_falsifiers_are_stated_in_advance(self) -> None:
        evidence = self.flat[EVIDENCE]
        self.assertIn("Falsifiers stated in advance", evidence)
        for falsifier in (
            "Managers value the drafting and discard the governance sections",
            "Approvers accept packets with planted omissions",
            "Learners return for streaks and reminders rather than for the plan",
            "Every paying customer is a personal contact of the founder",
            "The spine does not carry",
            "Capability packs are only ever authored by the founder",
        ):
            self.assertIn(falsifier, evidence, f"falsifier dropped: {falsifier!r}")

    def test_stop_conditions_exist_for_every_cycle(self) -> None:
        plan = self.docs[IMPLEMENTATION]
        for heading in (
            "### 1.7 Cycle 1 stop conditions",
            "### 2.5 Cycle 2 stop conditions",
            "### 3.5 Cycle 3 stop conditions",
        ):
            self.assertIn(heading, plan, f"missing {heading}")
        self.assertIn("Stop conditions", self.docs[STRATEGY])
        self.assertIn(
            "The refusal set has to be weakened for any lane to be useful",
            self.flat[STRATEGY],
        )

    def test_cycle_three_preconditions_gate_the_marketplace(self) -> None:
        plan = self.flat[IMPLEMENTATION]
        self.assertIn("Preconditions, not features", plan)
        for condition in (
            "consented",
            "rights-aware",
            "attributed",
            "versioned",
            "evaluated",
            "revocable",
        ):
            self.assertIn(condition, plan, f"contribution precondition dropped: {condition!r}")
        self.assertIn(
            "a marketplace assembled without them is a liability", plan
        )
        self.assertIn(
            "Do not start Cycle 3 at all if", self.flat[STRATEGY]
        )

    def test_rights_clearance_precedes_the_learner_lane(self) -> None:
        plan = self.flat[IMPLEMENTATION]
        self.assertIn("The dominant constraint is rights, not engineering", plan)
        self.assertIn(
            "It does not reproduce, reconstruct, or approximate proprietary test items",
            plan,
        )
        self.assertIn("clean-room drafting procedure written", plan)
        self.assertIn("IP counsel engaged before any commercial corpus", plan)
        # And no outcome claim the system cannot support.
        self.assertIn("No pass-rate claim, no competence claim, no score prediction", plan)
        self.assertIn("The outcome is explicitly *not*", self.docs[SEGMENTS])

    def test_community_participation_is_compensated_and_can_change_the_product(self) -> None:
        playbook = self.flat[PLAYBOOK]
        self.assertIn(
            "A community is a moat only when members change the product", playbook
        )
        self.assertIn("Reviewers are compensated", playbook)
        self.assertIn(
            "Unpaid nurse labor to legitimize a commercial product is not community participation",
            playbook,
        )
        self.assertIn("Disagreement is documented and published", playbook)
        self.assertIn('No "ratified" designation until', playbook)

    def test_the_page_matches_the_record(self) -> None:
        # Marketing prose drifts. Every load-bearing claim on the public page
        # must still exist in the documents behind it.
        self.assertIn("<title>", self.page)
        self.assertIn(
            "https://nurse-ai-os.org/three-lanes/", self.page, "canonical URL missing"
        )
        for claim in (
            "Build exactly one lane per 90-day cycle",
            "second real problem without being asked",
            "Institution-specific work is Yellow",
            "no clinical decision support",
        ):
            self.assertIn(claim, self.flat_page, f"page dropped: {claim!r}")
        # The page must not promise what no lane does.
        for forbidden in (
            "clinically validated",
            "hipaa compliant",
            "ai nurse",
            "autonomous",
        ):
            self.assertNotIn(
                forbidden, self.flat_page.casefold(), f"page overclaims: {forbidden!r}"
            )

    def test_the_page_states_its_status_above_the_content(self) -> None:
        head, _, _ = self.page.partition('<section id="decision"')
        self.assertIn("Status:", head, "status boundary is not above the first section")
        self.assertIn("proposed segmentation", flat(head))
        self.assertIn("permission to process patient data", flat(head))


if __name__ == "__main__":
    unittest.main()
