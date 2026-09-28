"""Assistants at work and the stop control (step 5.3): the stop-control tests.

The exit check: when the manager stops assistants, nothing new is sent,
work already on its way is abandoned at once and its reply is never saved
or shown, and the recurring brief waits, until the manager lets
assistants work again.

The model here is an in-process stand-in that blocks until the test lets
it answer, so "while the model is working" is a state the test controls,
not a race it hopes to win.
"""

from __future__ import annotations

import sqlite3
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import _bootstrap  # noqa: F401
from _bootstrap import fixed_clock

from nurse_manager import store as store_module
from nurse_manager.assistant import AssistantService, ProviderReply
from nurse_manager.control import AssistantControl, assistants_at_work
from nurse_manager.sample import load_sample
from nurse_manager.schedule import BriefSchedule
from nurse_manager.services import ManagerError, ManagerWorkspace
from nurse_manager.store import _connect, _split_sql

WEEK = "2026-09-28"
TODAY = "2026-09-30"
OWNER = "Sample Manager"
POLL = 0.05


class HeldModel:
    """A model that starts working when asked and answers only when released."""

    kind, model, runs_on = "local", "held", "this computer"

    def __init__(self, reply=None, *, during=None):
        self.started = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()
        self.calls = 0
        self.reply = reply
        self.during = during  # run inside the call, before answering

    def estimate_cents(self, *args):
        return 0

    def complete(self, system, prompt, *, max_output_tokens, timeout):
        self.calls += 1
        self.started.set()
        try:
            if self.during:
                self.during()
            else:
                self.release.wait(10)
            text = self.reply(prompt) if callable(self.reply) else prompt
            return ProviderReply(text=text, cost_cents=0)
        finally:
            self.finished.set()


def cited_lines(prompt: str) -> str:
    """A faithful rewrite: the headings and the cited lines."""
    return "\n".join(line for line in prompt.splitlines() if line.startswith("#") or "`" in line)


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "ws"
        self.clock = fixed_clock()
        self.ws, _ = load_sample(self.root, clock=self.clock)
        self.addCleanup(self.ws.close)
        # A model must be connected for requests to be sent at all.
        AssistantService(self.ws).connect_local(OWNER, "held")
        self.control = AssistantControl(self.ws)

    def open(self) -> ManagerWorkspace:
        """Another connection, as another request thread in the app has."""
        ws = ManagerWorkspace(self.root, clock=self.clock)
        self.addCleanup(ws.close)
        return ws

    def service(self, model, ws=None) -> AssistantService:
        return AssistantService(ws or self.ws, provider_factory=lambda s: model, timeout=10,
                                stop_poll=POLL)

    def in_background(self, work):
        """Run ``work(ws)`` on its own thread with its own connection."""
        box: dict = {}

        def run():
            ws = ManagerWorkspace(self.root, clock=self.clock)
            try:
                box["result"] = work(ws)
            except BaseException as exc:  # noqa: BLE001 - reported to the test
                box["error"] = exc
            finally:
                ws.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread, box

    def ledger(self):
        return list(self.ws.store.conn.execute(
            "SELECT * FROM assistant_requests ORDER BY created_at, id"))

    def model_drafts(self):
        return list(self.ws.store.conn.execute(
            "SELECT * FROM artifact_revisions WHERE created_by LIKE 'assistant:%'"))

    def section(self):
        return assistants_at_work(self.ws)


