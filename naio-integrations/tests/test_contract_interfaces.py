import unittest

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    Decision,
    GatewayRequest,
    KnowledgeRetrievalInterface,
    MemoryInterface,
    ObservabilityInterface,
    OrchestrationInterface,
    PolicyDecision,
    PolicyDecisionInterface,
    PrivacyTransformationInterface,
    RiskTier,
    ValidationInterface,
)


class DirectiveTaxonomyTests(unittest.TestCase):
    def test_risk_tiers_match_directive_v1_1(self):
        self.assertEqual(
            [tier.value for tier in RiskTier],
            ["green", "yellow", "orange", "red-p", "red-e"],
        )

    def test_data_classes_are_d0_through_d4(self):
        self.assertEqual([d.value for d in DataClass], ["D0", "D1", "D2", "D3", "D4"])
        self.assertEqual(DataClass.D3.rank, 3)

    def test_action_modes_rank_monotonically(self):
        ranks = [mode.rank for mode in ActionMode]
        self.assertEqual(ranks, sorted(ranks))
        self.assertGreater(ActionMode.CONSTRAINED_AUTONOMY.rank, ActionMode.DRAFT.rank)

    def test_side_effects_begin_at_prepare_action(self):
        self.assertFalse(ActionMode.OBSERVE.has_side_effects)
        self.assertFalse(ActionMode.RECOMMEND.has_side_effects)
        self.assertTrue(ActionMode.PREPARE_ACTION.has_side_effects)
        self.assertTrue(ActionMode.ACT_WITH_APPROVAL.has_side_effects)
        self.assertTrue(ActionMode.UNRESTRICTED_AUTONOMY.has_side_effects)

    def test_unrestricted_autonomy_exists_only_to_be_prohibited(self):
        self.assertIn(ActionMode.UNRESTRICTED_AUTONOMY, list(ActionMode))


class ContractShapeTests(unittest.TestCase):
    def test_requests_and_decisions_are_immutable(self):
        actor = Actor(actor_id="rn-1", role="nurse", tenant="personal:rn-1")
        request = GatewayRequest(
            request_id="req-1",
            actor=actor,
            intent="summarize_policy",
            content="hello",
            risk_tier=RiskTier.GREEN,
            data_class=DataClass.D0,
            action_mode=ActionMode.DRAFT,
        )
        with self.assertRaises(AttributeError):
            request.content = "mutated"
        decision = PolicyDecision(decision=Decision.ALLOW, reason_codes=("OK",))
        with self.assertRaises(AttributeError):
            decision.decision = Decision.DENY
        self.assertTrue(decision.allowed)

    def test_all_six_interfaces_are_abstract(self):
        for interface in (
            PolicyDecisionInterface,
            PrivacyTransformationInterface,
            ValidationInterface,
            ObservabilityInterface,
            MemoryInterface,
            KnowledgeRetrievalInterface,
            OrchestrationInterface,
        ):
            with self.assertRaises(TypeError, msg=interface.__name__):
                interface()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
