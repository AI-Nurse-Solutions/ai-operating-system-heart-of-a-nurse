"""Records, capture rules, views, and restore (G2/G3 exit evidence)."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import _bootstrap
from _bootstrap import fixed_clock

from nurse_manager.sample import SAMPLE_PATH, load_sample
from nurse_manager.services import CaptureRefused, ManagerError, ManagerWorkspace
from nurse_manager.store import MIGRATIONS_DIR, RestoreRefused, Store, StoreError
from nurse_manager.views import board, library, mission_control, project_dashboard, table

WEEK = "2026-09-28"
TODAY = "2026-09-30"


class _TempCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def sample(self, name="ws"):
        ws, _ = load_sample(self.tmp / name, clock=fixed_clock())
        self.addCleanup(ws.close)
        return ws

    def empty(self, name="empty", owner="Test Manager"):
        ws = ManagerWorkspace(self.tmp / name, clock=fixed_clock())
        self.addCleanup(ws.close)
        ws.create("Empty workspace", owner)
        return ws


class StoreTests(_TempCase):
    def test_migrations_apply_once_and_reopen_cleanly(self):
        store = Store(self.tmp / "a.sqlite")
        version = store.schema_version
        store.close()
        reopened = Store(self.tmp / "a.sqlite")
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.schema_version, version)
        count = reopened.conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]
        self.assertEqual(count, len(list(MIGRATIONS_DIR.glob("*.sql"))))

    def test_database_from_a_newer_release_is_refused(self):
        store = Store(self.tmp / "a.sqlite")
        store.conn.execute(
            "INSERT INTO schema_migrations VALUES ('9999_future', '2030-01-01')"
        )
        store.close()
        with self.assertRaises(StoreError):
            Store(self.tmp / "a.sqlite")

    def test_restore_refuses_to_discard_newer_work(self):
        ws = self.sample()
        backup = ws.store.backup(self.tmp / "backups" / "b1.sqlite")
        task_id = ws.add_task("Created after the backup", "Sample Manager")
        with self.assertRaises(RestoreRefused) as caught:
            ws.store.restore(backup)
        self.assertEqual(caught.exception.newer_events, 1)
        # Nothing changed: the newer task is still there.
        self.assertTrue(any(r["id"] == task_id for r in table(ws)["rows"]))

    def test_explicit_restore_keeps_a_recoverable_pre_restore_copy(self):
        ws = self.sample()
        backup = ws.store.backup(self.tmp / "backups" / "b1.sqlite")
        task_id = ws.add_task("Created after the backup", "Sample Manager")
        safety = ws.store.restore(backup, allow_discarding_newer=True)
        self.assertFalse(any(r["id"] == task_id for r in table(ws)["rows"]))
        kept = sqlite3.connect(str(safety))
        self.addCleanup(kept.close)
        self.assertEqual(
            kept.execute("SELECT count(*) FROM tasks WHERE id = ?", (task_id,)).fetchone()[0], 1
        )

    def test_a_backup_from_an_earlier_release_is_brought_up_to_date_on_restore(self):
        ws = self.sample()
        backup = ws.store.backup(self.tmp / "backups" / "b1.sqlite")
        old = sqlite3.connect(str(backup))
        old.executescript(
            "DROP TABLE project_feedback; DROP TABLE project_notes;"
            " DROP TABLE assistant_requests;"
            " DROP TABLE assistant_settings;"
            " DELETE FROM schema_migrations WHERE version != '0001_initial';"
        )
        old.close()
        ws.store.restore(backup)
        tables = {r[0] for r in ws.store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertIn("assistant_settings", tables)
        self.assertEqual(ws.store.schema_version, max(f.stem for f in MIGRATIONS_DIR.glob("*.sql")))

    def test_upgrading_keeps_every_ai_request_already_recorded(self):
        # Open a workspace with the schema as it was at 0002, record a request...
        import shutil as _shutil
        from unittest import mock

        from nurse_manager import store as store_module
        old_dir = self.tmp / "migrations-0002"
        old_dir.mkdir()
        for name in ("0001_initial.sql", "0002_assistant.sql"):
            _shutil.copy(MIGRATIONS_DIR / name, old_dir / name)
        with mock.patch.object(store_module, "MIGRATIONS_DIR", old_dir):
            old = Store(self.tmp / "u.sqlite")
            old.conn.execute("INSERT INTO workspaces VALUES ('ws-000000000001', 'W', 'personal_manager',"
                             " 'M', 0, '2026-09-28T00:00:00+00:00')")
            old.conn.execute(
                "INSERT INTO assistant_requests (id, workspace_id, task, provider, outcome,"
                " requested_by, created_at, cost_cents) VALUES ('air-000000000001',"
                " 'ws-000000000001', 'weekly_brief', 'local', 'provider_failed', 'M',"
                " '2026-09-28T00:00:00+00:00', NULL)")
            self.assertEqual(old.schema_version, "0002_assistant")
            old.close()
        # ...then open it with this release: the row survives the table rebuild.
        new = Store(self.tmp / "u.sqlite")
        self.addCleanup(new.close)
        rows = [tuple(r) for r in new.conn.execute(
            "SELECT id, task, outcome, cost_cents FROM assistant_requests")]
        self.assertEqual(rows, [("air-000000000001", "weekly_brief", "provider_failed", None)])
        new.conn.execute(
            "INSERT INTO assistant_requests (id, workspace_id, task, provider, outcome,"
            " requested_by, created_at) VALUES ('air-000000000002', 'ws-000000000001',"
            " 'project_question', 'local', 'answered', 'M', '2026-09-28T00:00:00+00:00')")
        self.assertEqual(new.conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_restore_of_an_identical_backup_needs_no_permission(self):
        ws = self.sample()
        backup = ws.store.backup(self.tmp / "backups" / "b1.sqlite")
        ws.store.restore(backup)

    def test_corrupt_backup_is_refused_without_touching_live_data(self):
        ws = self.sample()
        bad = self.tmp / "bad.sqlite"
        bad.write_bytes(b"not a database" * 100)
        with self.assertRaises(Exception):
            ws.store.restore(bad)
        self.assertEqual(len(table(ws)["rows"]), 8)


class CaptureRuleTests(_TempCase):
    def test_sample_week_loads_and_is_marked_synthetic(self):
        ws = self.sample()
        self.assertTrue(ws.info.sample)
        self.assertEqual(ws.info.profile, "personal_manager")
        data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(data["synthetic"])

    def test_identifiers_are_refused_not_stored(self):
        ws = self.empty()
        for text in (
            "Call back at 555-201-7788",
            "Email chair@example.org about the charter",
            "Follow up MRN: A123456",
        ):
            with self.subTest(text=text), self.assertRaises(CaptureRefused):
                ws.add_task(text, "Test Manager")
        self.assertEqual(table(ws)["rows"], [])

    def test_restricted_material_is_outside_the_personal_profile(self):
        ws = self.empty()
        with self.assertRaises(CaptureRefused):
            ws.add_source("Unit budget", "personal_permitted", "local://budget.xlsx",
                          data_class="D2")
        with self.assertRaises(CaptureRefused):
            ws.add_source("Staff evaluations", "employer_confidential", "local://evals")

    def test_dragging_a_card_cannot_complete_it(self):
        ws = self.empty()
        task_id = ws.add_task("Draft agenda", "Test Manager", status="ready")
        with self.assertRaises(ManagerError):
            ws.move_task(task_id, "completed")
        with self.assertRaises(ManagerError):
            ws.complete_task(task_id, "   ")
        ws.complete_task(task_id, "Agenda saved in the committee folder")
        self.assertEqual(table(ws)["rows"][0]["status"], "completed")

    def test_the_database_itself_refuses_completion_without_evidence(self):
        ws = self.empty()
        task_id = ws.add_task("Draft agenda", "Test Manager")
        with self.assertRaises(sqlite3.IntegrityError):
            ws.store.conn.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))

    def test_no_more_than_three_priorities(self):
        ws = self.empty()
        with self.assertRaises(ManagerError):
            ws.set_priorities(WEEK, ["a", "b", "c", "d"])

    def test_records_from_another_workspace_cannot_be_linked(self):
        other = self.sample("other")
        foreign_project = other.store.conn.execute("SELECT id FROM projects").fetchone()[0]
        ws = self.empty()
        with self.assertRaises(ManagerError):
            ws.add_task("Borrowed", "Test Manager", project_id=foreign_project)


class ViewTests(_TempCase):
    def test_same_ids_and_counts_across_views(self):
        ws = self.sample()
        b = board(ws)
        t = table(ws)
        mc = mission_control(ws, today=TODAY, week_of=WEEK)
        board_ids = sorted(card["id"] for col in b["columns"] for card in col["cards"])
        table_ids = sorted(row["id"] for row in t["rows"])
        self.assertEqual(board_ids, table_ids)
        for col in b["columns"]:
            self.assertEqual(col["count"], mc["task_counts"][col["status"]])
            self.assertEqual(
                col["count"], sum(1 for r in t["rows"] if r["status"] == col["status"])
            )
        project_total = sum(
            p["open_tasks"] + p["completed_tasks"] for p in mc["projects_in_motion"]["items"]
        )
        linked = sum(1 for r in t["rows"] if r["project"])
        self.assertEqual(project_total, linked)

    def test_mission_control_answers_what_needs_attention(self):
        ws = self.sample()
        mc = mission_control(ws, today=TODAY, week_of=WEEK)
        self.assertTrue(mc["sample"])
        self.assertEqual(len(mc["priorities"]["items"]), 3)
        self.assertEqual(
            [i["title"] for i in mc["needs_my_judgment"]["items"]],
            ["Decide council meeting cadence"],
        )
        overdue = [f for f in mc["follow_ups"]["items"] if f["overdue"]]
        self.assertEqual([f["title"] for f in overdue], ["Confirm vendor webinar dates"])
        self.assertEqual(mc["assistants_at_work"]["state"], "unavailable")

    def test_empty_workspace_states_are_honest(self):
        ws = self.empty()
        mc = mission_control(ws, today=TODAY, week_of=WEEK)
        for key in ("priorities", "needs_my_judgment", "projects_in_motion", "follow_ups",
                    "recent_accepted_outputs"):
            with self.subTest(section=key):
                self.assertEqual(mc[key]["state"], "empty")
                self.assertTrue(mc[key]["empty_message"])
        self.assertIn("without one", mc["assistants_at_work"]["empty_message"])

    def test_blocked_and_paused_are_explicit_not_hidden(self):
        ws = self.empty()
        task_id = ws.add_task("Book room", "Test Manager", status="ready", due_date="2026-10-01")
        ws.set_blocked(task_id, True, "Waiting for a decision")
        ws.set_paused(task_id, True)
        card = board(ws)["columns"][1]["cards"][0]
        self.assertTrue(card["blocked"])
        self.assertTrue(card["paused"])
        self.assertEqual(board(ws, show_paused=False)["columns"][1]["count"], 0)
        mc = mission_control(ws, today=TODAY, week_of=WEEK)
        self.assertEqual(mc["follow_ups"]["state"], "empty")


class LibraryTests(_TempCase):
    """The Library (3.6a): every source, whichever project it belongs to."""

    def test_every_source_overdue_reviews_first(self):
        ws = self.sample()
        lib = library(ws, today=TODAY)
        titles = [i["title"] for i in lib["items"]]
        self.assertEqual(len(titles), 3)
        self.assertEqual(titles[0], "Council charter template (synthetic)")
        self.assertTrue(lib["items"][0]["review_overdue"])
        self.assertEqual(lib["review_overdue"], 1)
        unattached = next(i for i in lib["items"] if i["project_id"] is None)
        self.assertEqual(unattached["project"], None)
        self.assertEqual(titles[1:], sorted(titles[1:], key=str.lower))
        self.assertEqual({p["title"] for p in lib["projects"]},
                         {r["title"] for r in ws.store.conn.execute("SELECT title FROM projects")})

    def test_the_same_source_ids_as_the_project_dashboards(self):
        ws = self.sample()
        on_dashboards = set()
        for (pid,) in ws.store.conn.execute("SELECT id FROM projects"):
            on_dashboards |= {r["id"] for r in project_dashboard(ws, pid, today=TODAY)["resources"]}
        in_library = {i["id"] for i in library(ws, today=TODAY)["items"] if i["project_id"]}
        self.assertEqual(in_library, on_dashboards)

    def test_adding_a_source_keeps_the_capture_rules(self):
        ws = self.sample()
        with self.assertRaises(CaptureRefused):
            ws.add_source("Grid", "internal", "x://y")
        with self.assertRaises(CaptureRefused):
            ws.add_source("Grid", "public", "x://y", data_class="D2")
        with self.assertRaises(CaptureRefused):
            ws.add_source("Call 555-867-5309", "public", "x://y")
        for kwargs in ({"review_date": "someday"}, {"project_id": "prj-000000000000"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ManagerError):
                ws.add_source("Guide", "public", "https://example.org/guide", **kwargs)
        with self.assertRaises(ManagerError):
            ws.add_source("x" * 201, "public", "https://example.org/guide")
        sid = ws.add_source("Guide", "public", "https://example.org/guide", review_date="2027-01-05")
        self.assertIn(sid, [i["id"] for i in library(ws, today=TODAY)["items"]])

    @unittest.skipUnless(hasattr(__import__("time"), "tzset"), "needs a settable time zone")
    def test_an_added_source_reads_the_same_as_the_library(self):
        # In a time zone whose day differs from UTC's right now, the earlier of
        # the two days is overdue by one reckoning and not the other, so the
        # answer from adding the source must use the same (local) day as the Library.
        import os
        import time
        from datetime import datetime, timedelta, timezone

        from nurse_manager import cli

        now = datetime.now(timezone.utc)
        zone, offset = (("Etc/GMT-14", 14) if (now + timedelta(hours=14)).date() != now.date()
                        else ("Etc/GMT+12", -12))
        previous = os.environ.get("TZ")
        os.environ["TZ"] = zone
        time.tzset()
        try:
            local_today = (now + timedelta(hours=offset)).date().isoformat()
            review = min(local_today, now.date().isoformat())
            ws = str(self.tmp / "tz")
            cli.run(["sample", ws])
            code, env = cli.run(["source-add", ws, "--title", "Guide", "--kind", "public",
                                 "--reference", "https://example.org/guide",
                                 "--review", review])
            self.assertEqual(code, 0, env)
            self.assertEqual(env["data"]["source"]["review_overdue"], review < local_today)
            _, lib = cli.run(["library", ws, "--today", local_today])
            added = next(i for i in lib["data"]["items"] if i["title"] == "Guide")
            self.assertEqual(added, env["data"]["source"])
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_an_empty_workspace_has_an_empty_library(self):
        ws = ManagerWorkspace(self.tmp / "empty", clock=fixed_clock())
        self.addCleanup(ws.close)
        ws.create("Empty", "Test Manager")
        lib = library(ws, today=TODAY)
        self.assertEqual((lib["items"], lib["review_overdue"], lib["projects"]), ([], 0, []))


class FeedbackTests(_TempCase):
    """Project feedback (3.5c): about the work, from a group or role, closed with a response."""

    def project(self, ws, title_prefix):
        return ws.store.conn.execute(
            "SELECT id FROM projects WHERE title LIKE ?", (title_prefix + "%",)).fetchone()[0]

    def test_feedback_shows_on_its_project_open_first(self):
        ws = self.sample()
        huddle = self.project(ws, "Huddle")
        dash = project_dashboard(ws, huddle, today=TODAY)
        self.assertEqual([f["kind"] for f in dash["feedback"]], ["change", "worked"])
        self.assertEqual(dash["readiness"]["open_feedback"], 2)
        ws.address_feedback(dash["feedback"][1]["id"], "Kept the Dates slot in week two.")
        dash = project_dashboard(ws, huddle, today=TODAY)
        self.assertEqual([f["status"] for f in dash["feedback"]], ["open", "addressed"])
        self.assertEqual(dash["feedback"][1]["response"], "Kept the Dates slot in week two.")
        self.assertEqual(dash["feedback"][1]["addressed_on"], TODAY)
        self.assertEqual(dash["readiness"]["open_feedback"], 1)

    def test_addressed_needs_a_written_response_even_in_the_database(self):
        ws = self.sample()
        fid = project_dashboard(ws, self.project(ws, "Huddle"), today=TODAY)["feedback"][0]["id"]
        with self.assertRaises(ManagerError):
            ws.address_feedback(fid, "   ")
        with self.assertRaises(sqlite3.IntegrityError):
            ws.store.conn.execute(
                "UPDATE project_feedback SET status = 'addressed' WHERE id = ?", (fid,))
        ws.address_feedback(fid, "Capped Asks at three.")
        with self.assertRaises(ManagerError):
            ws.address_feedback(fid, "Again.")

    def test_capture_rules_apply(self):
        ws = self.sample()
        pid = self.project(ws, "Huddle")
        with self.assertRaises(CaptureRefused):
            ws.add_feedback(pid, "Night shift", "change", "Call 555-867-5309 about it", TODAY)
        with self.assertRaises(CaptureRefused):
            ws.add_feedback(pid, "jane.doe@example.org", "worked", "Good pilot", TODAY)
        for args in (("", "worked", "Good", TODAY), ("Group", "praise", "Good", TODAY),
                     ("Group", "worked", "", TODAY), ("Group", "worked", "Good", "last week"),
                     ("Group", "worked", "Good", "2030-01-01"), ("x" * 81, "worked", "Good", TODAY),
                     ("Group", "worked", "x" * 1001, TODAY)):
            with self.subTest(args=args[:2]), self.assertRaises(ManagerError):
                ws.add_feedback(pid, *args)
        with self.assertRaises(ManagerError):
            ws.add_feedback("prj-000000000000", "Group", "worked", "Good", TODAY)
        with self.assertRaises(ManagerError):
            ws.address_feedback("fbk-000000000000", "Done")

    def test_addressing_is_decided_inside_the_write(self):
        # Two requests that both read "open" before either writes: only one wins.
        from unittest import mock

        ws = self.sample()
        fid = project_dashboard(ws, self.project(ws, "Huddle"), today=TODAY)["feedback"][0]["id"]
        stale = dict(ws._require_row("project_feedback", fid))
        ws.address_feedback(fid, "First response.")
        with mock.patch.object(ws, "_require_row", return_value=stale), \
                self.assertRaises(ManagerError):
            ws.address_feedback(fid, "Second response.")
        row = ws._require_row("project_feedback", fid)
        self.assertEqual(row["response"], "First response.")
        events = [e for e in ws.store.events() if e["record_id"] == fid and e["kind"] == "address"]
        self.assertEqual(len(events), 1)

    @unittest.skipUnless(hasattr(__import__("time"), "tzset"), "needs a settable time zone")
    def test_feedback_dates_follow_the_local_calendar_day(self):
        import os
        import time

        previous = os.environ.get("TZ")
        os.environ["TZ"] = "Etc/GMT-10"  # UTC+10: local midnight comes first
        time.tzset()
        try:
            # 15:00 UTC on 30 September is 01:00 on 1 October locally.
            ws, _ = load_sample(self.tmp / "tz", clock=fixed_clock("2026-09-30T15:00:00+00:00"))
            self.addCleanup(ws.close)
            self.assertEqual(ws.local_today(), "2026-10-01")
            fid = ws.add_feedback(self.project(ws, "Huddle"), "Night shift huddle", "worked",
                                  "The Dates slot helped.", "2026-10-01")
            ws.address_feedback(fid, "Kept it.")
            self.assertEqual(ws._require_row("project_feedback", fid)["addressed_on"],
                             "2026-10-01")
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_feedback_is_audited(self):
        ws = self.sample()
        fid = ws.add_feedback(self.project(ws, "Unit"), "Council members", "worked",
                              "The draft scope section was clear.", TODAY)
        ws.address_feedback(fid, "Shared at the next meeting.")
        kinds = [(e["kind"], e["record_type"], e["record_id"]) for e in ws.store.events()]
        self.assertIn(("create", "feedback", fid), kinds)
        self.assertIn(("address", "feedback", fid), kinds)


class ProjectDashboardTests(_TempCase):
    def project(self, ws, title_prefix):
        return ws.store.conn.execute(
            "SELECT id FROM projects WHERE title LIKE ?", (title_prefix + "%",)
        ).fetchone()[0]

    def test_tasks_are_the_tables_rows_for_this_project(self):
        ws = self.sample()
        pid = self.project(ws, "Unit Based Council")
        dash = project_dashboard(ws, pid, today=TODAY)
        rows = [r for r in table(ws)["rows"] if r["project"] == dash["project"]["title"]]
        self.assertEqual(dash["tasks"], rows)
        self.assertEqual(dash["project"]["owner"], "Sample Manager")

    def test_readiness_is_stated_facts_from_the_records(self):
        ws = self.sample()
        ubc = project_dashboard(ws, self.project(ws, "Unit Based Council"), today=TODAY)
        self.assertEqual(ubc["readiness"], {
            "has_next_milestone": True, "open_tasks": 3, "completed_tasks": 0,
            "blocked_tasks": 1, "needs_judgment": 1, "overdue_tasks": 0,
            "tasks_without_next_action": 1,
            "open_feedback": 1,
        })
        self.assertTrue(ubc["resources"][0]["review_overdue"])
        edu = project_dashboard(ws, self.project(ws, "Fall education"), today=TODAY)
        self.assertEqual(edu["readiness"]["overdue_tasks"], 1)
        self.assertEqual([e["task"] for e in edu["evidence"]], ["List required annual education modules"])
        huddle = project_dashboard(ws, self.project(ws, "Huddle"), today=TODAY)
        self.assertEqual([d["question"] for d in huddle["decisions"]], ["Which huddle format do we pilot?"])

    def test_a_project_from_elsewhere_is_refused(self):
        other = self.sample("other")
        foreign = self.project(other, "Huddle")
        ws = self.empty()
        with self.assertRaises(ManagerError):
            project_dashboard(ws, foreign, today=TODAY)
        with self.assertRaises(ManagerError):
            project_dashboard(ws, "prj-000000000000", today=TODAY)


if __name__ == "__main__":
    unittest.main()
