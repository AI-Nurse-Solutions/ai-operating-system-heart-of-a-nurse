# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0

"""Task transitions preserve evidence and decide against locked current state."""

import multiprocessing
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager import store as store_module
from nurse_manager.brief import compose_weekly_brief
from nurse_manager.services import CaptureRefused, ManagerError, ManagerWorkspace
from nurse_manager.views import board, mission_control, project_dashboard


def racing_move(root, task_id, target, barrier, results):
    ws = ManagerWorkspace(Path(root))
    try:
        barrier.wait(10)
        try:
            ws.move_task(task_id, target, expected_status="ready")
            results.put("moved")
        except ManagerError:
            results.put("stale")
    finally:
        ws.close()


class TaskTransitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "workspace"
        self.ws = ManagerWorkspace(self.root)
        self.addCleanup(self.ws.close)
        self.ws.create("Synthetic work", "me")
        self.project = self.ws.add_project("Synthetic project", "Practice planning", "me")
        self.task = self.ws.add_task("Synthetic task", "me", project_id=self.project,
                                     status="ready", due_date="2026-10-01")

    def row(self):
        return dict(self.ws._require_row("tasks", self.task))

    def history(self):
        return [dict(row) for row in self.ws.store.conn.execute(
            "SELECT * FROM task_transitions WHERE task_id = ? ORDER BY rowid", (self.task,))]

    def test_completed_task_requires_reasoned_reopen_and_keeps_previous_evidence(self):
        self.ws.complete_task(self.task, "Outline reviewed", expected_status="ready")
        before = self.row()
        for change in (lambda: self.ws.move_task(self.task, "ready"),
                       lambda: self.ws.complete_task(self.task, "Replacement evidence"),
                       lambda: self.ws.set_blocked(self.task, True, "Awaiting review"),
                       lambda: self.ws.set_paused(self.task, True),
                       lambda: self.ws.withdraw_task(self.task, "No longer needed"),
                       lambda: self.ws.reopen_task(self.task, " ")):
            with self.assertRaises(ManagerError):
                change()
        self.assertEqual(self.row(), before)
        self.ws.reopen_task(self.task, "A new review is required", expected_status="completed")
        self.assertEqual((self.row()["status"], self.row()["completion_evidence"]), ("ready", ""))
        self.ws.complete_task(self.task, "Second outline reviewed")
        history = self.history()
        self.assertEqual([row["kind"] for row in history], ["complete", "reopen", "complete"])
        self.assertEqual(history[1]["previous_evidence"], "Outline reviewed")
        self.assertEqual(history[1]["reason"], "A new review is required")
        self.assertEqual(history[2]["completion_evidence"], "Second outline reviewed")
        for sql in ("UPDATE task_transitions SET previous_evidence = ''", "DELETE FROM task_transitions"):
            with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                self.ws.store.conn.execute(sql)

    def test_withdrawal_is_reasoned_terminal_and_excluded_from_open_work(self):
        with self.assertRaises(ManagerError):
            self.ws.withdraw_task(self.task, "")
        with self.assertRaises(CaptureRefused):
            self.ws.withdraw_task(self.task, "Call 555-867-5309")
        self.ws.withdraw_task(self.task, "The planning exercise ended")
        self.assertEqual(self.row()["withdrawal_reason"], "The planning exercise ended")
        view = project_dashboard(self.ws, self.project, today="2026-10-04")
        self.assertEqual((view["readiness"]["open_tasks"], view["readiness"]["completed_tasks"]), (0, 0))
        home = mission_control(self.ws, today="2026-10-04", week_of="2026-09-28")
        self.assertEqual(home["task_counts"]["withdrawn"], 1)
        self.assertEqual(home["follow_ups"]["items"], [])
        withdrawn = next(column for column in board(self.ws)["columns"] if column["status"] == "withdrawn")
        self.assertEqual(withdrawn["cards"][0]["id"], self.task)
        body, _refs = compose_weekly_brief(self.ws, "2026-09-28", "2026-10-04")
        self.assertNotIn("Synthetic task", body)
        with self.assertRaises(ManagerError):
            self.ws.move_task(self.task, "ready")
        self.ws.reopen_task(self.task, "Resume the exercise", expected_status="withdrawn")
        self.assertEqual(self.row()["withdrawal_reason"], "")

    def test_stale_noop_and_foreign_tasks_make_no_history_or_events(self):
        foreign_id = "tsk-" + "f" * 12
        self.ws.store.conn.execute(
            "INSERT INTO workspaces SELECT 'ws-ffffffffffff', name, profile, owner, sample, created_at"
            " FROM workspaces WHERE id = ?", (self.ws.info.id,))
        self.ws.store.conn.execute(
            "INSERT INTO tasks (id, workspace_id, title, owner, status, created_at, updated_at)"
            " VALUES (?, 'ws-ffffffffffff', 'Synthetic foreign task', 'Other role', 'ready', ?, ?)",
            (foreign_id, self.ws.clock(), self.ws.clock()))
        before = self.ws.store.events()
        for change in (lambda: self.ws.move_task(self.task, "ready"),
                       lambda: self.ws.move_task(self.task, "in_progress", expected_status="idea"),
                       lambda: self.ws.move_task(foreign_id, "in_progress"),
                       lambda: self.ws.reopen_task(self.task, "Not terminal")):
            with self.assertRaises(ManagerError):
                change()
        self.assertEqual(self.history(), [])
        self.assertEqual(self.ws.store.events(), before)
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT status FROM tasks WHERE id = ?", (foreign_id,)).fetchone()[0], "ready")

    def test_failed_history_insert_rolls_back_task_and_audit(self):
        self.ws.store.conn.execute("CREATE TRIGGER fail_history BEFORE INSERT ON task_transitions"
                                   " BEGIN SELECT RAISE(ABORT, 'synthetic history failure'); END")
        before, events = self.row(), self.ws.store.events()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "history failure"):
            self.ws.move_task(self.task, "in_progress")
        self.assertEqual(self.row(), before)
        self.assertEqual(self.ws.store.events(), events)

    def test_two_processes_cannot_both_move_the_same_reviewed_state(self):
        ctx = multiprocessing.get_context("spawn")
        barrier, results = ctx.Barrier(2), ctx.Queue()
        processes = [ctx.Process(target=racing_move, args=(str(self.root), self.task, status, barrier, results))
                     for status in ("in_progress", "needs_judgment")]
        try:
            for process in processes:
                process.start()
            outcomes = sorted(results.get(timeout=20) for _ in processes)
            for process in processes:
                process.join(10)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(outcomes, ["moved", "stale"])
            self.assertEqual(len(self.history()), 1)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                process.join()
            results.close()
            results.join_thread()