class StopWhileWorkingTests(_Case):
    def test_stopping_abandons_a_brief_being_drafted_and_discards_the_reply(self):
        model = HeldModel(cited_lines)
        thread, box = self.in_background(
            lambda ws: self.service(model, ws).draft_weekly_brief(WEEK, TODAY, OWNER))
        self.assertTrue(model.started.wait(5))

        # It is shown as at work while the model works.
        (item,) = self.section()["items"]
        self.assertEqual((item["kind"], item["title"]), ("request", "Drafting this week's brief"))
        self.assertIn("Waiting for held on this computer", item["detail"])
        self.assertEqual(item["id"], self.ledger()[-1]["id"])

        started = time.monotonic()
        self.control.stop(OWNER)
        thread.join(5)
        self.assertFalse(thread.is_alive(), "the request did not return after the stop")
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertFalse(model.finished.is_set(), "it returned before the model answered")

        result = box["result"]
        self.assertEqual(result["outcome"], "stopped")
        self.assertFalse(result["drafted_by_model"])
        self.assertIn("discarded", result["reason"])
        self.assertEqual(result["revision"]["created_by"], OWNER)  # records only
        (row,) = self.ledger()
        self.assertEqual(row["outcome"], "stopped")
        self.assertIsNotNone(row["finished_at"])

        # The model answers after all: nothing it says is used.
        model.release.set()
        self.assertTrue(model.finished.wait(5))
        time.sleep(POLL * 4)
        self.assertEqual(self.model_drafts(), [])
        self.assertEqual([r["outcome"] for r in self.ledger()], ["stopped"])
        section = self.section()
        self.assertEqual((section["stopped"], section["items"]), (True, []))

    def test_stopping_abandons_a_project_question_and_the_answer_is_never_shown(self):
        project_id = self.ws.store.conn.execute(
            "SELECT id FROM projects ORDER BY created_at LIMIT 1").fetchone()["id"]
        model = HeldModel(cited_lines)
        thread, box = self.in_background(lambda ws: self.service(model, ws).answer_project_question(
            project_id, "What comes next?", TODAY, OWNER))
        self.assertTrue(model.started.wait(5))
        self.assertEqual(self.section()["items"][0]["title"],
                         "Answering a question about a project")
        self.control.stop(OWNER)
        thread.join(5)
        self.assertFalse(thread.is_alive())
        model.release.set()
        result = box["result"]
        self.assertEqual((result["outcome"], result["answer"], result["answered_by_model"]),
                         ("stopped", "", False))
        (row,) = self.ledger()
        self.assertEqual((row["outcome"], row["output_sha256"]), ("stopped", ""))
        # With no answer bound to the request, nothing can be kept as a note.
        with self.assertRaises(ManagerError):
            self.service(model).keep_project_note(row["id"], project_id, "What comes next?",
                                                  cited_lines("x"), OWNER)

    def elsewhere(self, *changes):
        """Stop or restart from another connection, as the stop button's request does."""
        def run():
            ws = ManagerWorkspace(self.root, clock=self.clock)
            try:
                for change in changes:
                    getattr(AssistantControl(ws), change)(OWNER)
            finally:
                ws.close()
        return run

    def test_a_stop_landing_after_the_reply_is_checked_still_discards_it(self):
        # The model answered and every check passed; the stop lands just
        # before the save. The save is decided inside the write, so the
        # reply is still discarded.
        model = HeldModel(cited_lines, during=lambda: None)
        service = self.service(model)
        check = AssistantService._check_output

        def check_then_stop(self_, *args, **kwargs):
            problem = check(self_, *args, **kwargs)
            self.elsewhere("stop")()
            return problem

        for ask in (lambda: service.draft_weekly_brief(WEEK, TODAY, OWNER),
                    lambda: service.answer_project_question(
                        self.ws.store.conn.execute("SELECT id FROM projects").fetchone()[0],
                        "Next?", TODAY, OWNER)):
            with self.subTest(ask=ask), \
                    mock.patch.object(AssistantService, "_check_output", check_then_stop):
                result = ask()
                self.assertEqual(result["outcome"], "stopped")
                self.assertEqual(result.get("answer", ""), "")
                self.assertEqual(self.model_drafts(), [])
                self.assertEqual(self.ledger()[-1]["output_sha256"], "")
                self.control.resume(OWNER)

    def test_stop_then_restart_while_it_works_still_discards_that_reply(self):
        model = HeldModel(cited_lines, during=self.elsewhere("stop", "resume"))
        service = self.service(model)
        service.stop_poll = 60  # the model answers long before the first poll
        result = service.draft_weekly_brief(WEEK, TODAY, OWNER)
        self.assertEqual(result["outcome"], "stopped")
        self.assertEqual(self.model_drafts(), [])
        # Work started after the restart goes ahead.
        again = self.service(HeldModel(cited_lines, during=lambda: None))
        self.assertEqual(again.draft_weekly_brief(WEEK, TODAY, OWNER)["outcome"], "drafted")

    def test_an_abandoned_request_counts_as_sent(self):
        before = AssistantService(self.ws).status()["requests_today"]
        model = HeldModel(cited_lines)
        thread, _box = self.in_background(
            lambda ws: self.service(model, ws).draft_weekly_brief(WEEK, TODAY, OWNER))
        self.assertTrue(model.started.wait(5))
        self.control.stop(OWNER)
        thread.join(5)
        model.release.set()
        self.assertEqual(AssistantService(self.ws).status()["requests_today"], before + 1)


