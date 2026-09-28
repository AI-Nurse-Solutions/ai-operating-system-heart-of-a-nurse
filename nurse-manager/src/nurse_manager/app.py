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
import re
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
    read_argv,
    send,
    serve_static,
)
from .services import ManagerWorkspace

DEFAULT_IDLE_TIMEOUT = 15 * 60
MAX_BODY = 64 * 1024  # room for an AI answer being kept as a note
LOCK_NAME = "app.lock.json"

# The only writes the screens can ask for once a workspace exists. Each one
# acts as the workspace's owner: the app runs for one person on their own
# computer, and the launch token proves the request came from its page.
WRITE_COMMANDS = ("brief", "accept", "assistant-local", "assistant-off", "assistant-brief",
                  "assistant-project", "note-keep", "feedback-add", "feedback-address",
                  "source-add", "learning-add", "learning-start", "learning-complete",
                  "contribution-add", "contribution-verify")
_REVISION_ID = re.compile(r"^rev-[0-9a-f]{12}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID = re.compile(r"^air-[0-9a-f]{12}$")
_FEEDBACK_ID = re.compile(r"^fbk-[0-9a-f]{12}$")
_LEARNING_ID = re.compile(r"^lrn-[0-9a-f]{12}$")
_CONTRIBUTION_ID = re.compile(r"^ctb-[0-9a-f]{12}$")
_HOURS = re.compile(r"^\d{1,3}(\.\d{1,2})?$")


INSTANCE_NAME = "app.instance"


class AlreadyRunning(RuntimeError):
    """Another Nurse AI OS instance already holds this user's data folder."""


class InstanceLock:
    """One instance per data folder, enforced by the operating system.

    The lock is an exclusive, non-blocking lock on a file, not the file's
    existence: taking it is atomic, so two launches that start together
    cannot both win, and the operating system releases it if the app
    crashes, so a stale lock never blocks the next launch.
    """

    def __init__(self, home: Path):
        self.path = Path(home) / INSTANCE_NAME
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            if os.name == "nt":  # pragma: no cover - exercised on the Windows build
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise AlreadyRunning("Nurse AI OS is already running for this user") from exc
        self.fd: int | None = fd

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)  # closing the descriptor releases the lock
            self.fd = None


def _say(text: str) -> None:
    """Print if there is somewhere to print. A windowed build has no console."""
    stream = sys.stdout
    if stream is None:
        return
    try:
        stream.write(text + "\n")
        stream.flush()
    except (OSError, ValueError):
        pass


def _launch_token() -> str:
    """A fresh random secret for this launch only. It is never stored in the repo."""
    return secrets.token_urlsafe(32)


class LocalApp:
    """One running instance: its token, workspace, and lifetime."""

    def __init__(self, home: Path, *, port: int = 0, idle_timeout: float = DEFAULT_IDLE_TIMEOUT):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        # Taken before anything else, so a second launch changes nothing.
        self.instance = InstanceLock(self.home)
        self.workspace = self.home / "workspace"
        self.token = _launch_token()
        self.idle_timeout = idle_timeout
        self.last_seen = time.monotonic()
        self.stopping = threading.Event()
        self.ready = threading.Event()  # set once the lock file names this instance
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", port), self._handler())
        except OSError:
            self.instance.release()
            raise
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

    def owner(self) -> str:
        """The workspace's accountable manager: the person this app runs for."""
        ws = ManagerWorkspace(self.workspace)
        try:
            return ws.info.owner
        finally:
            ws.close()

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
            self.instance.release()

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
                command = url.path[len("/ipc/"):] if url.path.startswith("/ipc/") else ""
                if command not in ("sample", "init", *WRITE_COMMANDS):
                    return self._text(404, "Unknown or unavailable command")
                if (self.headers.get("Content-Type") or "").split(";")[0] != "application/json":
                    return self._text(415, "Send JSON")
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, ValueError):
                    return self._text(400, "Malformed JSON")
                if not isinstance(body, dict):
                    return self._text(400, "Send a JSON object")
                if command in ("sample", "init"):
                    return self._onboard(command, body)
                return self._write(command, body)

            def _read(self, command: str, query: dict[str, list[str]]) -> None:
                if command not in READ_ONLY_COMMANDS:
                    return self._text(404, "Unknown or unavailable command")
                argv = read_argv(command, app.workspace, query, date.today().isoformat())
                if isinstance(argv, str):
                    return self._text(400, argv)
                _code, envelope = cli.run(argv)
                return self._json(200, envelope)

            def _write(self, command: str, body: dict) -> None:
                if not app.has_workspace():
                    return self._json(200, {
                        "contract": cli.CONTRACT, "command": command, "ok": False,
                        "error": {"type": "ManagerError",
                                  "message": "Create or open a workspace first."},
                    })
                argv = _write_argv(command, body, app.workspace, app.owner())
                if isinstance(argv, str):
                    return self._text(400, argv)
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


