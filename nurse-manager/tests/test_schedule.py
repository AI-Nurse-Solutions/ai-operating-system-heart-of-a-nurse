"""The recurring weekly brief (5.1): restart, retry, and dedup, plus its rules.

Every run here is records-only and waits for the manager: it never calls a
model and never accepts a draft.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401

from nurse_manager.brief import BriefService
from nurse_manager.schedule import BriefSchedule
from nurse_manager.services import ManagerError, ManagerWorkspace
from nurse_manager.store import Store, _connect, _migrations

OWNER = "Test Manager"
UTC = timezone.utc
MONDAY = datetime(2026, 9, 28, tzinfo=UTC)  # week of 2026-09-28


class Clock:
    """A clock the test moves by hand; each reading advances one second."""

    def __init__(self, at: datetime):
        self.at = at

    def set(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> str:
        self.at += timedelta(seconds=1)
        return self.at.isoformat()


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "ws"
        self.clock = Clock(MONDAY)
        self.ws = self.open()
        self.ws.create("Schedule workspace", OWNER)

    def open(self) -> ManagerWorkspace:
        """Open the workspace, as a new process (or an app restart) would."""
        ws = ManagerWorkspace(self.root, clock=self.clock)
        self.addCleanup(ws.close)
        return ws

    def schedule(self, ws=None) -> BriefSchedule:
        return BriefSchedule(ws or self.ws, tz=UTC)

    def turn_on(self, weekday=0, hour=7):
        self.schedule().configure(enabled=True, weekday=weekday, hour=hour, by=OWNER)

    def revisions(self, week_of="2026-09-28") -> list[sqlite3.Row]:
        return list(self.ws.store.conn.execute(
            "SELECT r.* FROM artifact_revisions r JOIN artifacts a ON a.id = r.artifact_id"
            " WHERE a.week_of = ?", (week_of,)))

    def runs(self) -> list[sqlite3.Row]:
        return list(self.ws.store.conn.execute("SELECT * FROM brief_runs ORDER BY week_of"))


class DefaultAndTimingTests(_Case):
    def test_off_until_the_manager_turns_it_on(self):
        self.clock.set(MONDAY + timedelta(days=3))
        self.assertEqual(self.schedule().run_due()["outcome"], "off")
        view = self.schedule().view()
        self.assertEqual((view["enabled"], view["next_at"], view["last_run"]), (False, None, None))
        self.assertEqual((self.runs(), self.revisions()), ([], []))

    def test_not_before_the_chosen_hour_then_a_records_only_draft_that_waits(self):
        self.turn_on(weekday=0, hour=7)
        self.clock.set(MONDAY + timedelta(hours=6, minutes=59))
        self.assertEqual(self.schedule().run_due()["outcome"], "not_due")
        self.assertEqual(self.schedule().view()["next_at"], "2026-09-28T07:00:00+00:00")
        self.clock.set(MONDAY + timedelta(hours=7))
        result = self.schedule().run_due()
        self.assertEqual((result["outcome"], result["week_of"]), ("drafted", "2026-09-28"))
        [revision] = self.revisions()
        self.assertEqual(result["run"]["revision_id"], revision["id"])
        # A draft by the owner from records: never accepted, never a model's.
        self.assertEqual((revision["status"], revision["created_by"], revision["accepted_by"]),
                         ("draft", OWNER, None))
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM assistant_requests").fetchone()[0], 0)
        self.assertEqual(self.schedule().view()["next_at"], "2026-10-05T07:00:00+00:00")

    def test_a_week_already_done_shows_next_week_even_if_the_hour_moves_later(self):
        self.turn_on(hour=7)
        self.clock.set(MONDAY + timedelta(hours=8))
        self.assertEqual(self.schedule().run_due()["outcome"], "drafted")
        self.turn_on(hour=21)
        self.assertEqual(self.schedule().view()["next_at"], "2026-10-05T21:00:00+00:00")

    def test_a_time_slept_through_is_caught_up_but_earlier_weeks_are_not_backfilled(self):
        self.turn_on(weekday=0, hour=7)
        # Off or asleep for two whole weeks; first awake on a Thursday.
        self.clock.set(MONDAY + timedelta(days=17, hours=10))
        result = self.schedule().run_due()
        self.assertEqual((result["outcome"], result["week_of"]), ("drafted", "2026-10-12"))
        self.assertEqual([r["week_of"] for r in self.runs()], ["2026-10-12"])

    def test_the_hour_is_the_computers_local_time(self):
        plus_ten = timezone(timedelta(hours=10))
        self.turn_on(weekday=0, hour=7)
        # 22:00 UTC on Sunday is 08:00 on Monday at UTC+10: due there.
        self.clock.set(MONDAY - timedelta(hours=2))
        result = BriefSchedule(self.ws, tz=plus_ten).run_due()
        self.assertEqual((result["outcome"], result["week_of"]), ("drafted", "2026-09-28"))


class DedupTests(_Case):
    def test_asking_again_the_same_week_changes_nothing(self):
        self.turn_on()
        self.clock.set(MONDAY + timedelta(hours=8))
        self.assertEqual(self.schedule().run_due()["outcome"], "drafted")
        for _ in range(3):
            self.assertEqual(self.schedule().run_due()["outcome"], "done")
        self.assertEqual(len(self.revisions()), 1)
        self.assertEqual(len(self.runs()), 1)

    def test_two_processes_make_one_draft(self):
        self.turn_on()
        self.clock.set(MONDAY + timedelta(hours=8))
        other = self.open()
        outcomes = sorted([self.schedule().run_due()["outcome"],
                           self.schedule(other).run_due()["outcome"]])
        self.assertEqual(outcomes, ["done", "drafted"])
        self.assertEqual(len(self.revisions()), 1)

    def test_the_managers_own_brief_wins(self):
        self.turn_on()
        mine = BriefService(self.ws).draft_weekly_brief("2026-09-28", "2026-09-28")
        self.clock.set(MONDAY + timedelta(hours=8))
        result = self.schedule().run_due()
        self.assertEqual((result["outcome"], result["run"]["revision_id"]), ("skipped", mine.id))
        self.assertIn("already has a brief", result["run"]["reason"])
        self.assertEqual(len(self.revisions()), 1)

    def test_a_week_already_done_is_not_redone_after_the_hour_changes(self):
        self.turn_on(hour=7)
        self.clock.set(MONDAY + timedelta(hours=8))
        self.schedule().run_due()
        self.turn_on(hour=9)
        self.clock.set(MONDAY + timedelta(hours=10))
        self.assertEqual(self.schedule().run_due()["outcome"], "done")
        self.assertEqual(len(self.revisions()), 1)


    def test_a_manual_draft_racing_the_scheduler_joins_the_same_week(self):
        import threading

        errors = []

        def manual_draft():  # the manager's request, from its own connection
            other = ManagerWorkspace(self.root, clock=self.clock)
            try:
                BriefService(other).add_weekly_draft("2026-09-28", "Manual draft.", [], OWNER)
            except Exception as exc:  # noqa: BLE001 - reported below
                errors.append(exc)
            finally:
                other.close()

        with self.ws.store.transaction():
            # The scheduler holds the write lock and has written this week's draft...
            BriefService(self.ws).add_weekly_draft("2026-09-28", "Scheduled draft.", [], OWNER)
            # ...when the manager asks for a draft.
            manual = threading.Thread(target=manual_draft)
            manual.start()
            time.sleep(0.3)
        manual.join(10)
        self.assertEqual(errors, [])
        artifacts = self.ws.store.conn.execute(
            "SELECT count(*) FROM artifacts WHERE week_of = '2026-09-28'").fetchone()[0]
        self.assertEqual((artifacts, len(self.revisions())), (1, 2))


    def test_turning_it_off_while_a_run_waits_for_the_lock_stops_that_run(self):
        import threading

        self.turn_on()
        self.clock.set(MONDAY + timedelta(hours=8))
        results = []

        def scheduler():  # the app's thread, on its own connection
            other = ManagerWorkspace(self.root, clock=self.clock)
            try:
                results.append(BriefSchedule(other, tz=UTC).run_due()["outcome"])
            finally:
                other.close()

        with self.ws.store.transaction():
            # The manager is saving "off" when the scheduler, which read "on", asks.
            self.schedule().configure(enabled=False, weekday=0, hour=7, by=OWNER)
            thread = threading.Thread(target=scheduler)
            thread.start()
            time.sleep(0.3)
        thread.join(10)
        self.assertEqual(results, ["off"])
        self.assertEqual((self.revisions(), self.runs()), ([], []))


class RestartTests(_Case):
    def test_settings_and_runs_survive_a_restart(self):
        self.turn_on(weekday=2, hour=6)
        self.clock.set(MONDAY + timedelta(days=2, hours=7))
        self.assertEqual(self.schedule().run_due()["outcome"], "drafted")
        self.ws.close()
        again = self.open()
        view = self.schedule(again).view()
        self.assertEqual((view["enabled"], view["weekday"], view["hour"]), (True, 2, 6))
        self.assertEqual(view["last_run"]["status"], "drafted")
        self.assertEqual(self.schedule(again).run_due()["outcome"], "done")
        # The next week, after a restart, runs once for that week.
        self.clock.set(MONDAY + timedelta(days=9, hours=7))
        self.assertEqual(self.schedule(again).run_due()["outcome"], "drafted")
        self.assertEqual([r["week_of"] for r in again.store.conn.execute(
            "SELECT week_of FROM brief_runs ORDER BY week_of")], ["2026-09-28", "2026-10-05"])

    def test_a_crash_mid_run_leaves_nothing_half_done(self):
        self.turn_on()
        self.clock.set(MONDAY + timedelta(hours=8))
        # The process dies after the draft is written but before the run is recorded.
        with mock.patch.object(BriefSchedule, "_record", side_effect=KeyboardInterrupt), \
                self.assertRaises(KeyboardInterrupt):
            self.schedule().run_due()
        self.ws.close()
        again = self.open()
        self.assertEqual(again.store.conn.execute(
            "SELECT count(*) FROM artifact_revisions").fetchone()[0], 0)
        self.assertEqual(self.schedule(again).run_due()["outcome"], "drafted")
        self.assertEqual(again.store.conn.execute(
            "SELECT count(*) FROM artifact_revisions").fetchone()[0], 1)


class RetryTests(_Case):
    def fail_drafting(self, times):
        real = BriefService.draft_weekly_brief
        calls = {"n": 0}

        def flaky(service, week_of, today):
            calls["n"] += 1
            if calls["n"] <= times:
                raise sqlite3.OperationalError("database is locked")
            return real(service, week_of, today)

        return mock.patch.object(BriefService, "draft_weekly_brief", flaky)

    def test_a_failure_is_retried_after_a_wait_then_succeeds(self):
        self.turn_on()
        start = MONDAY + timedelta(hours=8)
        self.clock.set(start)
        with self.fail_drafting(1):
            failed = self.schedule().run_due()
            self.assertEqual((failed["outcome"], failed["run"]["attempts"]), ("failed", 1))
            self.assertIn("database is locked", failed["run"]["reason"])
            self.assertEqual(datetime.fromisoformat(failed["run"]["next_attempt_at"])
                             - datetime.fromisoformat(failed["run"]["at"]), timedelta(minutes=5))
            self.assertEqual(self.schedule().run_due()["outcome"], "waiting")
            self.clock.set(start + timedelta(minutes=6))
            done = self.schedule().run_due()
        self.assertEqual((done["outcome"], done["run"]["attempts"]), ("drafted", 2))
        self.assertEqual(done["run"]["reason"], "")
        self.assertEqual(len(self.revisions()), 1)

    def test_it_gives_up_after_three_attempts_and_says_so(self):
        self.turn_on()
        start = MONDAY + timedelta(hours=8)
        self.clock.set(start)
        with self.fail_drafting(99):
            self.assertEqual(self.schedule().run_due()["outcome"], "failed")
            self.clock.set(start + timedelta(minutes=6))
            second = self.schedule().run_due()
            self.assertEqual((second["outcome"], second["run"]["attempts"]), ("failed", 2))
            self.clock.set(start + timedelta(minutes=40))
            third = self.schedule().run_due()
            self.clock.set(start + timedelta(hours=5))
            later = self.schedule().run_due()
        self.assertEqual((third["outcome"], third["run"]["attempts"]), ("gave_up", 3))
        self.assertIsNone(third["run"]["next_attempt_at"])
        self.assertIn("draft this week's brief by hand", third["run"]["reason"])
        self.assertEqual(later["outcome"], "gave_up")
        self.assertEqual(self.revisions(), [])
        # The next week starts fresh.
        self.clock.set(MONDAY + timedelta(days=7, hours=8))
        self.assertEqual(self.schedule().run_due()["outcome"], "drafted")

    def test_the_next_time_shown_is_the_retry_then_next_week_after_giving_up(self):
        self.turn_on()
        start = MONDAY + timedelta(hours=8)
        self.clock.set(start)
        with self.fail_drafting(99):
            failed = self.schedule().run_due()
            self.assertEqual(self.schedule().view()["next_at"],
                             failed["run"]["next_attempt_at"])
            self.clock.set(start + timedelta(minutes=6))
            self.schedule().run_due()
            self.clock.set(start + timedelta(minutes=40))
            self.assertEqual(self.schedule().run_due()["outcome"], "gave_up")
        self.assertEqual(self.schedule().view()["next_at"], "2026-10-05T07:00:00+00:00")

    def test_a_failure_after_another_process_finished_leaves_its_result(self):
        self.turn_on()
        self.clock.set(MONDAY + timedelta(hours=8))
        self.assertEqual(self.schedule().run_due()["outcome"], "drafted")
        now = datetime.fromisoformat(self.clock()).astimezone(UTC)
        result = self.schedule()._failed("2026-09-28", now, RuntimeError("late"))
        self.assertEqual((result["outcome"], result["run"]["status"]), ("done", "drafted"))


@unittest.skipUnless(hasattr(time, "tzset"), "needs a settable local time zone")
class LocalTimeTests(_Case):
    def test_next_weeks_time_uses_that_days_own_offset(self):
        old = os.environ.get("TZ")
        self.addCleanup(time.tzset)
        self.addCleanup(lambda: os.environ.pop("TZ", None) if old is None
                        else os.environ.__setitem__("TZ", old))
        os.environ["TZ"] = "America/New_York"
        time.tzset()
        local = BriefSchedule(self.ws)  # the computer's own zone
        # US daylight saving ends on 2026-11-01: 07:00 is -04:00 before, -05:00 after.
        self.assertEqual(local.due_at(date(2026, 10, 26), 0, 7).isoformat(),
                         "2026-10-26T07:00:00-04:00")
        self.assertEqual(local.due_at(date(2026, 11, 2), 0, 7).isoformat(),
                         "2026-11-02T07:00:00-05:00")


class MigrationRaceTests(unittest.TestCase):
    def test_a_migration_another_process_applied_meanwhile_is_not_run_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workspace.sqlite"
            Store(path).conn.close()

            class StaleRead:
                """A connection whose first look at the applied versions is out of date,
                as if another process migrated between that read and the write lock."""

                def __init__(self, conn):
                    self.conn, self.stale = conn, True

                def execute(self, sql, *args):
                    if self.stale and sql == "SELECT version FROM schema_migrations":
                        self.stale = False
                        return iter(())
                    return self.conn.execute(sql, *args)

                def __getattr__(self, name):
                    return getattr(self.conn, name)

            late = Store.__new__(Store)
            late.path, late.clock = path, lambda: "2026-09-28T00:00:00+00:00"
            late.conn = StaleRead(_connect(path))
            late._migrate()  # must not try to create the tables again
            self.assertEqual(late.conn.execute(
                "SELECT count(*) FROM schema_migrations").fetchone()[0], len(_migrations()))
            late.conn.close()


class SettingsTests(_Case):
    def test_only_the_owner_changes_it_and_values_are_checked(self):
        with self.assertRaises(ManagerError):
            self.schedule().configure(enabled=True, weekday=0, hour=7, by="Someone Else")
        for weekday, hour in ((7, 7), (-1, 7), (0, 24), (0, -1)):
            with self.subTest(weekday=weekday, hour=hour), self.assertRaises(ManagerError):
                self.schedule().configure(enabled=True, weekday=weekday, hour=hour, by=OWNER)
        with self.assertRaises(sqlite3.IntegrityError):
            self.ws.store.conn.execute(
                "INSERT INTO brief_schedule VALUES (?, 1, 9, 7, ?, ?)",
                (self.ws.info.id, OWNER, "2026-09-28T00:00:00+00:00"))

    def test_changes_are_audited_and_turning_it_off_stops_runs(self):
        self.turn_on()
        self.schedule().configure(enabled=False, weekday=0, hour=7, by=OWNER)
        self.clock.set(MONDAY + timedelta(hours=8))
        self.assertEqual(self.schedule().run_due()["outcome"], "off")
        kinds = [e["kind"] for e in self.ws.store.events() if e["record_type"] == "brief_schedule"]
        self.assertEqual(kinds, ["configure", "configure"])

    def test_a_drafted_run_needs_its_revision_even_in_the_database(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.ws.store.conn.execute(
                "INSERT INTO brief_runs (workspace_id, week_of, status, attempts, updated_at)"
                " VALUES (?, '2026-09-28', 'drafted', 1, ?)",
                (self.ws.info.id, "2026-09-28T00:00:00+00:00"))


if __name__ == "__main__":
    unittest.main()
