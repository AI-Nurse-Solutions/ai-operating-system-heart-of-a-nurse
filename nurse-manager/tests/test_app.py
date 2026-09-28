"""The local app host (ADR 0003): authenticated, loopback-only, honest lifetime."""

import http.client
import json
import os
import stat
import sys
import tempfile
import threading
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager import app as local_app
from nurse_manager import resources
from nurse_manager.services import ManagerWorkspace


class _AppCase(unittest.TestCase):
    schedule_interval = 60.0

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.app = local_app.LocalApp(self.home, idle_timeout=120,
                                      schedule_interval=self.schedule_interval)
        self.thread = threading.Thread(target=self.app.serve, daemon=True)
        self.thread.start()
        self.assertTrue(self.app.ready.wait(10), "the app did not start")

    def tearDown(self):
        self.app.stop()
        self.thread.join(timeout=10)
        self._tmp.cleanup()

    def request(self, path, method="GET", body=None, *, token=True, host=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.app.port, timeout=10)
        conn.putrequest(method, path, skip_host=True)
        conn.putheader("Host", host or f"127.0.0.1:{self.app.port}")
        if token:
            conn.putheader("Authorization", f"Bearer {self.app.token if token is True else token}")
        data = b""
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
            conn.putheader("Content-Type", "application/json")
        for name, value in (headers or {}).items():
            conn.putheader(name, value)
        conn.putheader("Content-Length", str(len(data)))
        conn.endheaders(data)
        response = conn.getresponse()
        payload = response.read()
        conn.close()
        return response.status, payload

    def envelope(self, *args, **kwargs):
        status, payload = self.request(*args, **kwargs)
        self.assertEqual(status, 200, payload)
        return json.loads(payload)


