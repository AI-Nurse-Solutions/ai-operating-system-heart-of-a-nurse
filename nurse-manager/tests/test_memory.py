"""Scoped memory (5.2): inspect, correct, exclude, delete, on the governed contract."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401
from _bootstrap import fixed_clock

from nurse_manager._naio import MemoryInterface, MemoryRecord
from nurse_manager.assistant import compose_project_context
from nurse_manager.memory import MemoryRefused, WorkspaceMemory
from nurse_manager.sample import load_sample
from nurse_manager.services import CaptureRefused, ManagerError
from nurse_manager.views import memory, mission_control

TODAY = "2026-09-30"
OWNER = "Sample Manager"


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws, _ = load_sample(Path(self._tmp.name) / "ws", clock=fixed_clock())
        self.addCleanup(self.ws.close)
        self.mem = WorkspaceMemory(self.ws)
        projects = mission_control(self.ws, today=TODAY, week_of="2026-09-28")[
            "projects_in_motion"]["items"]
        self.huddle = next(p["id"] for p in projects if p["title"].startswith("Huddle"))
        self.council = next(p["id"] for p in projects if p["title"].startswith("Unit Based"))

    def item(self, memory_id):
        return next(i for i in memory(self.ws, today=TODAY)["items"] if i["id"] == memory_id)


class ContractTests(_Case):
    def test_it_is_the_governed_memory_contract_and_keeps_its_consent_rules(self):
        self.assertIsInstance(self.mem, MemoryInterface)
        record = MemoryRecord(memory_id="mem-000000000001", tenant=self.ws.info.id,
                              role_scope="any", content="Keep it short.",
                              provenance="Written by Sample Manager", created_at="x")
        for consent in ("ask_before_remembering", "do_not_remember", "sure"):
            with self.subTest(consent=consent), self.assertRaises(MemoryRefused):
                self.mem.remember(record, consent)
        from dataclasses import replace
        with self.assertRaises(MemoryRefused):
            self.mem.remember(replace(record, provenance=" "), "remember")
        with self.assertRaises(MemoryRefused):
            self.mem.remember(replace(record, tenant="ws-000000000000"), "remember")
        stored = self.mem.remember(record, "remember")
        self.assertEqual((stored.content, stored.quarantined), ("Keep it short.", False))
        self.assertEqual(self.mem.recall("ws-000000000000", "any", ""), ())
        self.assertIn("Keep it short.", [r.content for r in self.mem.recall(
            self.ws.info.id, "any", "short")])


class InspectTests(_Case):
    def test_in_use_then_expired_then_excluded_with_who_wrote_it(self):
        expiring = self.mem.add("Council agendas two days ahead (synthetic).",
                                project_id=self.council, expires_on=TODAY)
        self.ws.store.conn.execute("UPDATE memories SET expires_on = '2026-09-01' WHERE id = ?",
                                   (expiring,))
        view = memory(self.ws, today=TODAY)
        self.assertEqual((view["in_use"], view["expired"], view["excluded"]), (2, 1, 1))
        self.assertEqual([(i["status"], i["expired"]) for i in view["items"]],
                         [("active", False), ("active", False), ("active", True),
                          ("excluded", False)])
        first = view["items"][0]
        self.assertIsNone(first["project_id"])  # all work comes before one project
        self.assertEqual(view["items"][1]["project_title"], "Huddle format pilot")
        self.assertRegex(first["provenance"], r"^Written by Sample Manager on \d{4}-\d{2}-\d{2}$")


class CaptureRuleTests(_Case):
    def test_identifiers_are_refused_not_stored_redacted(self):
        before = memory(self.ws, today=TODAY)["items"]
        for text in ("Email jane.doe@example.org first", "Call 555-867-5309"):
            with self.subTest(text=text), self.assertRaises(CaptureRefused):
                self.mem.add(text)
        self.assertEqual(memory(self.ws, today=TODAY)["items"], before)

    def test_text_scope_and_expiry_are_checked(self):
        for kwargs in ({"content": " "}, {"content": "x" * 501},
                       {"content": "ok", "project_id": "prj-000000000000"},
                       {"content": "ok", "expires_on": "soon"},
                       {"content": "ok", "expires_on": "2020-01-01"}):
            content = kwargs.pop("content")
            with self.subTest(content=content[:10], **kwargs), self.assertRaises(ManagerError):
                self.mem.add(content, **kwargs)
        with self.assertRaises(sqlite3.IntegrityError):
            self.ws.store.conn.execute(
                "INSERT INTO memories (id, workspace_id, content, provenance, created_at,"
                " updated_at) VALUES ('mem-000000000009', ?, ' ', 'p', 'x', 'x')",
                (self.ws.info.id,))


class CorrectExcludeDeleteTests(_Case):
    def setUp(self):
        super().setUp()
        self.mid = self.mem.add("Council agendas go out two days ahead (synthetic).")

    def test_correcting_changes_the_text_and_says_who_corrected_it(self):
        self.mem.correct_text(self.mid, "Council agendas go out three days ahead (synthetic).")
        item = self.item(self.mid)
        self.assertEqual(item["content"], "Council agendas go out three days ahead (synthetic).")
        self.assertRegex(item["provenance"], r"^Corrected by Sample Manager on ")
        with self.assertRaises(CaptureRefused):
            self.mem.correct_text(self.mid, "Ask jane.doe@example.org")

    def test_exclude_keeps_it_but_it_is_never_sent_and_can_be_used_again(self):
        self.mem.exclude(self.mid)
        self.assertEqual(self.item(self.mid)["status"], "excluded")
        text, refs = compose_project_context(self.ws, self.huddle, TODAY)
        self.assertNotIn(self.mid, refs)
        self.assertNotIn("two days ahead", text)
        with self.assertRaises(MemoryRefused):
            self.mem.exclude(self.mid)
        self.mem.include(self.mid)
        self.assertIn(self.mid, compose_project_context(self.ws, self.huddle, TODAY)[1])
        with self.assertRaises(MemoryRefused):
            self.mem.include(self.mid)

    def test_a_status_change_is_decided_inside_the_write(self):
        stale = dict(self.ws._require_row("memories", self.mid))
        self.mem.exclude(self.mid)
        with mock.patch.object(self.ws, "_require_row", return_value=stale), \
                self.assertRaises(MemoryRefused):
            self.mem.exclude(self.mid)

    def test_deleting_is_final_and_leaves_no_text_behind(self):
        text = "Council agendas go out two days ahead (synthetic)."
        self.mem.delete(self.mid)
        self.assertNotIn(self.mid, [i["id"] for i in memory(self.ws, today=TODAY)["items"]])
        db = self.ws.store.conn
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            for row in db.execute(f"SELECT * FROM {table}"):  # noqa: S608
                self.assertNotIn(text, " ".join(str(v) for v in tuple(row)), table)
        events = [(e["kind"], e["record_id"]) for e in self.ws.store.events()
                  if e["record_type"] == "memory" and e["record_id"] == self.mid]
        self.assertEqual(events, [("create", self.mid), ("delete", self.mid)])
        with self.assertRaises(MemoryRefused):
            self.mem.delete(self.mid)
        with self.assertRaises(MemoryRefused):
            self.mem.correct_text(self.mid, "Back again.")

    def test_deleted_and_corrected_text_is_not_left_in_the_file(self):
        # Set explicitly: some SQLite builds default it on, others off.
        self.assertEqual(self.ws.store.conn.execute("PRAGMA secure_delete").fetchone()[0], 1)
        self.mem.correct_text(self.mid, "Replaced wording (synthetic).")
        other = self.mem.add("Zebra-striped reminder for the file test (synthetic).")
        self.mem.delete(other)
        path = self.ws.store.path
        self.ws.close()
        data = path.read_bytes()
        self.assertNotIn(b"two days ahead", data)
        self.assertNotIn(b"Zebra-striped reminder", data)
        self.assertIn(b"Replaced wording", data)


class WhatIsSentTests(_Case):
    def test_only_memories_in_use_for_all_work_or_this_project_are_sent(self):
        for_council = self.mem.add("Council prefers written options (synthetic).",
                                   project_id=self.council)
        expired = self.mem.add("Old note (synthetic).", expires_on=TODAY)
        self.ws.store.conn.execute("UPDATE memories SET expires_on = '2026-09-01' WHERE id = ?",
                                   (expired,))
        text, refs = compose_project_context(self.ws, self.huddle, TODAY)
        sent = {i["id"]: i for i in memory(self.ws, today=TODAY)["items"] if i["id"] in refs}
        self.assertEqual(sorted(i["content"] for i in sent.values()), [
            "Huddles stay at five minutes; do not suggest longer formats (synthetic).",
            "Lead with the decisions I need to make, then blockers (synthetic).",
        ])
        self.assertNotIn(for_council, refs)
        self.assertNotIn(expired, refs)
        self.assertNotIn("budget talks", text)  # the sample's excluded memory
        self.assertIn("## What the manager asked you to remember", text)
        self.assertIn(for_council, compose_project_context(self.ws, self.council, TODAY)[1])


if __name__ == "__main__":
    unittest.main()
