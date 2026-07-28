import unittest

import _bootstrap  # noqa: F401

from naio_integrations.contract import KnowledgeSource
from naio_integrations.knowledge import GovernedKnowledge

TODAY = "2026-07-28"


def make_sources():
    return [
        KnowledgeSource(
            source_id="policy-falls-2026",
            title="Falls Prevention Policy",
            doc_type="policy",
            effective_date="2026-01-01",
            expires_date="2027-01-01",
            jurisdiction="US",
            content="Hourly rounding and bed alarms are required for falls prevention.",
            tenant="org:mercy",
        ),
        KnowledgeSource(
            source_id="policy-falls-2019",
            title="Falls Prevention Policy (legacy)",
            doc_type="policy",
            effective_date="2019-01-01",
            expires_date="2021-01-01",
            jurisdiction="US",
            content="Legacy falls prevention guidance with quarterly rounding.",
            tenant="org:mercy",
        ),
        KnowledgeSource(
            source_id="research-falls-2025",
            title="Falls interventions meta-analysis",
            doc_type="research",
            effective_date="2025-06-01",
            expires_date=None,
            jurisdiction="US",
            content="Meta-analysis of falls prevention interventions in acute care.",
            tenant="org:mercy",
        ),
        KnowledgeSource(
            source_id="policy-uk-meds",
            title="Medication rounds guidance",
            doc_type="policy",
            effective_date="2026-02-01",
            expires_date=None,
            jurisdiction="UK",
            content="UK-specific medication rounds and falls documentation guidance.",
            tenant="org:mercy",
        ),
    ]


class GovernedKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.knowledge = GovernedKnowledge(home_jurisdiction="US")
        self.assertEqual(self.knowledge.index(make_sources()), 4)

    def test_answers_show_exact_source_and_dates(self):
        answer = self.knowledge.retrieve("org:mercy", "falls prevention rounding", TODAY)
        self.assertFalse(answer.refused)
        top = answer.passages[0]
        self.assertEqual(top["source_id"], "policy-falls-2026")
        self.assertEqual(top["effective_date"], "2026-01-01")
        self.assertIn("matched_terms", top)

    def test_policy_outranks_research(self):
        answer = self.knowledge.retrieve("org:mercy", "falls prevention", TODAY)
        types = [passage["doc_type"] for passage in answer.passages]
        self.assertEqual(types.index("policy"), 0)
        self.assertLess(types.index("policy"), types.index("research"))

    def test_expired_policy_carries_a_warning(self):
        answer = self.knowledge.retrieve("org:mercy", "falls prevention", TODAY)
        expired = [w for w in answer.warnings if w.startswith("EXPIRED")]
        self.assertTrue(expired)
        self.assertIn("policy-falls-2019", expired[0])

    def test_foreign_jurisdiction_carries_a_warning(self):
        answer = self.knowledge.retrieve("org:mercy", "medication rounds falls", TODAY)
        jurisdiction = [w for w in answer.warnings if w.startswith("JURISDICTION")]
        self.assertTrue(jurisdiction)
        self.assertIn("policy-uk-meds", jurisdiction[0])

    def test_mixed_policy_and_research_evidence_is_flagged(self):
        answer = self.knowledge.retrieve("org:mercy", "falls prevention", TODAY)
        self.assertTrue(any(w.startswith("MIXED EVIDENCE") for w in answer.warnings))

    def test_unsupported_questions_are_refused_not_answered(self):
        answer = self.knowledge.retrieve("org:mercy", "ventilator weaning protocol", TODAY)
        self.assertTrue(answer.refused)
        self.assertEqual(answer.passages, ())
        self.assertIn("refusing", answer.refusal_reason)

    def test_retrieval_never_crosses_tenants(self):
        answer = self.knowledge.retrieve("personal:rn-1", "falls prevention", TODAY)
        self.assertTrue(answer.refused)


if __name__ == "__main__":
    unittest.main()
