"""Pilot feedback and crash recovery (build step 6.3).

Pilot feedback is kept on this computer, screened like every other capture,
and leaves only as text the manager has reviewed and saved themselves. The
``reconcile`` command settles an export a crash interrupted, by checking the
file on disk and never by running it again.
"""

import hashlib
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401
from _bootstrap import fixed_clock

from nurse_manager import __version__, cli
from nurse_manager import store as store_module
from nurse_manager.pilot import AREAS, KINDS, MAX_PILOT_TEXT, PilotFeedback, pilot_item
from nurse_manager.sample import load_sample
from nurse_manager.services import CaptureRefused, ManagerError, ManagerWorkspace
from nurse_manager.store import MIGRATIONS_DIR, Store

OWNER = "Sample Manager"


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ws, _ = load_sample(self.tmp / "ws", clock=fixed_clock())
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self.ws.close)
        self.pilot = PilotFeedback(self.ws)

    def count(self) -> int:
        return self.ws.store.conn.execute("SELECT count(*) FROM pilot_feedback").fetchone()[0]

    def exports(self) -> list[tuple]:
        return [tuple(r) for r in self.ws.store.conn.execute(
            "SELECT items, sha256, exported_by FROM pilot_feedback_exports")]


class CaptureTests(_Case):
    def test_feedback_is_kept_here_with_its_area_and_kind(self):
        fid = self.pilot.add("weekly_brief", "problem",
                             "  The Accept button was hard to find on a small screen.  ")
        item = pilot_item(self.ws, fid)
        self.assertRegex(fid, r"^plf-[0-9a-f]{12}$")
        self.assertEqual((item["area"], item["kind"], item["summary"], item["exported_at"]),
                         ("weekly_brief", "problem",
                          "The Accept button was hard to find on a small screen.", None))
        events = [(e["actor"], e["kind"], e["record_id"]) for e in self.ws.store.events()
                  if e["record_type"] == "pilot_feedback"]
        self.assertEqual(events, [(OWNER, "create", fid)])

    def test_identifiers_are_refused_and_nothing_is_stored(self):
        for text, entity, matched in (
                ("Call the pilot desk at 555-010-4477", "PHONE_NUMBER", "555-010-4477"),
                ("Write to pilot@example.org", "EMAIL_ADDRESS", "pilot@example.org"),
                ("The patient in room 12 bed B saw it", "ROOM_BED", "room 12"),
                ("MRN 00123456 showed up in a draft", "MRN", "00123456")):
            with self.subTest(entity=entity):
                with self.assertRaises(CaptureRefused) as refused:
                    self.pilot.add("other", "problem", text)
                self.assertIn(entity, str(refused.exception))
                # Findings name the kind of identifier, never the matched text.
                self.assertNotIn(matched, str(refused.exception))
        self.assertEqual(self.count(), 0)

    def test_every_refusal_says_why_and_stores_nothing(self):
        for args, message in ((("reports", "problem", "Text"), "unknown part of the app"),
                              (("other", "complaint", "Text"), "unknown feedback kind"),
                              (("other", "idea", "   "), "your feedback is required"),
                              (("other", "idea", "x" * (MAX_PILOT_TEXT + 1)),
                               f"under {MAX_PILOT_TEXT} characters")):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ManagerError, message):
                    self.pilot.add(*args)
        self.assertEqual(self.count(), 0)

    def test_the_database_refuses_what_the_service_refuses(self):
        for area, kind, summary in (("reports", "idea", "x"), ("other", "complaint", "x"),
                                    ("other", "idea", "  ")):
            with self.subTest(area=area, kind=kind), self.assertRaises(sqlite3.IntegrityError):
                self.ws.store.conn.execute(
                    "INSERT INTO pilot_feedback (id, workspace_id, area, kind, summary,"
                    " created_at) VALUES ('plf-000000000001', ?, ?, ?, ?, 'now')",
                    (self.ws.info.id, area, kind, summary))

    def test_the_view_lists_newest_first_with_the_choices_the_screen_offers(self):
        first = self.pilot.add("getting_started", "worked", "The sample made sense quickly.")
        second = self.pilot.add("packs", "idea", "A pack for orientation checklists.")
        view = self.pilot.view()
        self.assertEqual([i["id"] for i in view["items"]], [second, first])
        self.assertEqual((view["sample"], view["not_yet_exported"], view["last_export"]),
                         (True, 2, None))
        self.assertEqual([a["value"] for a in view["areas"]], list(AREAS))
        self.assertEqual([k["value"] for k in view["kinds"]], list(KINDS))


