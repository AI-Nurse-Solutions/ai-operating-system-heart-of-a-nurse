import unittest

import _bootstrap  # noqa: F401

from naio_integrations.contract import KnowledgeSource
from naio_integrations.evidence import (
    EVIDENCE_LABELS,
    ClaimLedger,
    EvidenceError,
    EvidenceQuestionBuilder,
    compare_guidelines,
)
from naio_integrations.knowledge import GovernedKnowledge

TODAY = "2026-07-28"


def make_knowledge() -> GovernedKnowledge:
    knowledge = GovernedKnowledge(home_jurisdiction="US")
    knowledge.index(
        [
            KnowledgeSource(
                source_id="policy-falls-2026",
                title="Falls Prevention Policy",
                doc_type="policy",
                effective_date="2026-01-01",
                expires_date="2027-01-01",
                jurisdiction="US",
                content=(
                    "Hourly rounding is required on all units. Bed alarms are"
                    " applied for high-risk patients. Fall risk is reassessed"
                    " every shift."
                ),
                tenant="org:mercy",
            ),
            KnowledgeSource(
                source_id="research-falls-2025",
                title="Falls interventions meta-analysis",
                doc_type="research",
                effective_date="2025-06-01",
                expires_date=None,
                jurisdiction="US",
                content="Meta-analysis of hourly rounding effects on falls.",
                tenant="org:mercy",
            ),
        ]
    )
    return knowledge


class EvidenceQuestionBuilderTests(unittest.TestCase):
    def setUp(self):
        self.builder = EvidenceQuestionBuilder()

    def test_pico_question_renders_all_components(self):
        question = self.builder.build(
            population="adults on medical-surgical units",
            intervention="hourly rounding",
            comparison="rounding every two hours",
            outcome="fall rates",
        )
        self.assertEqual(question.framework, "PICO")
        self.assertIn("adults on medical-surgical units", question.question)
        self.assertIn("hourly rounding", question.question)
        self.assertIn("compared with rounding every two hours", question.question)
        self.assertIn("fall rates", question.question)
        self.assertTrue(question.question.endswith("?"))

    def test_timeframe_upgrades_to_picot(self):
        question = self.builder.build(
            population="ICU patients",
            intervention="early mobility",
            comparison="standard care",
            outcome="delirium incidence",
            timeframe="90 days",
        )
        self.assertEqual(question.framework, "PICOT")
        self.assertIn("within 90 days", question.question)

    def test_every_component_is_required(self):
        for missing in ("population", "intervention", "comparison", "outcome"):
            fields = {
                "population": "adults",
                "intervention": "rounding",
                "comparison": "usual care",
                "outcome": "falls",
            }
            fields[missing] = "   "
            with self.assertRaises(EvidenceError, msg=missing):
                self.builder.build(**fields)

    def test_components_are_privacy_screened(self):
        question = self.builder.build(
            population="the patient with MRN: A123456",
            intervention="hourly rounding",
            comparison="usual care",
            outcome="fall rates",
        )
        self.assertNotIn("A123456", question.question)
        self.assertNotIn("A123456", " ".join(question.search_terms))

    def test_search_terms_feed_governed_retrieval(self):
        knowledge = make_knowledge()
        question = self.builder.build(
            population="hospitalized adults",
            intervention="hourly rounding",
            comparison="usual care",
            outcome="falls prevention",
        )
        answer = knowledge.retrieve(
            "org:mercy", " ".join(question.search_terms), TODAY
        )
        self.assertFalse(answer.refused)
        self.assertEqual(answer.passages[0]["doc_type"], "policy")


