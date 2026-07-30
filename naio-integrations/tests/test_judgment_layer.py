import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    Decision,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.gateway import EdenaPolicyGateway
from naio_integrations.judgment import JudgmentGuide

NURSE = Actor(actor_id="rn-1", role="nurse", tenant="personal:rn-1")
STUDENT = Actor(actor_id="sn-1", role="pre-licensure-student", tenant="personal:sn-1")


def make_request(**overrides) -> GatewayRequest:
    defaults = dict(
        request_id="jdg-1",
        actor=NURSE,
        intent="summarize_policy",
        content="Summarize the unit falls policy for a huddle.",
        risk_tier=RiskTier.GREEN,
        data_class=DataClass.D0,
        action_mode=ActionMode.DRAFT,
    )
    defaults.update(overrides)
    return GatewayRequest(**defaults)


class FrameAndProbeTests(unittest.TestCase):
    def setUp(self):
        self.guide = JudgmentGuide()

    def test_intents_map_to_their_thinking_frames(self):
        cases = {
            "sandbox_case_review": "clinical_judgment",
            "process_improvement": "systems",
            "education_plan": "design",
            "evidence_question": "evidence",
            "totally_unmapped_intent": "general",
        }
        for intent, frame in cases.items():
            self.assertEqual(
                self.guide.frame_for(make_request(intent=intent)), frame, intent
            )

    def test_user_may_choose_a_frame_explicitly(self):
        request = make_request(
            intent="summarize_policy", metadata={"thinking_frame": "systems"}
        )
        self.assertEqual(self.guide.frame_for(request), "systems")

    def test_unknown_frame_override_falls_back_safely(self):
        request = make_request(metadata={"thinking_frame": "mind_reading"})
        self.assertEqual(self.guide.frame_for(request), "evidence")

    def test_probe_selection_is_deterministic_per_request(self):
        request = make_request(request_id="stable-1", intent="process_improvement")
        first = self.guide.guidance(request).probe
        second = self.guide.guidance(request).probe
        self.assertEqual(first, second)
        self.assertIn(
            first, self.guide.config["frames"]["systems"]["probes"]
        )

    def test_students_are_coach_first_by_default(self):
        plain_student = Actor(actor_id="s-1", role="student", tenant="personal:s-1")
        self.assertTrue(
            self.guide.guidance(make_request(actor=plain_student)).coach_first
        )
        aliased = JudgmentGuide(role_aliases={"pre-licensure-student": "student"})
        self.assertTrue(aliased.guidance(make_request(actor=STUDENT)).coach_first)
        self.assertFalse(self.guide.guidance(make_request()).coach_first)

    def test_any_role_may_opt_into_coach_first(self):
        request = make_request(metadata={"thinking_posture": "coach_first"})
        self.assertTrue(self.guide.guidance(request).coach_first)

    def test_notice_carries_the_doctrine(self):
        notice = self.guide.guidance(make_request()).notice
        self.assertIn("Agents propose. Humans judge. Nurses steward.", notice)
        self.assertIn("feature", notice)


class ReasoningLedgerTests(unittest.TestCase):
    def setUp(self):
        self.guide = JudgmentGuide()

    def test_naked_verdict_is_detected(self):
        ledger = self.guide.ledger("You should adopt hourly rounding. It is the best option.")
        self.assertTrue(ledger.decision_shaped)
        self.assertFalse(ledger.visible_reasoning)
        self.assertEqual(
            ledger.missing, ("assumptions", "alternatives", "change_conditions")
        )

    def test_visible_reasoning_is_credited(self):
        ledger = self.guide.ledger(
            "I recommend hourly rounding. This assumes current staffing holds. "
            "Another option is targeted rounding for high-risk patients. "
            "Revisit if fall rates do not move within one quarter."
        )
        self.assertTrue(ledger.decision_shaped)
        self.assertTrue(ledger.assumptions_stated)
        self.assertTrue(ledger.alternatives_stated)
        self.assertTrue(ledger.change_conditions_stated)
        self.assertEqual(ledger.missing, ())

    def test_descriptive_output_is_not_decision_shaped(self):
        ledger = self.guide.ledger("The policy describes rounding frequency and documentation.")
        self.assertFalse(ledger.decision_shaped)


class GatewayEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gateway = EdenaPolicyGateway(trace_root=Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def _yellow_recommend(self, **overrides) -> GatewayRequest:
        defaults = dict(
            risk_tier=RiskTier.YELLOW,
            data_class=DataClass.D2,
            action_mode=ActionMode.RECOMMEND,
            intent="process_improvement",
            content="How should we reduce falls on the unit?",
        )
        defaults.update(overrides)
        return make_request(**defaults)

    def test_consequential_naked_verdict_is_refused(self):
        result = self.gateway.submit(
            self._yellow_recommend(),
            executor=lambda _r: "You should adopt hourly rounding. It is the best option.",
        )
        self.assertIs(result.decision, Decision.DENY)
        self.assertIn("EDENA-JUDGMENT-VISIBILITY", result.reason_codes)
        self.assertEqual(result.stage, "judgment_ledger")
        self.assertIsNone(result.output)
        self.assertIsNotNone(result.reasoning_ledger)

    def test_recommendation_with_judgment_material_passes(self):
        result = self.gateway.submit(
            self._yellow_recommend(),
            executor=lambda _r: (
                "I recommend hourly rounding. This assumes current staffing "
                "holds. Another option is targeted rounding for high-risk "
                "patients. Revisit if fall rates do not move in one quarter."
            ),
        )
        self.assertIs(result.decision, Decision.ALLOW)
        self.assertTrue(result.reasoning_ledger.visible_reasoning)
        self.assertEqual(result.judgment.frame, "systems")

    def test_green_drafting_is_not_gated_but_still_framed(self):
        result = self.gateway.submit(
            make_request(intent="education_plan"),
            executor=lambda _r: "You should start with objectives.",
        )
        self.assertIs(result.decision, Decision.ALLOW)
        self.assertEqual(result.judgment.frame, "design")
        self.assertIn(
            "Agents propose. Humans judge. Nurses steward.", result.judgment.notice
        )

    def test_every_outcome_carries_the_frame_and_probe(self):
        denied = self.gateway.submit(
            make_request(
                actor=STUDENT,
                intent="patient_specific_recommendation",
                content="What should I do for this patient?",
            )
        )
        self.assertIs(denied.decision, Decision.DENY)
        self.assertIsNotNone(denied.judgment)
        self.assertTrue(denied.judgment.coach_first)
        self.assertTrue(denied.judgment.probe)

    def test_judgment_spans_carry_no_content(self):
        self.gateway.submit(
            self._yellow_recommend(request_id="jdg-span"),
            executor=lambda _r: "You should adopt hourly rounding. It is the best option.",
        )
        records = self.gateway.tracer.read("personal:rn-1")
        span_names = [r.get("name") for r in records if r.get("kind") == "span"]
        self.assertIn("judgment_frame", span_names)
        self.assertIn("judgment_ledger", span_names)
        self.assertNotIn("hourly rounding", json.dumps(records))

    def test_reason_code_is_documented_in_policy_config(self):
        reason_codes = self.gateway.policy.policy["reason_codes"]
        self.assertIn("EDENA-JUDGMENT-VISIBILITY", reason_codes)


if __name__ == "__main__":
    unittest.main()