class TaskMigrationTests(unittest.TestCase):
    def test_upgrade_preserves_every_task_and_event_without_inventing_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, old_dir = Path(tmp) / "workspace", Path(tmp) / "migrations"
            old_dir.mkdir()
            for path in store_module.MIGRATIONS_DIR.glob("*.sql"):
                if path.stem < "0014":
                    shutil.copyfile(path, old_dir / path.name)
            with mock.patch.object(store_module, "MIGRATIONS_DIR", old_dir):
                old = ManagerWorkspace(root)
                old.create("Synthetic legacy work", "me")
                old.add_task("Retained active task", "me", status="ready")
                done = old.add_task("Retained completed task", "me")
                # Seed the previous release's completed state directly: the
                # current transition writer intentionally requires migration 0014.
                old.store.conn.execute("UPDATE tasks SET status = 'completed', completion_evidence = ?"
                                       " WHERE id = ?", ("Legacy outline reviewed", done))
                old.store.conn.execute("UPDATE workspaces SET owner = 'Synthetic legacy manager'")
                old.store.conn.execute("UPDATE tasks SET owner = 'Synthetic legacy task role',"
                                       " reviewer = 'Synthetic legacy reviewer'")
                tasks = [dict(row) for row in old.store.conn.execute("SELECT * FROM tasks ORDER BY id")]
                events = old.store.events()
                old.close()
            new = ManagerWorkspace(root)
            try:
                upgraded = [dict(row) for row in new.store.conn.execute("SELECT * FROM tasks ORDER BY id")]
                self.assertEqual([{key: row[key] for key in tasks[0]} for row in upgraded], tasks)
                self.assertEqual(new.info.owner, "Synthetic legacy manager")
                self.assertTrue(all(row["withdrawal_reason"] == "" for row in upgraded))
                upgraded_events = [dict(row) for row in new.store.events()]
                self.assertEqual(
                    [{key: row[key] for key in events[0].keys()} for row in upgraded_events],
                    [dict(row) for row in events])
                self.assertTrue(all(row["event_sha256"] is None for row in upgraded_events))
                self.assertTrue(new.store.verify_events()["ok"])
                self.assertEqual(new.store.conn.execute("SELECT count(*) FROM task_transitions").fetchone()[0], 0)
                self.assertEqual(new.store.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                new.close()

    def test_migration_splitter_keeps_trigger_body_and_quoted_semicolons(self):
        statements = store_module._split_sql(
            "CREATE TABLE example (value TEXT);"
            "CREATE TRIGGER refuse BEFORE INSERT ON example BEGIN "
            "SELECT RAISE(ABORT, 'a; b'); END;")
        self.assertEqual(len(statements), 2)
        connection = sqlite3.connect(":memory:")
        try:
            for statement in statements:
                connection.execute(statement)
            with self.assertRaisesRegex(sqlite3.IntegrityError, "a; b"):
                connection.execute("INSERT INTO example VALUES ('x')")
        finally:
            connection.close()
