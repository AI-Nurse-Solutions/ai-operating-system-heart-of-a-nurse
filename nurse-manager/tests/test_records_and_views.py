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
from nurse_manager.views import board, mission_control, project_dashboard, table

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
            "DROP TABLE assistant_requests; DROP TABLE assistant_settings;"
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