class LocalAppTests(_AppCase):
    def test_binds_loopback_only(self):
        self.assertEqual(self.app.server.server_address[0], "127.0.0.1")

    def test_data_needs_the_launch_token_screens_do_not(self):
        self.assertEqual(self.request("/", token=False)[0], 200)
        self.assertEqual(self.request("/app.mjs", token=False)[0], 200)
        for path in ("/app/status", "/ipc/mission", "/ipc/board"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, token=False)[0], 401)
                self.assertEqual(self.request(path, token="wrong-" + "x" * 40)[0], 401)
        self.assertEqual(self.request("/app/quit", "POST", {}, token=False)[0], 401)
        self.assertTrue(self.thread.is_alive(), "an unauthenticated quit must not stop the app")

    def test_foreign_host_and_origin_are_refused(self):
        self.assertEqual(self.request("/app/status", host="evil.example")[0], 421)
        self.assertEqual(self.request("/", token=False, host="evil.example")[0], 421)
        self.assertEqual(self.request("/ipc/init", "POST", {"name": "a", "owner": "b"},
                                      headers={"Origin": "https://evil.example"})[0], 403)

    def test_only_the_listed_writes_are_reachable(self):
        for command in ("export", "approve", "run", "backup", "restore", "show", "mission"):
            with self.subTest(command=command):
                self.assertEqual(self.request(f"/ipc/{command}", "POST", {})[0], 404)
        for command in ("export", "approve", "run", "backup", "restore", "show", "brief",
                        "accept", "assistant-local", "assistant-off", "assistant-brief"):
            with self.subTest(command=command):
                self.assertEqual(self.request(f"/ipc/{command}")[0], 404)
        for command in local_app.WRITE_COMMANDS:
            with self.subTest(command=command):
                refused = self.envelope(f"/ipc/{command}", "POST", {})
                self.assertFalse(refused["ok"])
                self.assertIn("workspace first", refused["error"]["message"])

    def test_onboarding_creates_one_workspace_and_never_replaces_it(self):
        self.assertFalse(self.envelope("/app/status")["has_workspace"])
        refused = self.envelope("/ipc/init", "POST", {"name": "My unit", "owner": "me@example.org"})
        self.assertFalse(refused["ok"])
        self.assertEqual(refused["error"]["type"], "CaptureRefused")
        self.assertFalse(self.envelope("/app/status")["has_workspace"])
        made = self.envelope("/ipc/init", "POST", {"name": "My unit", "owner": "Test Manager"})
        self.assertTrue(made["ok"])
        self.assertTrue(self.envelope("/app/status")["has_workspace"])
        for command, body in (("init", {"name": "Other", "owner": "Someone"}), ("sample", {})):
            with self.subTest(command=command):
                again = self.envelope(f"/ipc/{command}", "POST", body)
                self.assertFalse(again["ok"])
                self.assertIn("already has a workspace", again["error"]["message"])
        mission = self.envelope("/ipc/mission")
        self.assertEqual(mission["data"]["workspace"], "My unit")

    def test_malformed_and_oversized_requests_are_refused(self):
        self.assertEqual(self.request("/ipc/init", "POST", b"not json")[0], 400)
        self.assertEqual(self.request("/ipc/init", "POST", [1, 2])[0], 400)
        self.assertEqual(self.request("/ipc/init", "POST", {"name": 1, "owner": 2})[0], 400)
        big = {"name": "x" * (local_app.MAX_BODY + 10), "owner": "y"}
        self.assertEqual(self.request("/ipc/init", "POST", big)[0], 413)
        conn = http.client.HTTPConnection("127.0.0.1", self.app.port, timeout=10)
        conn.request("POST", "/ipc/init", body="name=a", headers={
            "Host": f"127.0.0.1:{self.app.port}", "Authorization": f"Bearer {self.app.token}",
            "Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(conn.getresponse().status, 415)
        conn.close()

    def test_lock_file_is_private_and_finds_the_running_instance(self):
        lock = self.home / local_app.LOCK_NAME
        self.assertTrue(lock.is_file())
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o600)
        self.assertEqual(local_app._running_instance(self.home), self.app.url)

    def test_quit_stops_the_app_and_clears_the_lock(self):
        self.assertTrue(self.envelope("/app/quit", "POST", {})["ok"])
        self.thread.join(timeout=10)
        self.assertFalse(self.thread.is_alive())
        self.assertFalse((self.home / local_app.LOCK_NAME).exists())
        self.assertIsNone(local_app._running_instance(self.home))


class WorkspaceWriteTests(_AppCase):
    """Reviewing the brief and using AI from the screens, once a workspace exists."""

    def setUp(self):
        super().setUp()
        self.assertTrue(self.envelope("/ipc/sample", "POST", {})["ok"])
        self.body = {"week": "2026-09-28", "today": "2026-09-30"}

    def test_draft_review_and_accept_as_the_workspace_owner(self):
        self.assertIsNone(self.envelope("/ipc/weekly?week=2026-09-28")["data"]["current"])
        draft = self.envelope("/ipc/brief", "POST", self.body)["data"]
        weekly = self.envelope("/ipc/weekly?week=2026-09-28")["data"]
        self.assertEqual(weekly["current"]["revision"]["id"], draft["id"])
        self.assertIn("DRAFT", weekly["current"]["markdown"])
        stale = self.envelope("/ipc/accept", "POST", {"revision": draft["id"], "sha256": "0" * 64})
        self.assertFalse(stale["ok"])
        # A reviewer in the body is ignored: the app accepts as the owner only.
        accepted = self.envelope("/ipc/accept", "POST", {
            "revision": draft["id"], "sha256": draft["sha256"], "reviewer": "Someone Else"})
        self.assertEqual(accepted["data"]["accepted_by"], "Sample Manager")

    def test_learning_from_the_screens(self):
        added = self.envelope("/ipc/learning-add", "POST", {
            "title": "Budget basics (synthetic)", "kind": "course",
            "target_date": "2026-11-30", "hours": "4"})["data"]["item"]
        self.assertEqual((added["status"], added["hours"]), ("planned", 4.0))
        lid = added["id"]
        self.assertEqual(self.envelope("/ipc/learning-start", "POST",
                                       {"learning_id": lid})["data"]["item"]["status"], "in_progress")
        empty = self.envelope("/ipc/learning-complete", "POST",
                              {"learning_id": lid, "takeaway": " ", "completed_on": "2026-09-27"})
        self.assertFalse(empty["ok"])
        done = self.envelope("/ipc/learning-complete", "POST", {
            "learning_id": lid, "takeaway": "Read variances first.",
            "completed_on": "2026-09-27"})["data"]["item"]
        self.assertEqual(done["status"], "completed")
        for command, body in (("learning-add", {"title": "T", "kind": "webinar"}),
                              ("learning-add", {"title": "T", "kind": "course", "hours": "many"}),
                              ("learning-add", {"title": "T", "kind": "course", "target_date": "x"}),
                              ("learning-start", {"learning_id": "nope"}),
                              ("learning-complete", {"learning_id": lid, "completed_on": "x",
                                                     "takeaway": "t"})):
            with self.subTest(command=command, body=body):
                self.assertEqual(self.request(f"/ipc/{command}", "POST", body)[0], 400)
        view = self.envelope("/ipc/learning?today=2026-09-30")["data"]
        self.assertIn(lid, [i["id"] for i in view["items"]])

    def test_contributions_from_the_screens(self):
        view = self.envelope("/ipc/contributions?today=2026-09-30")["data"]
        project = view["projects"][0]["id"]
        added = self.envelope("/ipc/contribution-add", "POST", {
            "title": "Charter template (synthetic)", "kind": "committee",
            "occurred_on": "2026-09-27", "my_part": "Drafted it.",
            "shared_credit": "Unit Based Council members", "project_id": project,
        })["data"]["item"]
        self.assertEqual((added["status"], added["project_id"]), ("draft", project))
        cid = added["id"]
        empty = self.envelope("/ipc/contribution-verify", "POST",
                              {"contribution_id": cid, "evidence": " "})
        self.assertFalse(empty["ok"])
        done = self.envelope("/ipc/contribution-verify", "POST", {
            "contribution_id": cid, "evidence": "Adopted in the minutes (synthetic)."})
        self.assertEqual(done["data"]["item"]["status"], "verified")
        base = {"title": "T", "kind": "teaching", "my_part": "Taught.", "shared_credit": "Council"}
        for command, body in (("contribution-add", {**base, "kind": "award"}),
                              ("contribution-add", {**base, "occurred_on": "x"}),
                              ("contribution-add", {**base, "project_id": "nope"}),
                              ("contribution-add", {"title": "T", "kind": "teaching"}),
                              ("contribution-verify", {"contribution_id": "nope",
                                                       "evidence": "e"}),
                              ("contribution-verify", {"contribution_id": cid})):
            with self.subTest(command=command, body=body):
                self.assertEqual(self.request(f"/ipc/{command}", "POST", body)[0], 400)
        view = self.envelope("/ipc/contributions?today=2026-09-30")["data"]
        self.assertIn(cid, [i["id"] for i in view["items"]])

    def test_sources_from_the_screens(self):
        lib = self.envelope("/ipc/library?today=2026-09-30")["data"]
        self.assertEqual(len(lib["items"]), 3)
        added = self.envelope("/ipc/source-add", "POST", {
            "title": "Huddle evaluation questions", "kind": "synthetic",
            "reference": "synthetic://huddle-evaluation", "data_class": "D0",
            "project_id": lib["projects"][0]["id"], "review_date": "2027-01-31"})["data"]
        self.assertEqual(added["source"]["project_id"], lib["projects"][0]["id"])
        for body in ({"title": "T", "kind": "internal", "reference": "r"},
                     {"title": "T", "kind": "public", "reference": "r", "data_class": "D2"},
                     {"title": "T", "kind": "public", "reference": "r", "review_date": "soon"},
                     {"title": "T", "kind": "public", "reference": "r", "project_id": "nope"}):
            with self.subTest(body=body):
                self.assertEqual(self.request("/ipc/source-add", "POST", body)[0], 400)
        refused = self.envelope("/ipc/source-add", "POST", {
            "title": "Email jane.doe@example.org", "kind": "public", "reference": "r"})
        self.assertEqual(refused["error"]["type"], "CaptureRefused")
        self.assertEqual(len(self.envelope("/ipc/library")["data"]["items"]), 4)

    def test_feedback_from_the_screens(self):
        mission = self.envelope("/ipc/mission")["data"]
        project_id = mission["projects_in_motion"]["items"][0]["id"]
        added = self.envelope("/ipc/feedback-add", "POST", {
            "project_id": project_id, "from_group": "Evening huddle", "kind": "question",
            "summary": "Can Dates cover two weeks?", "received_on": "2026-09-27"})["data"]
        feedback_id = added["feedback"]["id"]
        refused = self.envelope("/ipc/feedback-add", "POST", {
            "project_id": project_id, "from_group": "jane.doe@example.org", "kind": "worked",
            "summary": "Good", "received_on": "2026-09-27"})
        self.assertEqual(refused["error"]["type"], "CaptureRefused")
        for body in ({"project_id": project_id, "from_group": "G", "kind": "praise",
                      "summary": "Good"},
                     {"project_id": "nope", "from_group": "G", "kind": "worked", "summary": "S"}):
            with self.subTest(body=body):
                self.assertEqual(self.request("/ipc/feedback-add", "POST", body)[0], 400)
        empty = self.envelope("/ipc/feedback-address", "POST",
                              {"feedback_id": feedback_id, "response": "  "})
        self.assertFalse(empty["ok"])
        done = self.envelope("/ipc/feedback-address", "POST",
                             {"feedback_id": feedback_id, "response": "Yes, two weeks."})["data"]
        self.assertEqual(done["feedback"]["status"], "addressed")
        dashboard = self.envelope(f"/ipc/project?id={project_id}")["data"]
        self.assertIn(feedback_id, [f["id"] for f in dashboard["feedback"]])

    def test_write_bodies_are_checked(self):
        for command, body in (("accept", {"revision": "x", "sha256": "y"}),
                              ("accept", {"revision": "rev-000000000000"}),
                              ("brief", {"week": "last week"}),
                              ("assistant-local", {"model": 3}),
                              ("assistant-brief", {}),
                              ("assistant-brief", {"prompt_sha256": "abc"})):
            with self.subTest(command=command, body=body):
                self.assertEqual(self.request(f"/ipc/{command}", "POST", body)[0], 400)

    def test_ai_from_the_screens_is_bound_to_the_reviewed_preview(self):
        from test_assistant import FakeModelServer, echo_rewrite

        server = FakeModelServer(echo_rewrite)
        self.addCleanup(server.close)
        preview = self.envelope("/ipc/assistant-preview?week=2026-09-28&today=2026-09-30")["data"]
        self.assertFalse(preview["will_send"])
        refused = self.envelope("/ipc/assistant-local", "POST",
                                {"model": "llama3.2", "endpoint": "http://example.com:11434"})
        self.assertFalse(refused["ok"])
        status = self.envelope("/ipc/assistant-local", "POST",
                               {"model": "llama3.2", "endpoint": server.endpoint})["data"]
        self.assertEqual(status["provider"], "local")
        preview = self.envelope("/ipc/assistant-preview?week=2026-09-28&today=2026-09-30")["data"]
        self.assertTrue(preview["will_send"])
        stale = self.envelope("/ipc/assistant-brief", "POST", {**self.body, "prompt_sha256": ""})
        self.assertFalse(stale["ok"])
        self.assertIn("review it again", stale["error"]["message"])
        self.assertEqual(server.requests, [])
        drafted = self.envelope("/ipc/assistant-brief", "POST",
                                {**self.body, "prompt_sha256": preview["prompt_sha256"]})["data"]
        self.assertEqual(drafted["outcome"], "drafted")
        self.assertEqual(server.requests[0]["body"]["prompt"], preview["prompt"])
        self.assertEqual(server.requests[0]["body"]["system"], preview["system"])
        project_id = self.envelope("/ipc/mission")["data"]["projects_in_motion"]["items"][0]["id"]
        question = "What should I do first?"
        from urllib.parse import quote
        asked = self.envelope(f"/ipc/assistant-project-preview?id={project_id}"
                              f"&today=2026-09-30&question={quote(question)}")["data"]
        self.assertTrue(asked["will_send"])
        self.assertIn(question, asked["prompt"])
        answer = self.envelope("/ipc/assistant-project", "POST", {
            "id": project_id, "question": question, "today": "2026-09-30",
            "prompt_sha256": asked["prompt_sha256"]})["data"]
        self.assertEqual(answer["outcome"], "answered")
        self.assertEqual(server.requests[-1]["body"]["prompt"], asked["prompt"])
        self.assertEqual(self.request("/ipc/assistant-project", "POST",
                                      {"id": "nope", "question": question, "prompt_sha256": ""})[0], 400)
        # Keeping the answer as a note: only the exact answer, and as the owner.
        keep = {"request_id": answer["request_id"], "project_id": project_id,
                "question": answer["question"], "answer": answer["answer"]}
        edited = self.envelope("/ipc/note-keep", "POST", {**keep, "answer": "Edited."})
        self.assertFalse(edited["ok"])
        note = self.envelope("/ipc/note-keep", "POST", {**keep, "kept_by": "Someone Else"})["data"]
        self.assertEqual(note["kept_by"], "Sample Manager")
        dashboard = self.envelope(f"/ipc/project?id={project_id}")["data"]
        self.assertEqual([n["id"] for n in dashboard["notes"]], [note["id"]])
        self.assertEqual(self.request("/ipc/note-keep", "POST", {**keep, "request_id": "x"})[0], 400)
        self.assertEqual(self.envelope("/ipc/assistant-off", "POST", {})["data"]["provider"], "none")


class LifetimeTests(unittest.TestCase):
    def test_the_app_stops_by_itself_when_no_page_is_in_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = local_app.LocalApp(Path(tmp), idle_timeout=1)
            thread = threading.Thread(target=app.serve, daemon=True)
            started = time.monotonic()
            thread.start()
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertLess(time.monotonic() - started, 8)

    def test_self_test_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(local_app.self_test(Path(tmp)), 0)

    def test_self_test_passes_without_a_console(self):
        # A windowed Windows build has no stdout; the exit code still reports.
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sys, "stdout", None):
            self.assertEqual(local_app.self_test(Path(tmp)), 0)