class StoppedBeforeSendingTests(_Case):
    def test_nothing_is_sent_while_stopped(self):
        self.control.stop(OWNER)
        model = HeldModel(cited_lines, during=lambda: None)
        service = self.service(model)
        preview = service.preview_weekly_brief(WEEK, TODAY)
        self.assertFalse(preview["will_send"])
        self.assertIn("assistants are stopped", preview["reason"])
        result = service.draft_weekly_brief(WEEK, TODAY, OWNER)
        self.assertEqual(result["outcome"], "refused_stopped")
        self.assertEqual(result["revision"]["created_by"], OWNER)
        self.assertEqual(model.calls, 0)
        project_id = self.ws.store.conn.execute("SELECT id FROM projects LIMIT 1").fetchone()[0]
        self.assertFalse(service.preview_project_question(project_id, "Next?", TODAY)["will_send"])
        answer = service.answer_project_question(project_id, "Next?", TODAY, OWNER)
        self.assertEqual((answer["outcome"], answer["answer"]), ("refused_stopped", ""))
        self.assertEqual(model.calls, 0)
        # Refused requests were never sent, so they do not count.
        self.assertEqual(service.status()["requests_today"], 0)

    def test_a_stop_after_the_preview_is_honoured_when_sending(self):
        model = HeldModel(cited_lines, during=lambda: None)
        service = self.service(model)
        preview = service.preview_weekly_brief(WEEK, TODAY)
        self.assertTrue(preview["will_send"])
        gates = AssistantService._gates

        def stop_after_the_gates(self_, *args, **kwargs):
            checked = gates(self_, *args, **kwargs)
            AssistantControl(self_.ws).stop(OWNER)  # lands after every gate passed
            return checked

        with mock.patch.object(AssistantService, "_gates", stop_after_the_gates):
            result = service.draft_weekly_brief(WEEK, TODAY, OWNER,
                                                reviewed_prompt_sha256=preview["prompt_sha256"])
        self.assertEqual(result["outcome"], "refused_stopped")
        self.assertEqual(model.calls, 0)

    def test_a_stop_and_restart_while_the_request_is_prepared_still_refuses_it(self):
        # The request began before the stop, so it stays abandoned even though
        # assistants were let work again before it reached the model.
        model = HeldModel(cited_lines, during=lambda: None)
        service = self.service(model)
        project_id = self.ws.store.conn.execute("SELECT id FROM projects LIMIT 1").fetchone()[0]
        gates = AssistantService._gates

        def stop_and_restart_during_the_gates(self_, *args, **kwargs):
            AssistantControl(self_.ws).stop(OWNER)
            AssistantControl(self_.ws).resume(OWNER)
            return gates(self_, *args, **kwargs)

        with mock.patch.object(AssistantService, "_gates", stop_and_restart_during_the_gates):
            brief = service.draft_weekly_brief(WEEK, TODAY, OWNER)
            answer = service.answer_project_question(project_id, "Next?", TODAY, OWNER)
        self.assertEqual((brief["outcome"], answer["outcome"]),
                         ("refused_stopped", "refused_stopped"))
        self.assertEqual((answer["answer"], model.calls), ("", 0))
        self.assertEqual(self.model_drafts(), [])
        # Asked again after the restart, it goes ahead.
        self.assertEqual(service.draft_weekly_brief(WEEK, TODAY, OWNER)["outcome"], "drafted")

    def test_letting_assistants_work_again_is_explicit_and_owner_only(self):
        with self.assertRaises(ManagerError):
            self.control.stop("Someone Else")
        first = self.control.stop(OWNER)
        second = self.control.stop(OWNER)  # stopping twice is always allowed
        self.assertEqual(second["generation"], first["generation"] + 1)
        with self.assertRaises(ManagerError):
            self.control.resume("Someone Else")
        self.assertTrue(self.control.state()["stopped"])
        state = self.control.resume(OWNER)
        self.assertEqual((state["stopped"], state["changed_by"]), (False, OWNER))
        with self.assertRaisesRegex(ManagerError, "not stopped"):
            self.control.resume(OWNER)
        result = self.service(HeldModel(cited_lines, during=lambda: None)).draft_weekly_brief(
            WEEK, TODAY, OWNER)
        self.assertEqual(result["outcome"], "drafted")
        kinds = [e["kind"] for e in self.ws.store.events() if e["record_type"] == "assistants"]
        self.assertEqual(kinds, ["stop", "stop", "resume"])