def _write_argv(command: str, body: dict, workspace: Path, owner: str) -> list[str] | str:
    """The CLI arguments for one write, or a message saying what is wrong."""

    def text(key: str, limit: int, *, required: bool = True) -> str | None:
        value = body.get(key, None if required else "")
        return value[:limit] if isinstance(value, str) else None

    today = body.get("today", date.today().isoformat())
    if not isinstance(today, str) or not _valid_date(today):
        return "today must be a YYYY-MM-DD date"
    week = body.get("week", monday_of(date.fromisoformat(today)).isoformat())
    if not isinstance(week, str) or not _valid_date(week):
        return "week must be a YYYY-MM-DD date"
    ws = str(workspace)
    if command == "brief":
        return ["brief", ws, "--week", week, "--today", today]
    if command == "accept":
        revision, sha = text("revision", 64), text("sha256", 64)
        if not revision or not _REVISION_ID.match(revision) or not sha or not _SHA256.match(sha):
            return "revision and sha256 are required"
        return ["accept", ws, "--revision", revision, "--reviewer", owner, "--sha", sha]
    if command == "assistant-local":
        model, endpoint = text("model", 100), text("endpoint", 200, required=False)
        if model is None or endpoint is None:
            return "model is required text; endpoint is optional text"
        argv = ["assistant-local", ws, "--model", model, "--by", owner]
        return argv + ["--endpoint", endpoint] if endpoint.strip() else argv
    if command == "assistant-off":
        return ["assistant-off", ws, "--by", owner]
    if command in ("learning-add", "learning-start", "learning-complete"):
        hours = text("hours", 10, required=False)
        if hours is None or (hours and not _HOURS.match(hours)):
            return "hours must be a number, like 1.5"
        if command == "learning-add":
            title, kind = text("title", 400), text("kind", 40)
            target = text("target_date", 20, required=False)
            if (title is None or kind not in ("course", "reading", "conference", "certification",
                                               "mentoring")
                    or target is None or (target and not _valid_date(target))):
                return "title and kind are required; target_date is YYYY-MM-DD"
            argv = ["learning-add", ws, "--title", title, "--kind", kind]
            argv += ["--target", target] if target else []
            return argv + (["--hours", hours] if hours else [])
        learning_id = text("learning_id", 64)
        if not learning_id or not _LEARNING_ID.match(learning_id):
            return "learning_id is required"
        if command == "learning-start":
            return ["learning-start", ws, "--id", learning_id]
        takeaway = text("takeaway", 2000)
        completed = body.get("completed_on", today)
        if takeaway is None or not isinstance(completed, str) or not _valid_date(completed):
            return "takeaway and a completed_on date are required"
        argv = ["learning-complete", ws, "--id", learning_id, "--takeaway", takeaway,
                "--completed", completed]
        return argv + (["--hours", hours] if hours else [])
    if command == "contribution-add":
        title, kind = text("title", 400), text("kind", 40)
        my_part, shared = text("my_part", 2000), text("shared_credit", 400)
        project_id = text("project_id", 64, required=False)
        occurred = body.get("occurred_on", today)
        if (title is None or my_part is None or shared is None
                or kind not in ("improvement", "teaching", "committee", "presentation",
                                "publication")
                or project_id is None or (project_id and not _PROJECT_ID.match(project_id))
                or not isinstance(occurred, str) or not _valid_date(occurred)):
            return ("title, kind, my_part, shared_credit, and an occurred_on date are required;"
                    " project_id is optional")
        argv = ["contribution-add", ws, "--title", title, "--kind", kind, "--occurred", occurred,
                "--my-part", my_part, "--shared-credit", shared]
        return argv + (["--project", project_id] if project_id else [])
    if command == "contribution-verify":
        contribution_id, evidence = text("contribution_id", 64), text("evidence", 2000)
        if not contribution_id or not _CONTRIBUTION_ID.match(contribution_id) or evidence is None:
            return "contribution_id and evidence are required"
        return ["contribution-verify", ws, "--id", contribution_id, "--evidence", evidence]
    if command == "source-add":
        title, kind, reference = text("title", 400), text("kind", 40), text("reference", 1000)
        data_class, project_id = text("data_class", 4, required=False), text("project_id", 64, required=False)
        review = text("review_date", 20, required=False)
        if (title is None or reference is None or kind not in ("public", "synthetic", "personal_permitted")
                or data_class not in ("", "D0", "D1") or project_id is None
                or (project_id and not _PROJECT_ID.match(project_id)) or review is None
                or (review and not _valid_date(review))):
            return "title, kind, and reference are required; data_class is D0 or D1"
        argv = ["source-add", ws, "--title", title, "--kind", kind, "--reference", reference,
                "--data-class", data_class or "D0"]
        if project_id:
            argv += ["--project", project_id]
        return argv + (["--review", review] if review else [])
    if command == "feedback-add":
        project_id, from_group = text("project_id", 64), text("from_group", 200)
        kind, summary = text("kind", 20), text("summary", 2000)
        received = body.get("received_on", today)
        if (not project_id or not _PROJECT_ID.match(project_id) or from_group is None
                or kind not in ("worked", "change", "question") or summary is None
                or not isinstance(received, str)
                or not _valid_date(received)):
            return "project_id, from_group, kind, summary, and a received_on date are required"
        return ["feedback-add", ws, "--project", project_id, "--from", from_group,
                "--kind", kind, "--summary", summary, "--received", received]
    if command == "feedback-address":
        feedback_id, response = text("feedback_id", 64), text("response", 2000)
        if not feedback_id or not _FEEDBACK_ID.match(feedback_id) or response is None:
            return "feedback_id and response are required"
        return ["feedback-address", ws, "--id", feedback_id, "--response", response]
    if command == "note-keep":
        request_id, project_id = text("request_id", 64), text("project_id", 64)
        question, answer = text("question", 2000), text("answer", 40000)
        if (not request_id or not _REQUEST_ID.match(request_id) or not project_id
                or not _PROJECT_ID.match(project_id) or question is None or answer is None):
            return "request_id, project_id, question, and answer are required"
        return ["note-keep", ws, "--request", request_id, "--project", project_id,
                "--question", question, "--answer", answer, "--by", owner]
    # AI requests are always bound to the preview the manager reviewed.
    sha = text("prompt_sha256", 64)
    if sha is None or not (sha == "" or _SHA256.match(sha)):
        return "prompt_sha256 from the preview is required"
    if command == "assistant-project":
        project_id, question = text("id", 64), text("question", 2000)
        if not project_id or not _PROJECT_ID.match(project_id) or question is None:
            return "id and question are required"
        return ["assistant-project", ws, "--id", project_id, "--today", today,
                "--question", question, "--by", owner, "--reviewed-sha", sha]
    return ["assistant-brief", ws, "--week", week, "--today", today, "--by", owner,
            "--reviewed-sha", sha]


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
        _say(f"{'PASS' if passed else 'FAIL'} {label}")
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
    try:
        app = LocalApp(home, port=args.port, idle_timeout=args.idle_timeout)
    except AlreadyRunning:
        # The running instance may still be starting: give it a moment to answer.
        existing = None
        for _ in range(20):
            existing = _running_instance(home)
            if existing:
                break
            time.sleep(0.25)
        if existing is None:
            _say("Nurse AI OS is already running for this user but is not answering yet."
                 " Try again in a moment.")
            return 1
        if args.print_url:
            _say(existing)
        if not args.no_browser:
            webbrowser.open(existing)
        return 0

    if args.print_url:
        _say(app.url)
    if not args.no_browser:
        threading.Timer(0.3, webbrowser.open, args=(app.url,)).start()
    try:
        app.serve()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
