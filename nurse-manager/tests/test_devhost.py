"""Development host boundaries (build step 3.5).

The dev host must stay narrow: loopback only, same-origin Host only,
read-only commands only, no path escapes, strict security headers, and
envelopes byte-for-byte equal to what the core returns.
"""

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from nurse_manager import cli, devhost
from nurse_manager.sample import load_sample
from nurse_manager.services import ManagerWorkspace

TODAY = "2026-09-30"


class DevHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls._tmp.name) / "ws"
        ws, _ = load_sample(cls.workspace)
        ws.close()
        ws = ManagerWorkspace(cls.workspace)
        cls.project_id = ws.store.conn.execute("SELECT id FROM projects ORDER BY id").fetchone()[0]
        ws.close()
        cls.server = devhost.serve(cls.workspace, 0, TODAY)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    def request(self, path, method="GET", host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest(method, path, skip_host=True)
        conn.putheader("Host", host or f"127.0.0.1:{self.port}")
        conn.endheaders()
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response, body

    def test_binds_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_read_only_commands_return_the_cores_envelope(self):
        for command in devhost.READ_ONLY_COMMANDS:
            with self.subTest(command=command):
                query = f"?id={self.project_id}" if command == "project" else ""
                response, body = self.request(f"/ipc/{command}{query}")
                self.assertEqual(response.status, 200)
                argv = [command, str(self.workspace)]
                if command == "mission":
                    argv += ["--today", TODAY, "--week", "2026-09-28"]
                if command == "project":
                    argv += ["--id", self.project_id, "--today", TODAY]
                self.assertEqual(json.loads(body), cli.run(argv)[1])

    def test_nothing_that_writes_is_reachable(self):
        for command in ("brief", "accept", "export", "approve", "run", "backup", "restore",
                        "init", "sample", "show"):
            with self.subTest(command=command):
                self.assertEqual(self.request(f"/ipc/{command}")[0].status, 404)
        for method in ("POST", "PUT", "DELETE", "PATCH"):
            with self.subTest(method=method):
                self.assertEqual(self.request("/ipc/mission", method)[0].status, 405)

    def test_foreign_host_headers_are_refused(self):
        for host in ("evil.example", f"evil.example:{self.port}", f"127.0.0.1.nip.io:{self.port}", ""):
            with self.subTest(host=host):
                self.assertEqual(self.request("/ipc/mission", host=host or " ")[0].status, 421)
        self.assertEqual(self.request("/", host=f"localhost:{self.port}")[0].status, 200)

    def test_paths_cannot_escape_the_renderer(self):
        for path in ("/../src/nurse_manager/cli.py", "/%2e%2e/src/nurse_manager/cli.py",
                     "/..%2f..%2fREADME.md", "/renderer/../../README.md", "/workspace.sqlite"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0].status, 404)

    def test_security_headers_are_always_sent(self):
        for path in ("/", "/app.mjs", "/ipc/board", "/missing"):
            with self.subTest(path=path):
                response, _ = self.request(path)
                csp = response.getheader("Content-Security-Policy")
                self.assertIn("script-src 'self'", csp)
                self.assertIn("frame-ancestors 'none'", csp)
                self.assertNotIn("unsafe-inline", csp)
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")

    def test_dates_are_validated_before_reaching_the_core(self):
        for query in ("today=2026-13-45", "today=yesterday", "today=2026-09-30&week=bad"):
            with self.subTest(query=query):
                self.assertEqual(self.request(f"/ipc/mission?{query}")[0].status, 400)
        for query in ("", "id=", "id=tsk-000000000000", "id=prj-XYZ", "id=../../etc",
                      f"id={self.project_id}&today=bad"):
            with self.subTest(project_query=query):
                self.assertEqual(self.request(f"/ipc/project?{query}")[0].status, 400)
        unknown = json.loads(self.request("/ipc/project?id=prj-000000000000")[1])
        self.assertFalse(unknown["ok"])
        response, body = self.request("/ipc/mission?today=2026-10-07")
        self.assertEqual(json.loads(body)["data"]["week_of"], "2026-10-05")

    def test_status_says_this_host_is_read_only(self):
        response, body = self.request("/app/status")
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body), {"app": "nurse-manager-devhost", "read_only": True})

    def test_renderer_files_are_served_with_their_types(self):
        for path, kind in (("/", "text/html"), ("/app.mjs", "text/javascript"),
                           ("/tokens.css", "text/css"), ("/favicon.svg", "image/svg+xml")):
            with self.subTest(path=path):
                response, _ = self.request(path)
                self.assertEqual(response.status, 200)
                self.assertTrue(response.getheader("Content-Type").startswith(kind))


if __name__ == "__main__":
    unittest.main()
