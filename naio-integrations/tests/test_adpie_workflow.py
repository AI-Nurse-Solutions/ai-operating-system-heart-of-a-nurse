import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.orchestration import AdpieWorkflow, WorkflowError


class AdpieWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = AdpieWorkflow(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, workflow_id="unit-improvement-1"):
        return self.runtime.start(workflow_id, {"project": "falls huddle redesign"})

    def test_workflow_starts_in_assessment(self):
        state = self.start()
        self.assertEqual(state["stage"], "assess")
        self.assertEqual(state["status"], "running")

    def test_duplicate_workflow_ids_are_rejected(self):
        self.start()
        with self.assertRaises(WorkflowError):
            self.start()

    def test_workflow_pauses_at_the_human_authorization_gate(self):
        self.start()
        self.runtime.advance("unit-improvement-1", findings="3 falls last month")
        self.runtime.advance("unit-improvement-1", problem="rounding gaps on nights")
        state = self.runtime.advance("unit-improvement-1", plan="hourly rounding pilot")
        self.assertEqual(state["stage"], "human_authorization")
        self.assertEqual(state["status"], "awaiting_authorization")
        with self.assertRaises(WorkflowError):
            self.runtime.advance("unit-improvement-1", sneak="past the gate")

    def test_authorization_requires_a_named_human(self):
        self.start()
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        with self.assertRaises(WorkflowError):
            self.runtime.authorize("unit-improvement-1", approver="", approved=True)
        with self.assertRaises(WorkflowError):
            self.runtime.authorize("unit-improvement-1", approver="   ", approved=True)

    def test_authorization_approval_must_be_an_explicit_boolean(self):
        self.start()
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        for truthy_nonbool in ("false", 1, "yes"):
            with self.assertRaises(WorkflowError):
                self.runtime.authorize(
                    "unit-improvement-1", approver="charge-nurse-lee", approved=truthy_nonbool
                )

    def test_declined_authorization_returns_to_planning(self):
        self.start()
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        state = self.runtime.authorize(
            "unit-improvement-1", approver="charge-nurse-lee", approved=False
        )
        self.assertEqual(state["stage"], "plan")
        self.assertFalse(state["authorization"]["approved"])

    def test_full_lifecycle_reaches_complete(self):
        self.start()
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        self.runtime.authorize(
            "unit-improvement-1", approver="charge-nurse-lee", approved=True
        )
        self.runtime.advance("unit-improvement-1", implemented="pilot live on nights")
        self.runtime.advance("unit-improvement-1", outcome="falls down 40%")
        state = self.runtime.advance("unit-improvement-1", lesson="keep the pilot")
        self.assertEqual(state["stage"], "complete")
        self.assertEqual(state["status"], "complete")
        with self.assertRaises(WorkflowError):
            self.runtime.advance("unit-improvement-1")

    def test_workflow_is_resumable_from_durable_checkpoints(self):
        self.start()
        self.runtime.advance("unit-improvement-1", findings="baseline gathered")
        resumed = AdpieWorkflow(Path(self.tmp.name))
        state = resumed.state("unit-improvement-1")
        self.assertEqual(state["stage"], "diagnose")
        self.assertEqual(
            state["stage_outputs"]["assess"], {"findings": "baseline gathered"}
        )
        advanced = resumed.advance("unit-improvement-1", problem="confirmed gaps")
        self.assertEqual(advanced["stage"], "plan")

    def test_history_records_every_transition(self):
        self.start()
        self.runtime.advance("unit-improvement-1")
        state = self.runtime.state("unit-improvement-1")
        events = [entry["event"] for entry in state["history"]]
        self.assertEqual(events[0], "started")
        self.assertIn("advanced", events)

    def test_reassess_loops_back_for_cyclical_improvement(self):
        self.start()
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        self.runtime.authorize(
            "unit-improvement-1", approver="charge-nurse-lee", approved=True
        )
        for _ in range(3):
            self.runtime.advance("unit-improvement-1")
        state = self.runtime.reassess("unit-improvement-1")
        self.assertEqual(state["stage"], "assess")
        self.assertIsNone(state["authorization"])

    def test_reassess_only_from_learn_or_complete(self):
        self.start()
        with self.assertRaises(WorkflowError):
            self.runtime.reassess("unit-improvement-1")

    def test_unknown_and_malformed_workflow_ids_fail(self):
        with self.assertRaises(WorkflowError):
            self.runtime.state("never-started")
        with self.assertRaises(WorkflowError):
            self.runtime.start("../escape", {})


if __name__ == "__main__":
    unittest.main()
