# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0

"""Competing processes claim one approval, execution, and final receipt."""

import multiprocessing
import sqlite3
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager.actions import ActionBoundary, ActionError, StaleApproval, write_markdown_export
from nurse_manager.brief import BriefService
from nurse_manager.sample import load_sample
from nurse_manager.services import ManagerWorkspace

OWNER = "me"


def competing_request(root, action_id, operation, barrier, results, entered, release):
    ws = ManagerWorkspace(Path(root))
    try:
        def handler(path, text):
            with (Path(root) / "effect-count").open("a", encoding="utf-8") as log:
                log.write("effect\n")
            digest = write_markdown_export(path, text)
            entered.set()
            if not release.wait(15):
                raise RuntimeError("test did not release the handler")
            return digest

        boundary = ActionBoundary(ws, handlers={"export_markdown": handler})
        barrier.wait(15)
        try:
            if operation == "approve":
                action = boundary.get(action_id)
                boundary.approve(action_id, OWNER, seen_sha256=action.payload_sha256,
                                 seen_destination=action.destination)
                results.put("approved")
            else:
                results.put(boundary.execute(action_id, OWNER))
        except ActionError:
            results.put("refused")
    finally:
        ws.close()


class ActionTransitionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "workspace"
        self.ws, _ = load_sample(self.root)
        self.addCleanup(self.ws.close)
        self.briefs = BriefService(self.ws)
        draft = self.briefs.draft_weekly_brief("2026-09-28", "2026-09-30")
        self.revision = self.briefs.accept(draft.id, OWNER, draft.body_sha256)
        self.boundary = ActionBoundary(self.ws)
        self.action = self.boundary.propose(
            "export_markdown", revision_id=self.revision.id, destination="brief.md",
            purpose="Save synthetic planning exercise", proposed_by=OWNER)
        self.ctx = multiprocessing.get_context("spawn")

    def approve(self):
        self.boundary.approve(self.action.id, OWNER, seen_sha256=self.action.payload_sha256,
                              seen_destination=self.action.destination)

    def start_requests(self, operation, count):
        barrier, results = self.ctx.Barrier(count), self.ctx.Queue()
        entered, release = self.ctx.Event(), self.ctx.Event()
        processes = [self.ctx.Process(target=competing_request, args=(
            str(self.root), self.action.id, operation, barrier, results, entered, release))
                     for _ in range(count)]

        def cleanup(keep_barrier=barrier):
            # Keep its shared semaphores alive until spawned children finish.
            release.set()
            for process in processes:
                process.join(5)
                if process.is_alive():
                    process.terminate()
                    process.join(5)
            results.close()

        self.addCleanup(cleanup)
        for process in processes:
            process.start()
        return processes, results, entered, release

    def join_requests(self, processes):
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)

    def assert_one_receipt(self, outcome):
        rows = self.ws.store.conn.execute(
            "SELECT outcome FROM receipts WHERE action_id = ?", (self.action.id,)).fetchall()
        self.assertEqual([row[0] for row in rows], [outcome])
        self.assertEqual(self.boundary.get(self.action.id).status, outcome)
        events = [row for row in self.ws.store.events()
                  if row["record_id"] == self.action.id and row["kind"] == outcome]
        self.assertEqual(len(events), 1)

    def test_competing_approvals_record_one_approval(self):
        processes, results, _entered, _release = self.start_requests("approve", 2)
        self.assertEqual(sorted(results.get(timeout=20) for _ in processes),
                         ["approved", "refused"])
        self.join_requests(processes)
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM approvals WHERE action_id = ?", (self.action.id,)).fetchone()[0], 1)
        events = [row for row in self.ws.store.events()
                  if row["record_id"] == self.action.id and row["kind"] == "approve"]
        self.assertEqual(len(events), 1)

    def test_competing_executions_invoke_handler_once(self):
        self.approve()
        processes, results, entered, release = self.start_requests("execute", 2)
        self.assertTrue(entered.wait(20))
        # Keep the winning handler open until the other process is refused.
        self.assertEqual(results.get(timeout=20), "refused")
        release.set()
        receipt = results.get(timeout=20)
        self.join_requests(processes)
        self.assertEqual(receipt["outcome"], "succeeded")
        self.assertEqual((self.root / "effect-count").read_text(), "effect\n")
        self.assert_one_receipt("succeeded")
        self.assertEqual(self.boundary.execute(self.action.id, OWNER), receipt)

    def test_recovery_and_live_finisher_share_one_receipt(self):
        self.approve()
        processes, results, entered, release = self.start_requests("execute", 1)
        self.assertTrue(entered.wait(20))
        settled = self.boundary.reconcile()
        self.assertEqual(len(settled), 1)
        release.set()
        self.assertEqual(results.get(timeout=20), settled[0])
        self.join_requests(processes)
        self.assert_one_receipt("succeeded")
        self.assertEqual(self.boundary.reconcile(), [])
        self.assertEqual((self.root / "effect-count").read_text(), "effect\n")

    def test_late_finisher_preserves_unknown_recovery_outcome(self):
        self.approve()
        self.ws.store.conn.execute("UPDATE actions SET status = 'executing' WHERE id = ?",
                                   (self.action.id,))
        settled = self.boundary.reconcile()[0]
        self.assertEqual(self.boundary._finish(self.action.id, OWNER, "succeeded", "late"), settled)
        self.assert_one_receipt("effect_unknown")

    def test_superseded_revision_cannot_be_approved(self):
        draft = self.briefs.revise(self.revision.artifact_id,
                                   self.revision.body_markdown + "\nNew planning note\n", OWNER)
        self.briefs.accept(draft.id, OWNER, draft.body_sha256)
        with self.assertRaises(StaleApproval):
            self.approve()
        self.assertEqual(self.boundary.get(self.action.id).status, "awaiting_approval")
        self.assertEqual(self.ws.store.conn.execute("SELECT count(*) FROM approvals").fetchone()[0], 0)

    def test_receipt_failure_rolls_back_terminal_state_and_audit(self):
        self.approve()
        self.ws.store.conn.execute("UPDATE actions SET status = 'executing' WHERE id = ?",
                                   (self.action.id,))
        self.ws.store.conn.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON receipts"
                                   " BEGIN SELECT RAISE(ABORT, 'synthetic receipt failure'); END")
        before = self.ws.store.events()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "receipt failure"):
            self.boundary._finish(self.action.id, OWNER, "succeeded", "synthetic")
        self.assertEqual(self.boundary.get(self.action.id).status, "executing")
        self.assertEqual(self.ws.store.events(), before)


if __name__ == "__main__":
    unittest.main()