class DeleteTests(_Case):
    def test_delete_removes_the_text_from_the_workspace_and_the_file(self):
        keep = self.pilot.add("other", "idea", "Keep this synthetic idea.")
        gone = self.pilot.add("other", "problem", "Quokka-shaped synthetic problem to delete.")
        self.pilot.delete(gone)
        self.assertEqual([i["id"] for i in self.pilot.items()], [keep])
        self.assertNotIn("Quokka", self.pilot.preview()["text"])
        events = [(e["kind"], e["record_id"]) for e in self.ws.store.events()
                  if e["record_type"] == "pilot_feedback"]
        self.assertEqual(events[-1], ("delete", gone))
        path = self.ws.store.path
        self.ws.close()
        self.assertNotIn(b"Quokka-shaped", path.read_bytes())

    def test_deleting_what_is_not_here_is_refused(self):
        fid = self.pilot.add("other", "idea", "Delete me (synthetic).")
        self.pilot.delete(fid)
        for missing in (fid, "plf-000000000000"):
            with self.subTest(id=missing), self.assertRaisesRegex(ManagerError, "not in this workspace"):
                self.pilot.delete(missing)


class PreviewTests(_Case):
    def test_the_preview_is_exactly_the_text_that_would_be_shared(self):
        self.pilot.add("weekly_brief", "problem", "The Accept button was hard to find.")
        self.pilot.add("ai_assistance", "question", "Can the preview be printed?")
        preview = self.pilot.preview()
        today = self.ws.local_today()
        self.assertEqual(preview["sha256"], hashlib.sha256(preview["text"].encode()).hexdigest())
        self.assertEqual((preview["items"], preview["can_export"], preview["reason"],
                          preview["findings"], preview["filename"]),
                         (2, True, "", [], f"nurse-ai-os-pilot-feedback-{today}.md"))
        self.assertTrue(preview["text"].startswith(
            "# Nurse AI OS pilot feedback\n\n"
            f"- App version: {__version__}\n"
            "- Workspace: the synthetic sample\n"
            f"- Prepared on: {today}\n"
            "- Items: 2\n"))
        # Dated by this computer's calendar, like everything else the manager sees.
        day = datetime.fromisoformat("2026-09-30T09:00:00+00:00").astimezone().date().isoformat()
        self.assertTrue(preview["text"].endswith(
            f"## 1. Weekly brief: Problem ({day})\n\nThe Accept button was hard to find.\n\n"
            f"## 2. AI assistance: Question ({day})\n\nCan the preview be printed?\n"))
        # Asking twice gives the same text: nothing about it is random.
        self.assertEqual(self.pilot.preview(), preview)

    def test_only_feedback_crosses_never_names_ids_or_records(self):
        fid = self.pilot.add("projects", "worked", "Dashboards are clear.")
        text = self.pilot.preview()["text"]
        info = self.ws.info
        for private in (info.name, info.owner, info.id, fid, "prj-", "tsk-", "Huddle"):
            with self.subTest(private=private):
                self.assertNotIn(private, text)

    def test_the_export_says_what_the_screen_cannot_do(self):
        text = self.pilot.preview()["text"]
        self.assertIn("does not detect people's names", text)
        self.assertIn("Nothing was sent automatically", text)
        self.assertNotRegex(text.lower(), r"phi[- ]free|de-identified|hipaa[- ]compliant")

    def test_an_empty_preview_says_so_and_cannot_be_exported(self):
        preview = self.pilot.preview()
        self.assertEqual((preview["items"], preview["can_export"]), (0, False))
        self.assertEqual(preview["reason"], "There is no pilot feedback to export yet.")

    def test_the_whole_export_is_screened_again_before_it_can_be_made(self):
        # Text that reached the table some other way (an older release, a
        # recognizer added since) is caught when the export is built.
        self.pilot.add("other", "idea", "Fine synthetic idea.")
        self.ws.store.conn.execute(
            "INSERT INTO pilot_feedback (id, workspace_id, area, kind, summary, created_at)"
            " VALUES ('plf-00000000beef', ?, 'other', 'question',"
            " 'Ask the desk at 555-010-4477', '2026-09-30T10:00:00+00:00')",
            (self.ws.info.id,))
        preview = self.pilot.preview()
        self.assertFalse(preview["can_export"])
        self.assertEqual(preview["findings"], ["PHONE_NUMBER"])
        self.assertIn("item 2 (PHONE_NUMBER)", preview["reason"])
        self.assertNotIn("555-010-4477", preview["reason"])
        with self.assertRaises(CaptureRefused):
            self.pilot.export(preview["sha256"], OWNER)
        self.assertEqual(self.exports(), [])
        self.pilot.delete("plf-00000000beef")
        self.assertTrue(self.pilot.preview()["can_export"])

    def test_the_screen_runs_over_the_text_as_a_whole_too(self):
        class SeesTheHeader:
            def analyze(self, text):
                from naio_integrations.contract import PrivacyFinding
                return (PrivacyFinding("CREDENTIAL", 0, 1, 1.0, "test"),) if "# Nurse" in text else ()

        self.pilot.add("other", "idea", "Fine synthetic idea.")
        self.ws.privacy = SeesTheHeader()
        preview = self.pilot.preview()
        self.assertEqual((preview["can_export"], preview["findings"]), (False, ["CREDENTIAL"]))
        self.assertIn("the export text", preview["reason"])