class SingleInstanceTests(unittest.TestCase):
    def test_a_second_instance_cannot_take_the_same_data_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = local_app.LocalApp(Path(tmp), idle_timeout=60)
            thread = threading.Thread(target=first.serve, daemon=True)
            thread.start()
            self.assertTrue(first.ready.wait(10))
            with self.assertRaises(local_app.AlreadyRunning):
                local_app.LocalApp(Path(tmp), idle_timeout=60)
            first.stop()
            thread.join(timeout=10)
            # Released on stop (and by the OS on a crash): the next launch works.
            again = local_app.LocalApp(Path(tmp), idle_timeout=60)
            again.instance.release()
            again.server.server_close()

    def test_two_launches_at_once_leave_exactly_one_instance(self):
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "PYTHONPATH": str(Path(local_app.__file__).resolve().parents[1])}
            args = [sys.executable, "-m", "nurse_manager.app", "--no-browser", "--print-url",
                    "--idle-timeout", "60", "--home", tmp]
            launches = [subprocess.Popen(args, stdout=subprocess.PIPE, text=True, env=env)
                        for _ in range(2)]
            try:
                urls = [p.stdout.readline().strip() for p in launches]
                self.assertEqual(urls[0], urls[1], "both launches lead to the same instance")
                time.sleep(1.0)
                running = [p for p in launches if p.poll() is None]
                self.assertEqual(len(running), 1, "exactly one instance keeps running")
                exited = [p for p in launches if p.poll() is not None]
                self.assertEqual(exited[0].returncode, 0)
                port, token = urls[0].split(":")[2].split("/")[0], urls[0].split("token=")[1]
                conn = http.client.HTTPConnection("127.0.0.1", int(port), timeout=10)
                conn.request("POST", "/app/quit", body="{}", headers={
                    "Host": f"127.0.0.1:{port}", "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"})
                self.assertEqual(conn.getresponse().status, 200)
                conn.close()
                self.assertEqual(running[0].wait(timeout=10), 0)
            finally:
                for p in launches:
                    if p.poll() is None:
                        p.kill()
                    p.stdout.close()

    def test_user_data_lives_outside_the_app_and_can_be_redirected(self):
        previous = os.environ.get("NURSE_AI_OS_HOME")
        try:
            os.environ["NURSE_AI_OS_HOME"] = "/tmp/elsewhere"
            self.assertEqual(resources.user_data_dir(), Path("/tmp/elsewhere"))
            del os.environ["NURSE_AI_OS_HOME"]
            self.assertNotIn(str(resources.manager_root()), str(resources.user_data_dir()))
            self.assertIn("nurse", str(resources.user_data_dir()).lower())
        finally:
            if previous is None:
                os.environ.pop("NURSE_AI_OS_HOME", None)
            else:
                os.environ["NURSE_AI_OS_HOME"] = previous


