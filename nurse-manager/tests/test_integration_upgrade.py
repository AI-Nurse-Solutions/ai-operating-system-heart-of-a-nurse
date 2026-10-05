# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0
"""Completed local features must coexist with upstream and audit history."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager import store as store_module
from nurse_manager.store import Store


class IntegratedUpgradeTests(unittest.TestCase):
    def upgrade_from(self, *, audit):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "workspace.sqlite"
            migrations = store_module._migrations()
            prior = [(name, sql) for name, sql in migrations
                     if name != "0014_task_transitions"
                     and (audit or name != "0016_event_chain")]
            with mock.patch.object(store_module, "_migrations", return_value=prior):
                old = Store(path)
                with old.transaction() as db:
                    db.execute("INSERT INTO workspaces VALUES"
                               " ('ws-synthetic', 'Synthetic workspace', 'personal_manager',"
                               " 'Synthetic role', 0, '2026-10-04')")
                    db.execute("INSERT INTO tasks"
                               " (id,workspace_id,title,owner,status,completion_evidence,created_at,updated_at)"
                               " VALUES ('tsk-synthetic','ws-synthetic','Retained task','Synthetic role',"
                               " 'completed','Synthetic review evidence','2026-10-04','2026-10-04')")
                    old.log("synthetic-role", "create", "task", "tsk-synthetic")
                before = dict(old.conn.execute("SELECT * FROM tasks").fetchone())
                events = [dict(row) for row in old.events()]
                anchor = (store_module._head_path(path).read_bytes() if audit else None)
                old.close()
            new = Store(path)
            try:
                versions = {row[0] for row in new.conn.execute("SELECT version FROM schema_migrations")}
                self.assertIn("0014_classifier", versions)
                self.assertIn("0014_task_transitions", versions)
                self.assertIn("0016_event_chain", versions)
                task = dict(new.conn.execute("SELECT * FROM tasks").fetchone())
                self.assertEqual({key: task[key] for key in before}, before)
                self.assertEqual(task["withdrawal_reason"], "")
                self.assertEqual(new.conn.execute("SELECT count(*) FROM task_transitions").fetchone()[0], 0)
                after_events = [dict(row) for row in new.events()]
                self.assertEqual([{key: row[key] for key in events[0]} for row in after_events], events)
                self.assertEqual(new.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
                report = new.verify_events()
                self.assertTrue(report["ok"], report)
                if audit:
                    self.assertEqual(store_module._head_path(path).read_bytes(), anchor)
                else:
                    self.assertIsNone(after_events[0]["event_sha256"])
                new.log("synthetic-role", "review", "task", "tsk-synthetic")
                self.assertTrue(new.verify_events()["ok"])
                self.assertTrue(list(path.parent.glob("backups/pre-migration-*.sqlite")))
            finally:
                new.close()

    def test_upgrade_from_upstream_classifier_preserves_records(self):
        self.upgrade_from(audit=False)

    def test_upgrade_from_completed_audit_step_preserves_chain_and_anchor(self):
        self.upgrade_from(audit=True)

    def original_task_schema(self, *, restore):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "original.sqlite"
            prior = [(name, sql) for name, sql in store_module._migrations()
                     if name < "0014" or name == "0014_task_transitions"]
            with mock.patch.object(store_module, "_migrations", return_value=prior):
                old = Store(path)
                with old.transaction() as db:
                    db.execute("INSERT INTO workspaces VALUES"
                               " ('ws-synthetic','Synthetic original','personal_manager',"
                               " 'Synthetic role',0,'2026-10-04')")
                    db.execute("INSERT INTO tasks"
                               " (id,workspace_id,title,owner,status,withdrawal_reason,created_at,updated_at)"
                               " VALUES ('tsk-synthetic','ws-synthetic','Retained withdrawn task',"
                               " 'Synthetic role','withdrawn','Exercise ended','2026-10-04','2026-10-04')")
                    db.execute("INSERT INTO task_transitions"
                               " (id,workspace_id,task_id,kind,from_status,to_status,reason,"
                               " previous_evidence,created_by,created_at)"
                               " VALUES ('trn-synthetic','ws-synthetic','tsk-synthetic','withdraw',"
                               " 'ready','withdrawn','Exercise ended','Retained earlier evidence',"
                               " 'Synthetic role','2026-10-04')")
                    old.log("synthetic-role", "withdraw", "task", "tsk-synthetic")
                before = {table: [dict(row) for row in old.conn.execute(f"SELECT * FROM {table}")]
                          for table in ("workspaces", "tasks", "task_transitions", "event_log")}
                backup = old.backup(root / "original-backup.sqlite")
                old.close()
            new = Store(root / "target.sqlite" if restore else path)
            try:
                if restore:
                    safety = new.restore(backup, allow_discarding_newer=True)
                    self.assertTrue(safety.is_file())
                for table, rows in before.items():
                    actual = [dict(row) for row in new.conn.execute(f"SELECT * FROM {table}")]
                    self.assertEqual([{key: row[key] for key in rows[0]} for row in actual], rows)
                versions = {row[0] for row in new.conn.execute("SELECT version FROM schema_migrations")}
                self.assertTrue({"0014_classifier", "0014_task_transitions", "0016_event_chain"} <= versions)
                self.assertEqual(new.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertTrue(new.verify_events()["ok"])
                self.assertIsNone(new.events()[0]["event_sha256"])
                new.log("synthetic-role", "review", "task", "tsk-synthetic")
                self.assertTrue(new.verify_events()["ok"])
            finally:
                new.close()

    def test_original_task_database_upgrades_without_losing_withdrawal_history(self):
        self.original_task_schema(restore=False)

    def test_original_task_backup_restores_without_losing_withdrawal_history(self):
        self.original_task_schema(restore=True)