class ExportTests(_Case):
    def test_the_export_is_the_reviewed_text_and_keeps_only_its_hash(self):
        fid = self.pilot.add("mission_control", "worked", "Mission Control answers my Monday.")
        preview = self.pilot.preview()
        made = self.pilot.export(preview["sha256"], OWNER)
        self.assertEqual({k: made[k] for k in preview}, preview)
        self.assertRegex(made["id"], r"^plx-[0-9a-f]{12}$")
        self.assertEqual(self.exports(), [(1, preview["sha256"], OWNER)])
        columns = {r[1] for r in self.ws.store.conn.execute(
            "PRAGMA table_info(pilot_feedback_exports)")}
        self.assertNotIn("text", columns)
        view = self.pilot.view()
        self.assertEqual(view["last_export"], {"items": 1, "exported_at": made["exported_at"]})
        self.assertEqual((view["not_yet_exported"], pilot_item(self.ws, fid)["exported_at"]),
                         (0, made["exported_at"]))
        events = [(e["kind"], e["record_id"]) for e in self.ws.store.events()
                  if e["record_type"] == "pilot_feedback"]
        self.assertEqual(events[-1], ("export", made["id"]))

    def test_a_change_after_the_preview_refuses_and_exports_nothing(self):
        self.pilot.add("other", "idea", "First synthetic idea.")
        preview = self.pilot.preview()
        self.pilot.add("other", "idea", "Added after the preview.")
        with self.assertRaisesRegex(ManagerError, "changed since you reviewed it"):
            self.pilot.export(preview["sha256"], OWNER)
        with self.assertRaisesRegex(ManagerError, "changed since you reviewed it"):
            self.pilot.export("0" * 64, OWNER)
        self.assertEqual(self.exports(), [])
        self.assertEqual(self.pilot.view()["not_yet_exported"], 2)

    def test_only_the_manager_exports_and_there_must_be_something_to_export(self):
        with self.assertRaisesRegex(ManagerError, "no pilot feedback to export"):
            self.pilot.export(self.pilot.preview()["sha256"], OWNER)
        self.pilot.add("other", "idea", "Synthetic idea.")
        preview = self.pilot.preview()
        for by in ("Someone Else", "", " "):
            with self.subTest(by=by), self.assertRaisesRegex(ManagerError, "accountable manager"):
                self.pilot.export(preview["sha256"], by)
        self.assertEqual(self.exports(), [])

    def test_an_export_that_was_not_saved_is_never_lost(self):
        # Every export holds every item, so exporting again gives the file back.
        self.pilot.add("other", "idea", "Synthetic idea.")
        first = self.pilot.export(self.pilot.preview()["sha256"], OWNER)
        again = self.pilot.export(self.pilot.preview()["sha256"], OWNER)
        self.assertEqual((again["text"], again["items"]), (first["text"], 1))
        self.assertEqual(len(self.exports()), 2)

    def test_the_own_workspace_is_named_as_such_never_by_its_name(self):
        own = ManagerWorkspace(self.tmp / "own", clock=fixed_clock())
        self.addCleanup(own.close)
        own.create("Unit planning", "Test Manager")
        pilot = PilotFeedback(own)
        pilot.add("getting_started", "worked", "Creating my workspace was quick.")
        text = pilot.export(pilot.preview()["sha256"], "Test Manager")["text"]
        self.assertIn("- Workspace: the manager’s own\n", text)
        self.assertNotIn("Unit planning", text)
        self.assertNotIn("Test Manager", text)


class CliTests(_Case):
    def test_the_command_surface_refuses_as_the_service_does(self):
        ws = str(self.tmp / "ws")
        self.ws.close()
        code, added = cli.run(["pilot-feedback-add", ws, "--area", "packs", "--kind", "idea",
                               "--summary=--looks like an option (synthetic)"])
        self.assertEqual(code, 0, added)
        self.assertEqual(added["data"]["item"]["summary"], "--looks like an option (synthetic)")
        code, refused = cli.run(["pilot-feedback-add", ws, "--area", "reports", "--kind",
                                 "idea", "--summary", "x"])
        self.assertEqual((code, refused["error"]["type"]), (2, "UsageError"))
        _, shown = cli.run(["pilot-feedback-preview", ws])
        code, stale = cli.run(["pilot-feedback-export", ws, "--reviewed-sha", "0" * 64,
                               "--by", OWNER])
        self.assertEqual((code, stale["ok"]), (2, False))
        code, made = cli.run(["pilot-feedback-export", ws, "--reviewed-sha",
                              shown["data"]["sha256"], "--by", OWNER])
        self.assertEqual((code, made["data"]["text"]), (0, shown["data"]["text"]))


