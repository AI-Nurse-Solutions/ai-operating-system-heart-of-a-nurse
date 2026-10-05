# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0
"""People labels reduce naming without claiming identity or safe free text."""
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from nurse_manager.services import CaptureRefused, ManagerWorkspace
from nurse_manager import cli, people
from nurse_manager.control import AssistantControl
from nurse_manager.views import mission_control


class PeopleFieldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ws = ManagerWorkspace(Path(self.temp.name) / "workspace")
        self.addCleanup(self.ws.close)
        self.ws.create("Synthetic planning", "me")
        self.project = self.ws.add_project("Practice project", "Public exercise", "me")

    def test_new_people_fields_refuse_uncontrolled_labels_without_events(self):
        attempts = [
            lambda: self.ws.add_project("Practice", "Public exercise", "Synthetic Person"),
            lambda: self.ws.add_task("Practice", "Synthetic Person"),
            lambda: self.ws.add_task("Practice", "me", reviewer="Synthetic Person"),
            lambda: self.ws.record_decision("Practice?", "Review", "Synthetic Person", "2026-10-04"),
            lambda: self.ws.add_feedback(self.project, "Synthetic Person", "worked", "Public exercise", "2020-01-01"),
            lambda: self.ws.add_contribution("Practice", "teaching", "2020-01-01", "Wrote outline", "Synthetic Person"),
        ]
        events = [dict(row) for row in self.ws.store.events()]
        for attempt in attempts:
            with self.subTest(attempt=attempt), self.assertRaises(CaptureRefused):
                attempt()
            self.assertEqual([dict(row) for row in self.ws.store.events()], events)
            self.assertTrue(self.ws.store.verify_events()["ok"])

    def test_new_workspace_refuses_a_name(self):
        ws = ManagerWorkspace(Path(self.temp.name) / "other")
        self.addCleanup(ws.close)
        with self.assertRaises(CaptureRefused):
            ws.create("Synthetic planning", "Synthetic Person")
        self.assertIsNone(ws._workspace_row())

    def test_names_inside_free_text_are_not_claimed_detected(self):
        task = self.ws.add_task("Practice with Synthetic Person", "me")
        self.assertIn("Synthetic Person", self.ws._require_row("tasks", task)["title"])

    def test_valid_roles_and_bounded_shared_credit_are_canonical(self):
        task = self.ws.add_task("Practice", " educator ", reviewer="review team")
        row = self.ws._require_row("tasks", task)
        self.assertEqual((row["owner"], row["reviewer"]), ("Educator", "Review team"))
        self.assertEqual(people.shared_labels(" council ; EDUCATOR "), "Council; Educator")
        for value in people.LABELS:
            self.assertEqual(people.label(value), value)
        self.assertEqual(people.label("", optional=True), "")
        self.assertEqual(people.status(self.ws.store.conn, self.ws.info.id)["unrecognized_fields"], 0)

    def test_invalid_types_markup_and_malformed_lists_make_no_changes(self):
        anchor = (self.ws.store.path.with_name("workspace.sqlite.audit-head.json")).read_bytes()
        before = [dict(row) for row in self.ws.store.events()]
        for value in (None, True, 1, [], {}, "", "<script>me</script>", "me; Educator", "me\nEducator"):
            with self.subTest(value=value), self.assertRaises(CaptureRefused):
                self.ws.add_task("Practice", value)
        for value in (None, [], "", "Educator;", ";Educator", "Educator;;Council",
                      "Educator; educator", "Educator; Synthetic Person", ";".join(people.LABELS[:7])):
            with self.subTest(shared=value), self.assertRaises(CaptureRefused):
                self.ws.add_contribution("Practice", "teaching", "2020-01-01", "Wrote outline", value)
        self.assertEqual([dict(row) for row in self.ws.store.events()], before)
        self.assertEqual((self.ws.store.path.with_name("workspace.sqlite.audit-head.json")).read_bytes(), anchor)
        self.assertEqual(self.ws.store.conn.execute("SELECT count(*) FROM tasks").fetchone()[0], 0)
        self.assertEqual(self.ws.store.conn.execute("SELECT count(*) FROM contributions").fetchone()[0], 0)

    def test_existing_labels_owner_binding_and_backups_remain_unchanged(self):
        task = self.ws.add_task("Practice", "me")
        # Synthetic earlier/unrecognized labels: the status check makes no
        # claim about their age or provenance. Direct SQL is outside writers.
        with self.ws.store.transaction() as db:
            db.execute("UPDATE workspaces SET owner = 'Synthetic legacy owner'")
            db.execute("UPDATE projects SET owner = 'Synthetic legacy project owner'")
            db.execute("UPDATE tasks SET owner = 'Synthetic legacy task owner', reviewer = 'Synthetic legacy reviewer'")
        before = dict(self.ws._require_row("tasks", task))
        events = [dict(row) for row in self.ws.store.events()]
        anchor = self.ws.store.path.with_name("workspace.sqlite.audit-head.json").read_bytes()
        root = self.ws.root
        self.ws.close()
        self.ws = ManagerWorkspace(root)
        self.addCleanup(self.ws.close)
        report = mission_control(self.ws, today="2026-10-04", week_of="2026-09-28")["people_fields"]
        self.assertEqual(report, {"policy": "personal-people@1", "unrecognized_fields": 4})
        self.assertEqual(dict(self.ws._require_row("tasks", task)), before)
        self.assertEqual([dict(row) for row in self.ws.store.events()], events)
        self.assertEqual(self.ws.store.path.with_name("workspace.sqlite.audit-head.json").read_bytes(), anchor)
        backup = self.ws.store.backup(Path(self.temp.name) / "backup.sqlite")
        self.ws.store.restore(backup)
        self.assertEqual(dict(self.ws._require_row("tasks", task)), before)
        self.assertEqual(self.ws.info.owner, "Synthetic legacy owner")
        with self.assertRaises(ValueError):
            AssistantControl(self.ws).stop("me")
        AssistantControl(self.ws).stop("Synthetic legacy owner")
        with self.assertRaises(CaptureRefused):
            self.ws.add_task("Practice", "Synthetic legacy owner")
        self.ws.add_task("Practice", "me")
        self.assertTrue(self.ws.store.verify_events()["ok"])

    def test_cli_default_and_refusal_share_the_backend(self):
        code, result = cli.run(["init", str(Path(self.temp.name) / "cli"), "--name", "Synthetic planning"])
        self.assertEqual(code, 0)
        self.assertEqual(result["data"]["owner"], "me")
        code, result = cli.run(["task-add", str(self.ws.root), "--title", "Practice", "--owner", "Synthetic Person"])
        self.assertNotEqual(code, 0)
        self.assertEqual(result["error"]["type"], "CaptureRefused")

    def test_generated_browser_rules_are_current(self):
        manager = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(manager / "tools/gen_people_rules.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Names are not automatically detected.", people.DATA_RULE)
