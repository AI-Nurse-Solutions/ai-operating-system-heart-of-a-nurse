# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0
"""Audit integrity, atomic writes, truthful legacy history, and recovery."""

import json
import multiprocessing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager import store as store_module
from nurse_manager.services import ManagerWorkspace
from nurse_manager.store import Store, StoreError


def append_events(path, barrier, results):
    store = Store(Path(path))
    try:
        barrier.wait(15)
        for _ in range(10):
            store.log("test-role", "synthetic", "task", "synthetic-id")
        results.put(store.verify_events()["ok"])
    finally:
        store.close()


class EventChainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.ws = ManagerWorkspace(self.root / "ws")
        self.addCleanup(self.ws.close)
        self.ws.create("Synthetic planning", "me")
        self.store = self.ws.store

    def checkpoint(self, backup):
        return json.loads(Path(str(backup) + ".audit.json").read_text())

    def remove_event_guards(self, conn):
        # A privileged offline attacker, not an ordinary application writer.
        guards = conn.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                              " AND tbl_name='event_log'").fetchall()
        for row in guards:
            conn.execute(f'DROP TRIGGER "{row[0]}"')
        return guards

    def test_sql_cannot_edit_delete_or_append_unchained_events(self):
        for sql in ("UPDATE event_log SET actor='changed'", "DELETE FROM event_log",
                    "INSERT INTO event_log (at,actor,kind,record_type,record_id)"
                    " VALUES ('then','role','synthetic','task','id')"):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.store.conn.execute(sql)

    def test_failed_audit_insert_rolls_back_record_and_chain_head(self):
        before = self.store.verify_events()
        self.store.conn.execute("CREATE TRIGGER fail_event BEFORE INSERT ON event_log"
                                " BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "audit failure"):
            self.ws.add_project("Synthetic project", "Planning exercise", "me")
        self.assertEqual(self.store.conn.execute("SELECT count(*) FROM projects").fetchone()[0], 0)
        self.assertEqual(self.store.verify_events(), before)

    def test_modified_deleted_and_reordered_chained_events_are_detected(self):
        self.store.log("test-role", "synthetic", "task", "one")
        self.store.log("test-role", "synthetic", "task", "two")
        for sql in ("UPDATE event_log SET kind='forged' WHERE seq=2",
                    "DELETE FROM event_log WHERE seq=2",
                    "UPDATE event_log SET seq=100 WHERE seq=2",
                    "DELETE FROM event_log WHERE seq=(SELECT max(seq) FROM event_log)"):
            backup = self.root / (str(abs(hash(sql))) + ".sqlite")
            self.store.backup(backup)
            damaged = sqlite3.connect(backup, isolation_level=None)
            damaged.row_factory = sqlite3.Row
            try:
                guards = self.remove_event_guards(damaged)
                damaged.execute(sql)
                for guard in guards:
                    damaged.execute(guard[1])
                self.assertFalse(store_module._audit_report(damaged)["ok"], sql)
            finally:
                damaged.close()

    def test_corrupt_history_refuses_a_new_write_without_changing_records(self):
        self.remove_event_guards(self.store.conn)
        self.store.conn.execute("UPDATE event_log SET actor='forged'")
        with self.assertRaises(StoreError):
            self.ws.add_project("Synthetic project", "Planning exercise", "me")
        self.assertEqual(self.store.conn.execute("SELECT count(*) FROM projects").fetchone()[0], 0)

    def test_backup_checkpoint_comes_from_the_copied_snapshot(self):
        backup = self.root / "copy.sqlite"
        before = self.store.verify_events()
        real_report = store_module._audit_report
        wrote = []

        def report_and_change_live(conn, checkpoint=None):
            if conn is not self.store.conn and not wrote:
                wrote.append(True)
                self.store.log("test-role", "late-write", "task", "synthetic-id")
            return real_report(conn, checkpoint)

        with mock.patch.object(store_module, "_audit_report", report_and_change_live):
            with self.assertRaisesRegex(StoreError, "retry when"):
                self.store.backup(backup)
        self.assertFalse(backup.exists())
        # A changed outside anchor refuses a stale copy, rather than falsely
        # binding it to the newer live head. A fresh retry names the copied head.
        self.store.backup(backup)
        checkpoint = self.checkpoint(backup)
        self.assertNotEqual(checkpoint["head_sha256"], before["head_sha256"])
        self.assertEqual(checkpoint["head_sha256"], self.store.verify_events()["head_sha256"])
        copied = sqlite3.connect(backup)
        copied.row_factory = sqlite3.Row
        try:
            self.assertTrue(real_report(copied, checkpoint)["ok"])
        finally:
            copied.close()

    def test_restore_refuses_damaged_chain_and_missing_or_wrong_checkpoint(self):
        for damage in ("chain", "missing", "checkpoint"):
            backup = self.root / (damage + ".sqlite")
            self.store.backup(backup)
            sidecar = Path(str(backup) + ".audit.json")
            if damage == "chain":
                conn = sqlite3.connect(backup, isolation_level=None)
                self.remove_event_guards(conn)
                conn.execute("UPDATE event_log SET actor='forged'")
                conn.close()
            elif damage == "missing":
                sidecar.unlink()
            else:
                checkpoint = self.checkpoint(backup)
                checkpoint["head_sha256"] = "f" * 64
                sidecar.write_text(json.dumps(checkpoint))
            before = self.store.verify_events()
            with self.assertRaises(StoreError):
                self.store.restore(backup, allow_discarding_newer=True)
            self.assertEqual(self.store.verify_events(), before)
            self.assertEqual(list((self.store.path.parent / "backups").glob("pre-restore-*")), [])

    def test_off_device_checkpoint_detects_rewritten_history_and_local_head(self):
        checkpoint = self.store.verify_events()
        guards = self.remove_event_guards(self.store.conn)
        row = dict(self.store.conn.execute("SELECT * FROM event_log WHERE seq=1").fetchone())
        row["actor"] = "forged-role"
        digest = store_module._event_digest(row)
        self.store.conn.execute("UPDATE event_log SET actor=?,event_sha256=? WHERE seq=1",
                                (row["actor"], digest))
        self.store.conn.execute("UPDATE audit_chain_state SET head_sha256=?", (digest,))
        for guard in guards:
            self.store.conn.execute(guard[1])
        self.assertTrue(store_module._audit_report(self.store.conn)["ok"])
        self.assertFalse(self.store.verify_events()["ok"])
        self.assertFalse(self.store.verify_events(checkpoint)["ok"])

    def test_database_only_rollback_and_missing_outside_anchor_are_detected(self):
        backup = self.root / "older.sqlite"
        self.store.backup(backup)
        self.store.log("test-role", "new-event", "task", "id")
        old = sqlite3.connect(backup)
        try:
            old.backup(self.store.conn)
        finally:
            old.close()
        self.assertTrue(store_module._audit_report(self.store.conn)["ok"])
        self.assertFalse(self.store.verify_events()["ok"])
        with self.assertRaises(StoreError):
            self.store.log("test-role", "would-hide-rollback", "task", "id")
        store_module._head_path(self.store.path).unlink()
        report = self.store.verify_events()
        self.assertFalse(report["ok"])
        self.assertEqual(report["anchor_status"], "missing")

    def test_legacy_database_rollback_cannot_reinitialize_the_newer_anchor(self):
        path = self.root / "old-live.sqlite"
        steps = [(v, sql) for v, sql in store_module._migrations() if v < "0016"]
        with mock.patch.object(store_module, "_migrations", return_value=steps):
            old = Store(path)
            old.log("test-role", "legacy", "task", "id")
            backup = self.root / "old-before-chain.sqlite"
            old.backup(backup)
            old.close()
        upgraded = Store(path)
        upgraded.log("test-role", "new-chained", "task", "id")
        upgraded.close()
        anchor_before = store_module._head_path(path).read_bytes()
        path.write_bytes(backup.read_bytes())
        with self.assertRaisesRegex(StoreError, "legacy database disagrees"):
            Store(path)
        self.assertEqual(store_module._head_path(path).read_bytes(), anchor_before)

    def test_backup_cannot_bless_a_concurrently_interrupted_anchor_commit(self):
        backup = self.root / "racy-backup.sqlite"
        other = Store(self.store.path)
        self.addCleanup(other.close)
        real_verify, real_write = self.store.verify_events, store_module._write_head
        wrote = []

        def verify_then_interrupted_commit(checkpoint=None):
            report = real_verify(checkpoint)
            if not wrote:
                wrote.append(True)
                calls = []
                def fail_finalize(path, committed, pending=None):
                    calls.append(True)
                    if len(calls) == 2:
                        raise OSError("synthetic interruption")
                    real_write(path, committed, pending)
                with mock.patch.object(store_module, "_write_head", fail_finalize):
                    with self.assertRaises(OSError):
                        other.log("test-role", "unconfirmed-anchor", "task", "id")
            return report

        with mock.patch.object(self.store, "verify_events", verify_then_interrupted_commit):
            with self.assertRaisesRegex(StoreError, "interrupted commit"):
                self.store.backup(backup)
        self.assertFalse(backup.exists())
        self.assertFalse(Path(str(backup) + ".audit.json").exists())

    def test_anchor_prepare_failure_rolls_back_writer_and_commit_failure_restores_anchor(self):
        before = self.store.verify_events()
        with mock.patch.object(store_module, "_write_head", side_effect=OSError("synthetic anchor failure")):
            with self.assertRaises(OSError):
                self.ws.add_project("Synthetic project", "Planning exercise", "me")
        self.assertEqual(self.store.verify_events(), before)
        self.assertEqual(self.store.conn.execute("SELECT count(*) FROM projects").fetchone()[0], 0)
        real_write = store_module._write_head

        def write_then_abort_commit(path, committed, pending=None):
            real_write(path, committed, pending)
            if pending is not None:
                self.store.conn.set_authorizer(lambda action, name, *_:
                                              sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_TRANSACTION
                                              and name == "COMMIT" else sqlite3.SQLITE_OK)

        try:
            with mock.patch.object(store_module, "_write_head", write_then_abort_commit):
                with self.assertRaises(sqlite3.DatabaseError):
                    self.store.log("test-role", "synthetic", "task", "id")
        finally:
            self.store.conn.set_authorizer(None)
        self.assertEqual(self.store.verify_events(), before)

    def test_interrupted_anchor_finalize_is_reported_and_never_automatically_blessed(self):
        real_write = store_module._write_head
        calls = []

        def fail_finalize(path, committed, pending=None):
            calls.append(pending)
            if len(calls) == 2:
                raise OSError("synthetic finalization failure")
            real_write(path, committed, pending)

        with mock.patch.object(store_module, "_write_head", fail_finalize):
            with self.assertRaises(OSError):
                self.store.log("test-role", "committed-but-unacknowledged", "task", "id")
        report = self.store.verify_events()
        self.assertFalse(report["ok"])
        self.assertIn("interrupted commit", report["error"])
        with self.assertRaises(StoreError):
            self.store.log("test-role", "unsafe-retry", "task", "id")

    def test_restore_checks_and_copy_use_the_same_source_snapshot(self):
        backup = self.root / "source-snapshot.sqlite"
        self.store.backup(backup)
        # WAL allows a source writer to commit while restore holds its read
        # snapshot. The copied database must still be the validated version.
        writer = sqlite3.connect(backup, isolation_level=None)
        self.addCleanup(writer.close)
        writer.execute("PRAGMA journal_mode=WAL")
        real_read = Path.read_text
        wrote = []

        def read_checkpoint_then_change_source(path, *args, **kwargs):
            text = real_read(path, *args, **kwargs)
            if path == Path(str(backup) + ".audit.json") and not wrote:
                wrote.append(True)
                writer.execute("INSERT INTO schema_migrations VALUES ('9999_unknown','synthetic')")
            return text

        with mock.patch.object(Path, "read_text", read_checkpoint_then_change_source):
            self.store.restore(backup)
        self.assertTrue(wrote)
        self.assertIsNone(self.store.conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version='9999_unknown'").fetchone())
        self.assertTrue(self.store.verify_events()["ok"])

    def test_null_and_non_object_checkpoints_cannot_disable_comparison(self):
        for content in ("null", "[]", "true", '"checkpoint"', '{}'):
            backup = self.root / (str(abs(hash(content))) + ".sqlite")
            self.store.backup(backup)
            Path(str(backup) + ".audit.json").write_text(content)
            with self.assertRaisesRegex(StoreError, "malformed"):
                self.store.restore(backup, allow_discarding_newer=True)

    def test_missing_guards_and_malformed_state_fail_closed(self):
        backup = self.root / "missing-guard.sqlite"
        self.store.backup(backup)
        conn = sqlite3.connect(backup, isolation_level=None)
        conn.execute("DROP TRIGGER event_log_advance_head")
        conn.close()
        with self.assertRaisesRegex(StoreError, "guards"):
            self.store.restore(backup)
        self.store.conn.execute("PRAGMA ignore_check_constraints=ON")
        self.store.conn.execute("UPDATE audit_chain_state SET legacy_through=-1,head_seq=-1")
        self.assertFalse(self.store.verify_events()["ok"])
        with self.assertRaises(StoreError):
            self.store.log("test-role", "synthetic", "task", "id")

    def test_fabricated_hash_is_refused_at_insertion(self):
        head = self.store.verify_events()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "hash does not match"):
            self.store.conn.execute("INSERT INTO event_log (seq,at,actor,kind,record_type,record_id,"
                                    "previous_sha256,event_sha256) VALUES (2,'then','role','event',"
                                    "'task','id',?,?)", (head["head_sha256"], "f" * 64))
        self.assertEqual(self.store.verify_events(), head)

    def test_restore_serializes_writers_through_safety_copy_and_replacement(self):
        backup = self.root / "restore.sqlite"
        self.store.backup(backup)
        other = Store(self.store.path)
        self.addCleanup(other.close)
        other.conn.execute("PRAGMA busy_timeout=10")
        real_backup = self.store.backup
        tried = []

        def backup_then_concurrent_writer(dest):
            result = real_backup(dest)
            tried.append(True)
            with self.assertRaises(sqlite3.OperationalError):
                other.log("test-role", "concurrent", "task", "id")
            return result

        with mock.patch.object(self.store, "backup", backup_then_concurrent_writer):
            self.store.restore(backup)
        self.assertTrue(tried)
        # Restore released the exclusive lock; subsequent writes are retained.
        other.log("test-role", "after-restore", "task", "id")
        self.assertEqual(self.store.verify_events()["chained_count"], 2)

    def test_failed_checkpoint_write_removes_only_the_owned_partial_backup(self):
        backup = self.root / "failed.sqlite"
        with mock.patch.object(store_module.json, "dump", side_effect=OSError("synthetic full disk")):
            with self.assertRaises(OSError):
                self.store.backup(backup)
        self.assertFalse(backup.exists())
        self.assertFalse(Path(str(backup) + ".audit.json").exists())
        sidecar = Path(str(backup) + ".audit.json")
        sidecar.write_text("existing unrelated checkpoint")
        with self.assertRaises(StoreError):
            self.store.backup(backup)
        self.assertEqual(sidecar.read_text(), "existing unrelated checkpoint")

    def test_backup_inside_record_transaction_refuses_instead_of_hanging(self):
        with self.store.transaction():
            with self.assertRaisesRegex(StoreError, "record transaction"):
                self.store.backup(self.root / "pending.sqlite")

    def test_migration_keeps_old_events_unchained_and_old_backups_restore(self):
        old_path = self.root / "legacy.sqlite"
        steps = [(v, sql) for v, sql in store_module._migrations() if v < "0016"]
        with mock.patch.object(store_module, "_migrations", return_value=steps):
            old = Store(old_path)
            old.log("test-role", "legacy", "task", "old-id")
            old_events = [tuple(row) for row in old.events()]
            legacy_backup = self.root / "legacy-copy.sqlite"
            old.backup(legacy_backup)
            old.close()
        upgraded = Store(old_path)
        try:
            rows = upgraded.events()
            self.assertEqual([tuple(row)[:6] for row in rows], old_events)
            self.assertIsNone(rows[0]["event_sha256"])
            upgraded.log("test-role", "new", "task", "new-id")
            report = upgraded.verify_events()
            self.assertTrue(report["ok"])
            self.assertEqual((report["legacy_count"], report["chained_count"]), (1, 1))
            upgraded.restore(legacy_backup, allow_discarding_newer=True)
            self.assertEqual(upgraded.verify_events()["legacy_count"], 1)
            self.assertEqual(upgraded.verify_events()["chained_count"], 0)
        finally:
            upgraded.close()

    def test_two_processes_append_one_serial_chain(self):
        ctx = multiprocessing.get_context("spawn")
        barrier, results = ctx.Barrier(2), ctx.Queue()
        processes = [ctx.Process(target=append_events,
                                 args=(str(self.store.path), barrier, results)) for _ in range(2)]
        try:
            for process in processes:
                process.start()
            self.assertEqual([results.get(timeout=25) for _ in processes], [True, True])
            for process in processes:
                process.join(10)
                self.assertEqual(process.exitcode, 0)
            report = self.store.verify_events()
            self.assertTrue(report["ok"])
            self.assertEqual(report["chained_count"], 21)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                process.join(5)
            results.close()


if __name__ == "__main__":
    unittest.main()