class MigrationTests(unittest.TestCase):
    def test_upgrading_a_workspace_keeps_its_records_and_adds_pilot_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            old_dir = tmp / "migrations-0012"
            old_dir.mkdir()
            for path in MIGRATIONS_DIR.glob("*.sql"):
                if path.stem < "0013":
                    shutil.copy(path, old_dir / path.name)
            with mock.patch.object(store_module, "MIGRATIONS_DIR", old_dir):
                old, _ = load_sample(tmp / "ws", clock=fixed_clock())
                before = old.store.conn.execute("SELECT count(*) FROM tasks").fetchone()[0]
                self.assertEqual(old.store.schema_version, "0012_action_policy_version")
                old.close()
            new = ManagerWorkspace(tmp / "ws", clock=fixed_clock())
            try:
                # Upgrades run to the latest migration, through 0013 on the way.
                self.assertEqual(new.store.schema_version,
                                 max(f.stem for f in MIGRATIONS_DIR.glob("*.sql")))
                self.assertIsNotNone(new.store.conn.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = '0013_pilot_feedback'"
                ).fetchone())
                self.assertEqual(new.store.conn.execute("SELECT count(*) FROM tasks").fetchone()[0],
                                 before)
                PilotFeedback(new).add("other", "worked", "Upgraded cleanly (synthetic).")
            finally:
                new.close()
            # An older release refuses the upgraded workspace rather than lose it.
            with mock.patch.object(store_module, "MIGRATIONS_DIR", old_dir):
                with self.assertRaisesRegex(store_module.StoreError, "newer schema"):
                    Store(tmp / "ws" / "workspace.sqlite")


class ReconcileTests(unittest.TestCase):
    """After a crash: an interrupted export is settled by checking the disk, never re-run."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws = str(Path(self._tmp.name) / "ws")
        cli.run(["sample", self.ws])
        draft = cli.run(["brief", self.ws, "--week", "2026-09-28", "--today", "2026-09-30"])[1]
        cli.run(["accept", self.ws, "--revision", draft["data"]["id"], "--reviewer", OWNER,
                 "--sha", draft["data"]["sha256"]])
        action = cli.run(["export", self.ws, "--revision", draft["data"]["id"], "--file",
                          "week.md", "--by", OWNER])[1]["data"]
        cli.run(["approve", self.ws, "--action", action["id"], "--approver", OWNER, "--sha",
                 action["payload_sha256"], "--destination", "week.md"])
        self.action = action["id"]
        self.exports = Path(self.ws) / "exports"

    def interrupt(self):
        with sqlite3.connect(Path(self.ws) / "workspace.sqlite") as db:
            db.execute("UPDATE actions SET status = 'executing' WHERE id = ?", (self.action,))

    def test_nothing_interrupted_means_nothing_settled(self):
        self.assertEqual(cli.run(["reconcile", self.ws]), (0, {
            "contract": cli.CONTRACT, "command": "reconcile", "ok": True,
            "data": {"settled": []}}))

    def test_an_interrupted_export_with_no_file_is_unknown_and_not_run_again(self):
        self.interrupt()
        code, envelope = cli.run(["reconcile", self.ws])
        self.assertEqual(code, 0)
        [receipt] = envelope["data"]["settled"]
        self.assertEqual((receipt["action_id"], receipt["outcome"]), (self.action, "effect_unknown"))
        self.assertFalse(self.exports.exists(), "reconcile never writes the file")
        self.assertEqual(cli.run(["reconcile", self.ws])[1]["data"]["settled"], [])
        code, refused = cli.run(["run", self.ws, "--action", self.action, "--actor", OWNER])
        self.assertEqual((code, refused["ok"]), (2, False))

    def test_an_interrupted_export_whose_file_matches_is_confirmed(self):
        cli.run(["run", self.ws, "--action", self.action, "--actor", OWNER])
        written = (self.exports / "week.md").read_bytes()
        self.interrupt()
        [receipt] = cli.run(["reconcile", self.ws])[1]["data"]["settled"]
        self.assertEqual(receipt["outcome"], "succeeded")
        self.assertIn(hashlib.sha256(written).hexdigest(), receipt["detail"])
        self.assertEqual((self.exports / "week.md").read_bytes(), written)


if __name__ == "__main__":
    unittest.main()