if __name__ == "__main__":
    unittest.main()


class RecurringBriefAppTests(_AppCase):
    """The running app prepares the recurring draft itself (5.1); the page only sets it."""

    schedule_interval = 0.2

    def setUp(self):
        super().setUp()
        self.assertTrue(self.envelope("/ipc/sample", "POST", {})["ok"])
        self.week = (date.today() - timedelta(days=date.today().weekday())).isoformat()

    def weekly(self):
        return self.envelope(f"/ipc/weekly?week={self.week}")["data"]

    def test_the_app_drafts_the_week_once_after_it_is_turned_on(self):
        self.assertEqual(self.weekly()["schedule"]["enabled"], False)
        time.sleep(0.5)  # several scheduler ticks while off: nothing happens
        self.assertIsNone(self.weekly()["schedule"]["last_run"])
        view = self.envelope("/ipc/brief-schedule-set", "POST",
                             {"enabled": True, "weekday": 0, "hour": 0})["data"]
        self.assertEqual((view["enabled"], view["weekday"], view["hour"]), (True, 0, 0))
        deadline = time.monotonic() + 10
        while self.weekly()["schedule"]["last_run"] is None and time.monotonic() < deadline:
            time.sleep(0.1)
        weekly = self.weekly()
        run = weekly["schedule"]["last_run"]
        self.assertEqual((run["week_of"], run["status"]), (self.week, "drafted"))
        self.assertEqual(weekly["current"]["revision"]["id"], run["revision_id"])
        self.assertEqual(weekly["current"]["revision"]["status"], "draft")
        time.sleep(0.6)  # more ticks: still one draft
        workspace = ManagerWorkspace(self.home / "workspace")
        try:
            count = workspace.store.conn.execute(
                "SELECT count(*) FROM artifact_revisions r JOIN artifacts a"
                " ON a.id = r.artifact_id WHERE a.week_of = ?", (self.week,)).fetchone()[0]
        finally:
            workspace.close()
        self.assertEqual(count, 1)

    def test_settings_are_checked_and_running_it_is_not_a_page_command(self):
        for body in ({"enabled": "yes", "weekday": 0, "hour": 7},
                     {"enabled": True, "weekday": 7, "hour": 7},
                     {"enabled": True, "weekday": 0, "hour": 24},
                     {"enabled": True, "weekday": "0", "hour": 7},
                     {"enabled": True, "weekday": True, "hour": 7},
                     {"enabled": True}):
            with self.subTest(body=body):
                self.assertEqual(self.request("/ipc/brief-schedule-set", "POST", body)[0], 400)
        self.assertNotEqual(self.request("/ipc/brief-run-due", "POST", {})[0], 200)
