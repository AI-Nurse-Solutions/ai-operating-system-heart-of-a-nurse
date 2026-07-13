import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from naio_harness.proposals import ProposalError, ProposalStore

HASH = "a" * 64


class Stage5ProposalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProposalStore(Path(self.tmp.name) / "proposals")
        self.arguments = {"text": "Synthetic public release"}

    def tearDown(self):
        self.tmp.cleanup()

    def create(self, **overrides):
        values = {
            "capability_id": "external.publish",
            "manifest_hash": HASH,
            "policy_version": "2.0.0",
            "dataset_version": "2026.07.13.1",
            "risk_tier": "orange",
            "autonomy_level": "A3",
            "side_effecting": True,
            "idempotent": False,
            "target": "approved-public-destination",
            "arguments": self.arguments,
            "max_attempts": 3,
        }
        values.update(overrides)
        return self.store.create(**values)

    def test_payload_is_not_persisted(self):
        proposal = self.create()
        raw = (self.store.directory / f"proposal-{proposal['proposal_id']}.json").read_text()
        self.assertNotIn(self.arguments["text"], raw)
        self.assertIn(proposal["action_digest"], raw)
        self.assertFalse(self.store.kanban_card(proposal["proposal_id"])["contains_payload"])

    def test_changed_action_invalidates_approval(self):
        proposal = self.create()
        with self.assertRaises(ProposalError):
            self.store.approve(proposal["proposal_id"], "authorized_reviewer", {"text": "changed"})
        self.assertEqual(self.store.load(proposal["proposal_id"])["status"], "pending_review")

    def test_side_effecting_restart_requires_fresh_review(self):
        proposal = self.create()
        self.store.approve(proposal["proposal_id"], "authorized_reviewer", self.arguments)
        self.store.acquire(proposal["proposal_id"], "worker-1", self.arguments)
        reconciled = self.store.reconcile_restart()
        self.assertEqual(len(reconciled), 1)
        recovered = self.store.load(proposal["proposal_id"])
        self.assertEqual(recovered["status"], "needs_review")
        self.assertIsNone(recovered["approval"])
        self.assertIsNone(recovered["lease"])

    def test_idempotent_read_only_work_may_resume(self):
        proposal = self.create(
            capability_id="local.read", risk_tier="green", autonomy_level="A2",
            side_effecting=False, idempotent=True, target="governed-workspace",
            arguments={"path": "public.md"},
        )
        args = {"path": "public.md"}
        self.store.approve(proposal["proposal_id"], "authorized_reviewer", args)
        self.store.acquire(proposal["proposal_id"], "worker-1", args)
        self.store.reconcile_restart()
        self.assertEqual(self.store.load(proposal["proposal_id"])["status"], "approved")

    def test_retry_ceiling_tombstones_after_restart(self):
        proposal = self.create(max_attempts=1)
        self.store.approve(proposal["proposal_id"], "authorized_reviewer", self.arguments)
        self.store.acquire(proposal["proposal_id"], "worker-1", self.arguments)
        self.store.reconcile_restart()
        recovered = self.store.load(proposal["proposal_id"])
        self.assertEqual(recovered["status"], "tombstoned")
        self.assertIn("retry_ceiling", recovered["tombstone_reason"])

    def test_expired_proposal_cannot_be_approved(self):
        proposal = self.create(expires_in_seconds=1)
        future = datetime.now(timezone.utc) + timedelta(seconds=2)
        with self.assertRaises(ProposalError):
            self.store.approve(proposal["proposal_id"], "authorized_reviewer", self.arguments, now=future)
        self.assertEqual(self.store.load(proposal["proposal_id"])["status"], "expired")

    def test_red_risk_cannot_become_executable_proposal(self):
        with self.assertRaises(ProposalError):
            self.create(risk_tier="red", autonomy_level="A0")

    def test_completed_result_is_digest_only_and_ledger_verifies(self):
        proposal = self.create()
        self.store.approve(proposal["proposal_id"], "authorized_reviewer", self.arguments)
        self.store.acquire(proposal["proposal_id"], "worker-1", self.arguments)
        completed = self.store.complete(proposal["proposal_id"], {"status": "sent", "remote_id": "synthetic"})
        self.assertEqual(completed["status"], "executed")
        self.assertEqual(len(completed["result_digest"]), 64)
        self.assertTrue(self.store.ledger.verify()["ok"])


if __name__ == "__main__":
    unittest.main()
