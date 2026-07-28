import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    DataClass,
    Decision,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.identity import IdentityError, MultiRoleIdentity
from naio_integrations.policy import EdenaPolicyEngine


class MultiRoleIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "identity.json"
        self.identity = MultiRoleIdentity("rn-avery", self.state)

    def tearDown(self):
        self.tmp.cleanup()

    def activate_icu_nurse_preceptor_qi_lead(self):
        """The spec section 9 example: one ICU nurse wearing three hats."""
        self.identity.activate_role("staff-nurse")
        self.identity.activate_role("educator")
        self.identity.activate_role("leader")
        self.identity.add_project(
            "falls-qi", "Falls reduction PDSA", roles=("staff-nurse", "leader")
        )
        self.identity.add_project(
            "orientee-plan", "Orientee ramp-up plan", roles=("educator",)
        )
        self.identity.add_competency("precepting", "Precepting and feedback")
        self.identity.set_competency_application(
            "precepting", "educator", "Coach orientees using SBI feedback."
        )
        self.identity.set_competency_application(
            "precepting", "staff-nurse", "Model bedside teach-back on shift."
        )
        self.identity.add_inbox_item("Committee minutes to review")
        self.identity.add_calendar_entry("2026-08-01 falls huddle")
        self.identity.add_portfolio_item("Falls poster draft")

    def test_one_identity_holds_multiple_role_lenses(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        self.assertEqual(
            self.identity.roles(), ("staff-nurse", "educator", "leader")
        )
        self.assertEqual(self.identity.active_role, "staff-nurse")

    def test_unknown_roles_fail_closed(self):
        with self.assertRaises(IdentityError):
            self.identity.activate_role("shadow-admin")
        with self.assertRaises(IdentityError):
            self.identity.switch_role("educator")

    def test_shared_stores_are_never_duplicated_across_lenses(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        nurse_view = self.identity.view("staff-nurse")
        leader_view = self.identity.view("leader")
        educator_view = self.identity.view("educator")
        # The same project object serves both tagged lenses.
        self.assertIs(
            nurse_view["projects"]["falls-qi"], leader_view["projects"]["falls-qi"]
        )
        self.assertNotIn("falls-qi", educator_view["projects"])
        # Inbox, calendar, and portfolio are the same single stores.
        for key in ("inbox", "calendar", "portfolio"):
            self.assertIs(nurse_view[key], educator_view[key], key)

    def test_spec_example_each_hat_sees_its_own_work(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        self.assertIn("falls-qi", self.identity.view("staff-nurse")["projects"])
        self.assertIn("orientee-plan", self.identity.view("educator")["projects"])
        self.assertIn("falls-qi", self.identity.view("leader")["projects"])

    def test_shared_competency_appears_once_with_role_specific_application(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        educator = self.identity.view("educator")["competencies"]["precepting"]
        nurse = self.identity.view("staff-nurse")["competencies"]["precepting"]
        self.assertEqual(educator["name"], nurse["name"])
        self.assertIn("SBI", educator["application"])
        self.assertIn("teach-back", nurse["application"])
        leader = self.identity.view("leader")["competencies"]["precepting"]
        self.assertIsNone(leader["application"])

    def test_role_switching_preserves_shared_content_and_layouts(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        self.identity.remember_layout(
            "educator", {"home_cards": ["feedback-queue", "learner-followups"]}
        )
        self.identity.switch_role("educator")
        self.assertEqual(self.identity.active_role, "educator")
        educator_layout = self.identity.layout_for("educator")
        self.assertTrue(educator_layout["remembered"])
        self.assertIn("learner-followups", educator_layout["home_cards"])
        self.identity.switch_role("staff-nurse")
        # Shared content survived the switches; educator layout is still remembered.
        self.assertIn("Committee minutes to review", self.identity.view()["inbox"])
        self.assertTrue(self.identity.layout_for("educator")["remembered"])

    def test_default_layouts_come_from_the_packet_catalog(self):
        self.identity.activate_role("staff-nurse")
        layout = self.identity.layout_for("staff-nurse")
        self.assertFalse(layout["remembered"])
        self.assertIn("workflow-friction-log", layout["home_cards"])
        self.assertIn("edena-guardrails", layout["home_cards"])

    def test_permissions_follow_workspace_not_title(self):
        engine = EdenaPolicyEngine()
        self.identity.activate_role("leader")
        # A leader hat in a personal workspace grants nothing Orange:
        # no authenticated organizational context means deny.
        actor = self.identity.actor_for("personal:rn-avery")
        decision = engine.decide(
            GatewayRequest(
                request_id="req-1",
                actor=actor,
                intent="workforce_summary",
                content="Summarize aggregate staffing readiness.",
                risk_tier=RiskTier.ORANGE,
                data_class=DataClass.D2,
                action_mode=ActionMode.RECOMMEND,
            )
        )
        self.assertIs(decision.decision, Decision.DENY)
        self.assertIn("EDENA-ORG-CONTEXT-REQUIRED", decision.reason_codes)
        # The same identity in an authenticated org workspace with a
        # recorded approval is permitted: context grants, not title.
        authorized = self.identity.actor_for(
            "org:mercy", authenticated_org="org:mercy", approvals=("appr-31",)
        )
        allowed = engine.decide(
            GatewayRequest(
                request_id="req-2",
                actor=authorized,
                intent="workforce_summary",
                content="Summarize aggregate staffing readiness.",
                risk_tier=RiskTier.ORANGE,
                data_class=DataClass.D2,
                action_mode=ActionMode.RECOMMEND,
            )
        )
        self.assertIs(allowed.decision, Decision.ALLOW)

    def test_student_lens_carries_the_student_policy_gates(self):
        engine = EdenaPolicyEngine()
        self.identity.activate_role("pre-licensure-student")
        actor = self.identity.actor_for("personal:rn-avery")
        self.assertEqual(actor.role, "pre-licensure-student")
        blocked = engine.decide(
            GatewayRequest(
                request_id="req-3",
                actor=actor,
                intent="patient_specific_recommendation",
                content="What should I do for the patient in my clinical today?",
                risk_tier=RiskTier.GREEN,
                data_class=DataClass.D0,
                action_mode=ActionMode.DRAFT,
            )
        )
        self.assertIs(blocked.decision, Decision.DENY)
        self.assertIn("EDENA-STUDENT-MODE", blocked.reason_codes)
        studying = engine.decide(
            GatewayRequest(
                request_id="req-4",
                actor=actor,
                intent="summarize_policy",
                content="Explain the falls policy in study terms.",
                risk_tier=RiskTier.GREEN,
                data_class=DataClass.D0,
                action_mode=ActionMode.DRAFT,
            )
        )
        self.assertIs(studying.decision, Decision.ALLOW)

    def test_org_login_cannot_be_carried_into_a_mismatched_workspace(self):
        self.identity.activate_role("leader")
        with self.assertRaises(IdentityError):
            self.identity.actor_for(
                "personal:rn-avery", authenticated_org="org:mercy"
            )

    def test_cross_role_suggestions_are_off_by_default_and_explained_when_on(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        self.identity.switch_role("educator")
        self.assertEqual(self.identity.suggestions(), ())
        self.identity.enable_cross_role_suggestions(True)
        suggestions = self.identity.suggestions()
        self.assertTrue(suggestions)
        for suggestion in suggestions:
            self.assertTrue(suggestion["because"], suggestion)
        references = {s["reference"] for s in suggestions}
        self.assertIn("falls-qi", references)

    def test_state_is_durable_across_restarts(self):
        self.activate_icu_nurse_preceptor_qi_lead()
        self.identity.switch_role("leader")
        resumed = MultiRoleIdentity("rn-avery", self.state)
        self.assertEqual(resumed.active_role, "leader")
        self.assertEqual(resumed.roles(), ("staff-nurse", "educator", "leader"))
        self.assertIn("falls-qi", resumed.view("leader")["projects"])

    def test_state_file_cannot_be_hijacked_by_another_identity(self):
        self.identity.activate_role("staff-nurse")
        with self.assertRaises(IdentityError):
            MultiRoleIdentity("someone-else", self.state)

    def test_projects_require_at_least_one_activated_role_tag(self):
        self.identity.activate_role("staff-nurse")
        with self.assertRaises(IdentityError):
            self.identity.add_project("p1", "Untagged", roles=())
        with self.assertRaises(IdentityError):
            self.identity.add_project("p2", "Wrong hat", roles=("leader",))

    def test_the_last_role_cannot_be_deactivated(self):
        self.identity.activate_role("staff-nurse")
        with self.assertRaises(IdentityError):
            self.identity.deactivate_role("staff-nurse")
        self.identity.activate_role("educator")
        self.identity.switch_role("educator")
        self.identity.deactivate_role("educator")
        self.assertEqual(self.identity.active_role, "staff-nurse")


if __name__ == "__main__":
    unittest.main()
