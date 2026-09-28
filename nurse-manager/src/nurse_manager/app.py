"""The local app: double-click, and the manager screens open in the browser (ADR 0003).

What happens at launch:

1. If Nurse AI OS is already running for this user, the launcher reopens
   the browser at it and exits. There is only ever one instance.
2. Otherwise it starts the manager core on 127.0.0.1 with a fresh random
   token, and opens the default browser at ``http://127.0.0.1:<port>/#token=…``.
   The fragment is never sent to any server or put in a referrer. The page
   moves the token into session storage and clears it from the address bar.
3. Every data call must carry ``Authorization: Bearer <token>``. Static
   screen files need no token, because they hold no records.
4. The page sends a heartbeat while it is open. With no contact for the
   idle timeout, the app stops by itself; the manager can also press Quit.

Records live in the manager's user-data folder (``resources.user_data_dir``),
never inside the application bundle.

    nurse-ai-os [--no-browser] [--port 0] [--idle-timeout 900] [--self-test]
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__, cli, resources
from .devhost import (
    READ_ONLY_COMMANDS,
    _PROJECT_ID,
    _valid_date,
    monday_of,
    send,
    serve_static,
)

DEFAULT_IDLE_TIMEOUT = 15 * 60
MAX_BODY = 16 * 1024
LOCK_NAME = "app.lock.json"


def _launch_token() -> str:
    """A fresh random secret for this launch only. It is never stored in the repo."""
    return secrets.token_urlsafe(32)


class LocalApp:
    """One running instance: its token, workspace, and lifetime."""

    def __init__(self, home: Path, *, port: int = 0, idle_timeout: float = DEFAULT_IDLE_TIMEOUT):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.workspace = self.home / "workspace"
        self.token = _launch_token()
        self.idle_timeout = idle_timeout
        self.last_seen = time.monotonic()
        self.stopping = threading.Event()
        self.ready = threading.Event()  # set once the lock file names this instance
        self.server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())
        self.port = self.server.server_address[1]

    # -- lifetime ---------------------------------------------------------

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/#token={self.token}"

    @property
    def lock_path(self) -> Path:
        return self.home / LOCK_NAME

    def has_workspace(self) -> bool:
        return (self.workspace / "workspace.sqlite").is_file() and self._workspace_ready()

    def _workspace_ready(self) -> bool:
        code, envelope = cli.run(["board", str(self.workspace)])
        return envelope.get("ok", False)

    def touch(self) -> None:
        self.last_seen = time.monotonic()

    def write_lock(self) -> None:
        data = json.dumps({"pid": os.getpid(), "port": self.port, "token": self.token})
        # The token grants access to the manager's records: owner-only file.
        fd = os.open(self.lock_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)

    def remove_lock(self) -> None:
        try:
            current = json.loads(self.lock_path.read_text(encoding="utf-8"))
            if current.get("token") == self.token:
                self.lock_path.unlink()
        except (OSError, ValueError):
            pass

    def serve(self) -> None:
        self.write_lock()
        self.ready.set()
        watchdog = threading.Thread(target=self._watch_idle, daemon=True)
        watchdog.start()
        try:
            self.server.serve_forever(poll_interval=0.25)
        finally:
            self.server.server_close()
            self.remove_lock()

    def stop(self) -> None:
        if not self.stopping.is_set():
            self.stopping.set()
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _watch_idle(self) -> None:
        while not self.stopping.wait(1.0):
            if time.monotonic() - self.last_seen > self.idle_timeout:
                self.stop()

    # -- HTTP -------------------------------------------------------------

    def _handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "nurse-ai-os"
            sys_version = ""

            def log_message(self, fmt, *args):
                pass

            def _json(self, status: int, payload: dict) -> None:
                send(self, status, json.dumps(payload, sort_keys=True).encode("utf-8"),
                     "application/json; charset=utf-8")

            def _text(self, status: int, message: str) -> None:
                send(self, status, message.encode("utf-8"), "text/plain; charset=utf-8")

            def _host_ok(self) -> bool:
                return self.headers.get("Host", "") in (
                    f"127.0.0.1:{app.port}", f"localhost:{app.port}")

            def _authorized(self) -> bool:
                header = self.headers.get("Authorization", "")
                scheme, _, presented = header.partition(" ")
                return scheme == "Bearer" and hmac.compare_digest(presented, app.token)

            def _origin_ok(self) -> bool:
                origin = self.headers.get("Origin")
                return origin is None or origin in (
                    f"http://127.0.0.1:{app.port}", f"http://localhost:{app.port}")

            def _gate(self) -> bool:
                if not self._host_ok():
                    self._text(421, "Misdirected request")
                    return False
                if not self._origin_ok():
                    self._text(403, "Cross-origin requests are refused")
                    return False
                if not self._authorized():
                    self._text(401, "This page is not connected to Nurse AI OS. Reopen the app.")
                    return False
                app.touch()
                return True

            def do_GET(self):  # noqa: N802
                url = urlparse(self.path)
                if not (url.path.startswith("/ipc/") or url.path.startswith("/app/")):
                    if not self._host_ok():
                        return self._text(421, "Misdirected request")
                    return serve_static(self, url.path)
                if not self._gate():
                    return
                if url.path == "/app/status":
                    return self._json(200, {
                        "app": "nurse-ai-os",
                        "version": __version__,
                        "has_workspace": app.has_workspace(),
                        "idle_timeout_seconds": int(app.idle_timeout),
                    })
                if url.path.startswith("/ipc/"):
                    return self._read(url.path[len("/ipc/"):], parse_qs(url.query))
                return self._text(404, "Not found")

            do_HEAD = do_GET

            def do_POST(self):  # noqa: N802
                url = urlparse(self.path)
                if not self._gate():
                    return
                length = int(self.headers.get("Content-Length") or 0)
                if length > MAX_BODY:
                    return self._text(413, "Request too large")
                raw = self.rfile.read(length) if length else b"{}"
                if url.path == "/app/heartbeat":
                    return self._json(200, {"ok": True})
                if url.path == "/app/quit":
                    self._json(200, {"ok": True, "message": "Nurse AI OS has stopped."})
                    app.stop()
                    return None
                if url.path in ("/ipc/sample", "/ipc/init"):
                    if (self.headers.get("Content-Type") or "").split(";")[0] != "application/json":
                        return self._text(415, "Send JSON")
                    try:
                        body = json.loads(raw.decode("utf-8") or "{}")
                    except (UnicodeDecodeError, ValueError):
                        return self._text(400, "Malformed JSON")
                    if not isinstance(body, dict):
                        return self._text(400, "Send a JSON object")
                    return self._onboard(url.path[len("/ipc/"):], body)
                return self._text(404, "Unknown or unavailable command")

            def _read(self, command: str, query: dict[str, list[str]]) -> None:
                if command not in READ_ONLY_COMMANDS:
                    return self._text(404, "Unknown or unavailable command")
                argv = [command, str(app.workspace)]
                day = (query.get("today") or [date.today().isoformat()])[0]
                if command in ("mission", "project") and not _valid_date(day):
                    return self._text(400, "today must be a YYYY-MM-DD date")
                if command == "mission":
                    week = (query.get("week") or [monday_of(date.fromisoformat(day)).isoformat()])[0]
                    if not _valid_date(week):
                        return self._text(400, "week must be a YYYY-MM-DD date")
                    argv += ["--today", day, "--week", week]
                if command == "project":
                    project_id = (query.get("id") or [""])[0]
                    if not _PROJECT_ID.match(project_id):
                        return self._text(400, "id must be a project record id")
                    argv += ["--id", project_id, "--today", day]
                _code, envelope = cli.run(argv)
                return self._json(200, envelope)

            def _onboard(self, command: str, body: dict) -> None:
                # Onboarding creates the workspace once; it never replaces one.
                if app.has_workspace():
                    return self._json(200, {
                        "contract": cli.CONTRACT, "command": command, "ok": False,
                        "error": {"type": "ManagerError",
                                  "message": "This computer already has a workspace."},
                    })
                if command == "sample":
                    _code, envelope = cli.run(["sample", str(app.workspace)])
                    return self._json(200, envelope)
                name, owner = body.get("name"), body.get("owner")
                if not isinstance(name, str) or not isinstance(owner, str):
                    return self._text(400, "name and owner are required text fields")
                _code, envelope = cli.run(
                    ["init", str(app.workspace), "--name", name[:200], "--owner", owner[:200]])
                # A refused capture leaves at most an empty database; retrying works.
                return self._json(200, envelope)

        return Handler


def _running_instance(home: Path) -> str | None:
    """Return the URL of a live instance for this user, if one answers."""
    lock = Path(home) / LOCK_NAME
    try:
        data = json.loads(lock.read_text(encoding="utf-8"))
        port, token = int(data["port"]), str(data["token"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/app/status", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310 — loopback only
            if json.loads(response.read()).get("app") == "nurse-ai-os":
                return f"http://127.0.0.1:{port}/#token={token}"
    except (OSError, ValueError, urllib.error.URLError):
        pass
    return None


def self_test(home: Path) -> int:
    """Start, onboard the sample, read every view, quit. Used by CI on packaged builds."""
    app = LocalApp(home, idle_timeout=60)
    thread = threading.Thread(target=app.serve, daemon=True)
    thread.start()
    app.ready.wait(10)
    base = f"http://127.0.0.1:{app.port}"

    def call(path: str, method: str = "GET", body: dict | None = None, token: str | None = app.token):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    checks = []
    status, _ = call("/app/status", token=None)
    checks.append(("data calls need the token", status == 401))
    status, page = call("/")
    checks.append(("screens are served", status == 200 and b"Nurse AI OS" in page))
    status, raw = call("/ipc/sample", "POST", {})
    checks.append(("sample workspace created", status == 200 and json.loads(raw)["ok"]))
    for command in ("mission", "board", "table"):
        status, raw = call(f"/ipc/{command}")
        checks.append((f"{command} answers", status == 200 and json.loads(raw)["ok"]))
    status, _ = call("/app/quit", "POST", {})
    thread.join(timeout=10)
    checks.append(("quit stops the app", not thread.is_alive()))
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {label}")
    return 0 if all(passed for _, passed in checks) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nurse-ai-os")
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--idle-timeout", type=float, default=DEFAULT_IDLE_TIMEOUT,
                        help="seconds without an open page before the app stops")
    parser.add_argument("--home", type=Path, help="data folder (default: the user-data folder)")
    parser.add_argument("--print-url", action="store_true",
                        help="print the tokened URL on the first line (for test harnesses)")
    parser.add_argument("--self-test", action="store_true",
                        help="run a built-in end-to-end check in a temporary folder and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            return self_test(Path(tmp))

    home = args.home or resources.user_data_dir()
    existing = _running_instance(home)
    if existing:
        if args.print_url:
            print(existing, flush=True)
        if not args.no_browser:
            webbrowser.open(existing)
        return 0

    app = LocalApp(home, port=args.port, idle_timeout=args.idle_timeout)
    if args.print_url:
        print(app.url, flush=True)
    if not args.no_browser:
        threading.Timer(0.3, webbrowser.open, args=(app.url,)).start()
    try:
        app.serve()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
