import unittest

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    Decision,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.policy import EdenaPolicyEngine


def make_request(**overrides):
    actor = overrides.pop(
        "actor",
        Actor(actor_id="rn-1", role="nurse", tenant="personal:rn-1"),
    )
    defaults = dict(
        request_id="req-1",
        actor=actor,
        intent="summarize_policy",
        content="public educational content",
        risk_tier=RiskTier.GREEN,
        data_class=DataClass.D0,
        action_mode=ActionMode.DRAFT,
    )
    defaults.update(overrides)
    return GatewayRequest(**defaults)


class PolicyEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = EdenaPolicyEngine()

    def test_green_d0_draft_is_allowed(self):
        decision = self.engine.decide(make_request())
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertIn("EDENA-WITHIN-SCOPE", decision.reason_codes)

    def test_green_cannot_accept_higher_data_classes(self):
        for data_class in (DataClass.D1, DataClass.D2, DataClass.D3, DataClass.D4):
            decision = self.engine.decide(make_request(data_class=data_class))
            self.assertIs(decision.decision, Decision.DENY, data_class)
            self.assertIn("EDENA-DATA-CLASS-CEILING", decision.reason_codes)

    def test_yellow_may_analyze_deidentified_institutional_information(self):
        decision = self.engine.decide(
            make_request(
                risk_tier=RiskTier.YELLOW,
                data_class=DataClass.D2,
                action_mode=ActionMode.RECOMMEND,
            )
        )
        self.assertIs(decision.decision, Decision.ALLOW)

    def test_yellow_cannot_accept_phi_class_data(self):
        decision = self.engine.decide(
            make_request(risk_tier=RiskTier.YELLOW, data_class=DataClass.D3)
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-DATA-CLASS-CEILING", decision.reason_codes)

    def test_yellow_cannot_prepare_actions(self):
        decision = self.engine.decide(
            make_request(risk_tier=RiskTier.YELLOW, action_mode=ActionMode.PREPARE_ACTION)
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-ACTION-MODE-CEILING", decision.reason_codes)

    def test_orange_requires_authenticated_org_context(self):
        decision = self.engine.decide(
            make_request(risk_tier=RiskTier.ORANGE, data_class=DataClass.D2)
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-ORG-CONTEXT-REQUIRED", decision.reason_codes)

    def test_orange_requires_recorded_approval(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
        )
        decision = self.engine.decide(
            make_request(actor=actor, risk_tier=RiskTier.ORANGE, data_class=DataClass.D2)
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-APPROVAL-REQUIRED", decision.reason_codes)

    def test_orange_with_org_and_approval_is_allowed_and_audited(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(actor=actor, risk_tier=RiskTier.ORANGE, data_class=DataClass.D2)
        )
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertIn("continuous_audit", decision.obligations)

    def test_external_side_effects_require_meaningful_approval(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.ORANGE,
                action_mode=ActionMode.ACT_WITH_APPROVAL,
                intent="send_update_email",
            )
        )
        self.assertIs(decision.decision, Decision.REQUIRE_APPROVAL)
        self.assertIn("EDENA-SIDE-EFFECT-GATE", decision.reason_codes)

    def test_side_effect_with_recorded_approval_id_is_allowed_and_logged(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.ORANGE,
                action_mode=ActionMode.ACT_WITH_APPROVAL,
                intent="send_update_email",
                metadata={"approval_id": "appr-77"},
            )
        )
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertIn("log_side_effect", decision.obligations)

    def test_fabricated_approval_id_is_denied_not_reprompted(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.ORANGE,
                action_mode=ActionMode.ACT_WITH_APPROVAL,
                intent="send_update_email",
                metadata={"approval_id": "appr-FORGED"},
            )
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-APPROVAL-UNRECOGNIZED", decision.reason_codes)

    def test_prepare_action_always_routes_to_approval(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.ORANGE,
                action_mode=ActionMode.PREPARE_ACTION,
            )
        )
        self.assertIs(decision.decision, Decision.REQUIRE_APPROVAL)

    def test_red_p_is_prohibited_at_every_action_mode(self):
        for mode in ActionMode:
            decision = self.engine.decide(
                make_request(risk_tier=RiskTier.RED_P, action_mode=mode)
            )
            self.assertIs(decision.decision, Decision.DENY, mode)
            self.assertIn("EDENA-PROHIBITED-TIER", decision.reason_codes)

    def test_unrestricted_autonomy_is_prohibited_at_every_tier(self):
        for tier in (RiskTier.GREEN, RiskTier.YELLOW, RiskTier.ORANGE, RiskTier.RED_E):
            decision = self.engine.decide(
                make_request(risk_tier=tier, action_mode=ActionMode.UNRESTRICTED_AUTONOMY)
            )
            self.assertIs(decision.decision, Decision.DENY, tier)
            self.assertIn("EDENA-UNRESTRICTED-AUTONOMY", decision.reason_codes)

    def test_red_e_requires_institutional_controls(self):
        actor = Actor(
            actor_id="charge-1",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-90",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.RED_E,
                action_mode=ActionMode.CONSTRAINED_AUTONOMY,
                metadata={"institutional_controls": ("kill_switch",)},
            )
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-INSTITUTIONAL-CONTROLS", decision.reason_codes)

    def test_red_e_with_full_controls_allows_constrained_autonomy(self):
        actor = Actor(
            actor_id="charge-1",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-90",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.RED_E,
                action_mode=ActionMode.CONSTRAINED_AUTONOMY,
                metadata={
                    "institutional_controls": (
                        "kill_switch",
                        "audit_stream",
                        "named_accountable_human",
                    )
                },
            )
        )
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertIn("continuous_audit", decision.obligations)
        self.assertIn("log_side_effect", decision.obligations)

    def test_constrained_autonomy_is_red_e_only(self):
        actor = Actor(
            actor_id="rn-2",
            role="nurse",
            tenant="org:mercy",
            authenticated_org="org:mercy",
            approvals=("appr-77",),
        )
        decision = self.engine.decide(
            make_request(
                actor=actor,
                risk_tier=RiskTier.ORANGE,
                action_mode=ActionMode.CONSTRAINED_AUTONOMY,
            )
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-ACTION-MODE-CEILING", decision.reason_codes)

    def test_student_mode_cannot_generate_patient_specific_recommendations(self):
        student = Actor(actor_id="sn-1", role="student", tenant="personal:sn-1")
        decision = self.engine.decide(
            make_request(actor=student, intent="patient_specific_recommendation")
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-STUDENT-MODE", decision.reason_codes)

    def test_student_mode_is_capped_at_draft(self):
        student = Actor(actor_id="sn-1", role="student", tenant="personal:sn-1")
        decision = self.engine.decide(
            make_request(
                actor=student,
                risk_tier=RiskTier.YELLOW,
                action_mode=ActionMode.RECOMMEND,
            )
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-STUDENT-MODE", decision.reason_codes)

    def test_student_drafting_stays_available(self):
        student = Actor(actor_id="sn-1", role="student", tenant="personal:sn-1")
        decision = self.engine.decide(make_request(actor=student))
        self.assertIs(decision.decision, Decision.ALLOW)

    def test_memory_cannot_cross_tenant_boundaries(self):
        decision = self.engine.decide(
            make_request(target_tenant="org:other-hospital")
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-TENANT-BOUNDARY", decision.reason_codes)

    def test_same_tenant_target_is_not_a_boundary_violation(self):
        decision = self.engine.decide(make_request(target_tenant="personal:rn-1"))
        self.assertIs(decision.decision, Decision.ALLOW)

    def test_engine_fails_closed_on_internal_error(self):
        self.engine.policy.pop("tier_data_ceilings")
        decision = self.engine.decide(make_request())
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-EVALUATOR-ERROR", decision.reason_codes)


if __name__ == "__main__":
    unittest.main()
