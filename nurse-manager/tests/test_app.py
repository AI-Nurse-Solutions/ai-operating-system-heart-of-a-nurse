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
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager import app as local_app
from nurse_manager import resources


class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.app = local_app.LocalApp(self.home, idle_timeout=120)
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

    def test_only_onboarding_writes_are_reachable(self):
        for command in ("brief", "accept", "export", "approve", "run", "backup", "restore", "show"):
            with self.subTest(command=command):
                self.assertEqual(self.request(f"/ipc/{command}", "POST", {})[0], 404)
                self.assertEqual(self.request(f"/ipc/{command}")[0], 404)

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