class ClaimLedgerTests(unittest.TestCase):
    def setUp(self):
        self.knowledge = make_knowledge()
        self.ledger = ClaimLedger(self.knowledge)

    def test_the_five_spec_labels_are_the_only_labels(self):
        self.assertEqual(
            set(EVIDENCE_LABELS),
            {
                "verified_source",
                "local_policy",
                "user_provided_context",
                "ai_synthesis",
                "assumption_requiring_confirmation",
            },
        )
        with self.assertRaises(EvidenceError):
            self.ledger.record_claim("org:mercy", "text", "gut_feeling")

    def test_no_citation_no_claim_for_source_backed_labels(self):
        for label in ("verified_source", "local_policy", "ai_synthesis"):
            with self.assertRaises(EvidenceError, msg=label):
                self.ledger.record_claim("org:mercy", "Rounding works.", label)

    def test_citations_must_exist_in_the_same_tenants_index(self):
        with self.assertRaises(EvidenceError):
            self.ledger.record_claim(
                "org:mercy",
                "Rounding works.",
                "verified_source",
                source_ids=("ghost-source",),
            )
        with self.assertRaises(EvidenceError):
            self.ledger.record_claim(
                "personal:rn-1",
                "Rounding works.",
                "verified_source",
                source_ids=("policy-falls-2026",),
            )

    def test_trace_replays_full_source_governance_metadata(self):
        claim = self.ledger.record_claim(
            "org:mercy",
            "Hourly rounding reduces falls.",
            "ai_synthesis",
            source_ids=("research-falls-2025", "policy-falls-2026"),
        )
        trace = self.ledger.trace(claim.claim_id)
        self.assertEqual(trace["label"], "ai_synthesis")
        self.assertEqual(len(trace["sources"]), 2)
        by_id = {s["source_id"]: s for s in trace["sources"]}
        self.assertEqual(
            by_id["policy-falls-2026"]["effective_date"], "2026-01-01"
        )
        self.assertEqual(by_id["research-falls-2025"]["doc_type"], "research")
        self.assertTrue(trace["local_policy_precedence"])

    def test_assumptions_await_a_named_human_confirmation(self):
        assumption = self.ledger.record_claim(
            "org:mercy",
            "Night-shift rounding compliance is lower.",
            "assumption_requiring_confirmation",
        )
        self.assertEqual(assumption.status, "awaiting_confirmation")
        self.assertEqual(
            self.ledger.unconfirmed_assumptions("org:mercy"), (assumption,)
        )
        with self.assertRaises(EvidenceError):
            self.ledger.confirm_assumption(
                assumption.claim_id, ("policy-falls-2026",), "  ", "2026-07-28"
            )
        with self.assertRaises(EvidenceError):
            self.ledger.confirm_assumption(
                assumption.claim_id, (), "Educator Kim", "2026-07-28"
            )
        confirmed = self.ledger.confirm_assumption(
            assumption.claim_id,
            ("policy-falls-2026",),
            "Educator Kim",
            "2026-07-28",
        )
        self.assertEqual(confirmed.status, "supported")
        self.assertEqual(confirmed.label, "verified_source")
        self.assertEqual(confirmed.confirmed_by, "Educator Kim")
        self.assertEqual(self.ledger.unconfirmed_assumptions("org:mercy"), ())

    def test_only_awaiting_assumptions_can_be_confirmed(self):
        supported = self.ledger.record_claim(
            "org:mercy",
            "Policy requires hourly rounding.",
            "local_policy",
            source_ids=("policy-falls-2026",),
        )
        with self.assertRaises(EvidenceError):
            self.ledger.confirm_assumption(
                supported.claim_id, ("policy-falls-2026",), "Kim", "2026-07-28"
            )

    def test_claim_text_is_privacy_screened(self):
        claim = self.ledger.record_claim(
            "org:mercy",
            "Rounding helped the patient with MRN: A123456.",
            "user_provided_context",
        )
        self.assertNotIn("A123456", claim.text)

    def test_bibliography_covers_supported_claims_only(self):
        self.ledger.record_claim(
            "org:mercy",
            "Policy requires hourly rounding.",
            "local_policy",
            source_ids=("policy-falls-2026",),
        )
        self.ledger.record_claim(
            "org:mercy",
            "Compliance may be lower at night.",
            "assumption_requiring_confirmation",
        )
        bibliography = self.ledger.bibliography("org:mercy")
        self.assertEqual(len(bibliography), 1)
        self.assertIn("Falls Prevention Policy", bibliography[0])
        self.assertIn("effective 2026-01-01", bibliography[0])
        self.assertEqual(self.ledger.bibliography("personal:rn-1"), ())


class CompareGuidelinesTests(unittest.TestCase):
    def make_version(self, source_id, effective, content, jurisdiction="US",
                     doc_type="policy"):
        return KnowledgeSource(
            source_id=source_id,
            title="Falls Prevention Policy",
            doc_type=doc_type,
            effective_date=effective,
            expires_date=None,
            jurisdiction=jurisdiction,
            content=content,
            tenant="org:mercy",
        )

    def test_added_and_removed_statements_are_detected(self):
        old = self.make_version(
            "falls-v1",
            "2025-01-01",
            "Hourly rounding is required. Bed alarms for high-risk patients.",
        )
        new = self.make_version(
            "falls-v2",
            "2026-01-01",
            "Hourly rounding is required. Fall risk is reassessed every shift.",
        )
        diff = compare_guidelines(old, new)
        self.assertEqual(diff["added"], ["Fall risk is reassessed every shift."])
        self.assertEqual(
            diff["removed"], ["Bed alarms for high-risk patients."]
        )
        self.assertEqual(diff["unchanged_count"], 1)
        self.assertEqual(diff["warnings"], ())

    def test_identical_versions_show_no_changes(self):
        old = self.make_version("v1", "2025-01-01", "Hourly rounding is required.")
        new = self.make_version("v2", "2026-01-01", "Hourly rounding is required.")
        diff = compare_guidelines(old, new)
        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])
        self.assertEqual(diff["unchanged_count"], 1)

    def test_backwards_date_order_is_warned(self):
        newer = self.make_version("v2", "2026-01-01", "A. B.")
        older = self.make_version("v1", "2025-01-01", "A. C.")
        diff = compare_guidelines(newer, older)
        self.assertTrue(any(w.startswith("DIRECTION") for w in diff["warnings"]))

    def test_jurisdiction_and_doc_type_changes_are_warned(self):
        old = self.make_version("v1", "2025-01-01", "A.")
        new = self.make_version(
            "v2", "2026-01-01", "A.", jurisdiction="UK", doc_type="research"
        )
        diff = compare_guidelines(old, new)
        self.assertTrue(
            any(w.startswith("JURISDICTION") for w in diff["warnings"])
        )
        self.assertTrue(
            any(w.startswith("DOCUMENT TYPE") for w in diff["warnings"])
        )

    def test_comparison_is_deterministic(self):
        old = self.make_version("v1", "2025-01-01", "B. A. C.")
        new = self.make_version("v2", "2026-01-01", "C. D. B.")
        first = compare_guidelines(old, new)
        second = compare_guidelines(old, new)
        self.assertEqual(first, second)
        self.assertEqual(first["added"], ["D."])
        self.assertEqual(first["removed"], ["A."])


if __name__ == "__main__":
    unittest.main()