class MissionControlTests(_Case):
    def test_the_section_says_what_is_stopped_and_what_waits(self):
        section = self.section()
        self.assertEqual((section["state"], section["stopped"], section["changed_at"]),
                         ("empty", False, None))
        self.assertIn("No assistant is running", section["empty_message"])
        BriefSchedule(self.ws, tz=timezone.utc).configure(enabled=True, weekday=4, hour=7,
                                                          by=OWNER)
        (item,) = self.section()["items"]
        self.assertEqual((item["id"], item["kind"]), ("brief-schedule", "schedule"))
        self.assertIn("Fridays at 07:00", item["detail"])
        self.control.stop(OWNER)
        section = self.section()
        self.assertEqual((section["stopped"], section["changed_by"]), (True, OWNER))
        self.assertIn("Waiting while assistants are stopped", section["items"][0]["detail"])
        BriefSchedule(self.ws).configure(enabled=False, weekday=4, hour=7, by=OWNER)
        self.assertIn("Nothing runs until you let them work again",
                      self.section()["empty_message"])

    def test_a_request_left_unfinished_by_a_crash_is_not_shown_for_ever(self):
        def unfinished(created_at):
            request_id = f"air-{created_at[-11:-6].replace(':', '')}0000000"
            self.ws.store.conn.execute(
                "INSERT INTO assistant_requests (id, workspace_id, task, provider, model,"
                " outcome, requested_by, created_at) VALUES (?, ?, 'weekly_brief', 'local',"
                " 'held', 'provider_failed', ?, ?)",
                (request_id, self.ws.info.id, OWNER, created_at))
            return request_id

        now = datetime.fromisoformat(self.clock())
        recent = unfinished((now - timedelta(seconds=10)).isoformat())
        unfinished((now - timedelta(minutes=5)).isoformat())
        self.assertEqual([i["id"] for i in self.section()["items"]], [recent])
        self.control.stop(OWNER)
        self.assertIn("will be discarded", self.section()["items"][0]["detail"])


class RecurringBriefTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.at = datetime(2026, 9, 28, 9, tzinfo=timezone.utc)  # Monday, after 07:00
        self.ws = ManagerWorkspace(Path(tmp.name) / "ws", clock=lambda: self.at.isoformat())
        self.addCleanup(self.ws.close)
        self.ws.create("Stop workspace", "Test Manager")
        self.schedule = BriefSchedule(self.ws, tz=timezone.utc)
        self.schedule.configure(enabled=True, weekday=0, hour=7, by="Test Manager")

    def test_the_recurring_brief_waits_while_stopped_and_runs_after(self):
        AssistantControl(self.ws).stop("Test Manager")
        for _ in range(3):
            self.assertEqual(self.schedule.run_due()["outcome"], "stopped")
        self.assertTrue(self.schedule.view()["stopped"])
        count = "SELECT count(*) FROM brief_runs"
        self.assertEqual(self.ws.store.conn.execute(count).fetchone()[0], 0)
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM artifact_revisions").fetchone()[0], 0)
        AssistantControl(self.ws).resume("Test Manager")
        self.assertFalse(self.schedule.view()["stopped"])
        self.assertEqual(self.schedule.run_due()["outcome"], "drafted")

    def test_a_stop_saved_while_a_run_waited_for_the_lock_governs_it(self):
        other = ManagerWorkspace(self.ws.root, clock=lambda: self.at.isoformat())
        self.addCleanup(other.close)
        settings = BriefSchedule.settings

        def stop_first(self_):
            # The pre-check outside the lock sees "running"; the stop lands
            # before the run takes the lock, and the run must see it.
            if not self_.ws.store.conn.in_transaction:
                AssistantControl(other).stop("Test Manager")
            return settings(self_)

        with mock.patch.object(BriefSchedule, "settings", stop_first):
            self.assertEqual(self.schedule.run_due()["outcome"], "stopped")
        self.assertEqual(self.ws.store.conn.execute(
            "SELECT count(*) FROM brief_runs").fetchone()[0], 0)


class MigrationTests(unittest.TestCase):
    def test_the_request_ledger_is_rebuilt_with_every_row_and_note_kept(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "workspace.sqlite"
        conn = _connect(path)
        conn.execute("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY,"
                     " applied_at TEXT NOT NULL)")
        earlier = [m for m in store_module._migrations() if m[0] < "0010"]
        for version, sql in earlier:
            conn.execute("BEGIN IMMEDIATE")
            for statement in _split_sql(sql):
                conn.execute(statement)
            conn.execute("INSERT INTO schema_migrations VALUES (?, 'then')", (version,))
            conn.execute("COMMIT")
        at = "2026-09-01T09:00:00+00:00"
        conn.executescript(f"""
            INSERT INTO workspaces (id, name, profile, owner, sample, created_at)
                VALUES ('ws-000000000001', 'W', 'personal_manager', 'M', 0, '{at}');
            INSERT INTO projects (id, workspace_id, title, purpose, owner, created_at,
                updated_at)
                VALUES ('prj-000000000001', 'ws-000000000001', 'P', 'p', 'M', '{at}', '{at}');
            INSERT INTO assistant_requests (id, workspace_id, task, provider, model, outcome,
                requested_by, created_at, output_sha256)
                VALUES ('air-000000000001', 'ws-000000000001', 'project_question', 'local',
                        'm', 'answered', 'M', '{at}', 'abc');
            INSERT INTO project_notes (id, workspace_id, project_id, request_id, question,
                body_markdown, body_sha256, written_by, model, kept_by, kept_at)
                VALUES ('note-000000000001', 'ws-000000000001', 'prj-000000000001',
                        'air-000000000001', 'q', 'a', 'h', 'assistant:local', 'm', 'M', '{at}');
        """)
        conn.close()

        store = store_module.Store(path)
        self.addCleanup(store.close)
        self.assertEqual(store.schema_version, "0010_assistant_stop")
        (row,) = store.conn.execute("SELECT * FROM assistant_requests")
        self.assertEqual((row["id"], row["outcome"], row["output_sha256"], row["finished_at"]),
                         ("air-000000000001", "answered", "abc", at))
        self.assertEqual(store.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(store.conn.execute(
            "SELECT request_id FROM project_notes").fetchone()[0], "air-000000000001")
        # The new outcomes are accepted; anything else still is not.
        with self.assertRaises(sqlite3.IntegrityError):
            store.conn.execute("UPDATE assistant_requests SET outcome = 'sent'")
        store.conn.execute("UPDATE assistant_requests SET outcome = 'stopped'")


if __name__ == "__main__":
    unittest.main()
