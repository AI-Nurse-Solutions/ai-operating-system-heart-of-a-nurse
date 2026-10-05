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
from .http_transport import (
    READ_ONLY_COMMANDS,
    _PROJECT_ID,
    bind_values,
    _valid_date,
    monday_of,
    read_argv,
    send,
    serve_static,
)
from .packs import MAX_DOCUMENT_CHARS
from .pilot import AREAS as PILOT_AREAS, KINDS as PILOT_KINDS
from .services import ManagerWorkspace

DEFAULT_IDLE_TIMEOUT = 15 * 60
# How often the running app asks whether the recurring brief is due (step 5.1).
SCHEDULE_INTERVAL = 60.0
MAX_BODY = 256 * 1024  # room for a pack document (50,000 characters) as JSON
LOCK_NAME = "app.lock.json"

# The only writes the screens can ask for once a workspace exists. Each one
# acts as the workspace's owner: the app runs for one person on their own
# computer, and the launch token proves the request came from its page.
WRITE_COMMANDS = ("brief", "accept", "assistant-local", "assistant-off", "assistant-brief",
                  "assistant-project", "note-keep", "feedback-add", "feedback-address",
                  "source-add", "learning-add", "learning-start", "learning-complete",
                  "contribution-add", "contribution-verify", "brief-schedule-set",
                  "memory-add", "memory-correct", "memory-exclude", "memory-include",
                  "memory-delete", "assistants-stop", "assistants-resume", "pack-start",
                  "document-save", "pilot-feedback-add", "pilot-feedback-delete",
                  "pilot-feedback-export", "classifier-connect", "classifier-off",
                  "classifier-jobs", "classifier-route", "classifier-order")
WRITE_COMMANDS += ("project-add", "task-add", "decision-add", "priorities-set", "task-move",
                   "task-block", "task-pause", "task-complete", "task-reopen", "task-withdraw")
_TASK_ID = re.compile(r"^tsk-[0-9a-f]{12}$")
_REVISION_ID = re.compile(r"^rev-[0-9a-f]{12}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID = re.compile(r"^air-[0-9a-f]{12}$")
_FEEDBACK_ID = re.compile(r"^fbk-[0-9a-f]{12}$")
_LEARNING_ID = re.compile(r"^lrn-[0-9a-f]{12}$")
_MEMORY_ID = re.compile(r"^mem-[0-9a-f]{12}$")
_CONTRIBUTION_ID = re.compile(r"^ctb-[0-9a-f]{12}$")
_DOCUMENT_ID = re.compile(r"^art-[0-9a-f]{12}$")
_PILOT_ID = re.compile(r"^plf-[0-9a-f]{12}$")
_PACK_PART = re.compile(r"^[a-z][a-z0-9-]{1,59}$")
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

    def __init__(self, home: Path, *, port: int = 0, idle_timeout: float = DEFAULT_IDLE_TIMEOUT,
                 schedule_interval: float = SCHEDULE_INTERVAL):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        # Taken before anything else, so a second launch changes nothing.
        self.instance = InstanceLock(self.home)
        self.workspace = self.home / "workspace"
        self.token = _launch_token()
        self.idle_timeout = idle_timeout
        self.schedule_interval = schedule_interval
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
        threading.Thread(target=self._run_schedule, daemon=True).start()
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

    def _run_schedule(self) -> None:
        """The recurring weekly brief runs only while this app runs ("when this
        device is awake"): once at start, so a time slept through is caught up,
        then every interval. It is not activity, so it never keeps the app open."""
        while True:
            if (self.workspace / "workspace.sqlite").is_file():
                try:
                    cli.run(["brief-run-due", str(self.workspace)])
                except Exception:  # noqa: BLE001 - a failure is recorded; try again later
                    pass
            if self.stopping.wait(self.schedule_interval):
                return

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
                _code, envelope = cli.run(bind_values(argv))
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
                # A JEV key travels only in the request body and is handed to
                # the command in process: never an argument, never logged.
                secret = body.get("api_key") if command == "classifier-connect" else None
                if command == "classifier-connect" and not isinstance(secret, str):
                    return self._text(400, "api_key is required text")
                _code, envelope = cli.run(bind_values(argv), secret=secret)
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
    if command in ("project-add", "task-add", "decision-add", "priorities-set",
                   "task-move", "task-block", "task-pause", "task-complete", "task-reopen", "task-withdraw"):
        # Reject oversize capture inputs instead of silently truncating them.
        def field(key, limit, *, default=None):
            value = body.get(key, default)
            return value if isinstance(value, str) and len(value) <= limit else None

        def project_link():
            value = field("project_id", 64, default="")
            return value if value is not None and (not value or _PROJECT_ID.fullmatch(value)) else None

        if command == "project-add":
            title, purpose = field("title", 200), field("purpose", 2000)
            role, milestone = field("owner_role", 80, default="me"), field("milestone", 1000, default="")
            if None in (title, purpose, role, milestone):
                return "title, purpose, owner_role and milestone must be bounded text"
            return [command, ws, "--title", title, "--purpose", purpose, "--owner", role, "--milestone", milestone]
        if command == "task-add":
            title, role = field("title", 200), field("owner_role", 80, default="me")
            reviewer, next_action = field("reviewer_role", 80, default=""), field("next_action", 2000, default="")
            link, due, status = project_link(), field("due_date", 10, default=""), body.get("status", "idea")
            if (None in (title, role, reviewer, next_action, link, due)
                    or status not in ("idea", "ready", "in_progress", "needs_judgment")
                    or (due and not _valid_date(due))):
                return "task fields, project id, due date and active status must be valid"
            return ([command, ws, "--title", title, "--owner", role, "--reviewer", reviewer,
                     "--next-action", next_action, "--status", status]
                    + (["--project", link] if link else []) + (["--due", due] if due else []))
        if command == "decision-add":
            question, decision = field("question", 2000), field("decision", 2000)
            role, on = field("decision_role", 80, default="me"), field("decided_on", 10)
            rationale, link = field("rationale", 4000, default=""), project_link()
            if None in (question, decision, role, on, rationale, link) or not _valid_date(on):
                return "decision fields, date and project id must be valid"
            return ([command, ws, "--question", question, "--decision", decision, "--by", role,
                     "--on", on, "--rationale", rationale] + (["--project", link] if link else []))
        if command == "priorities-set":
            digest = field("expected_sha256", 64)
            if body.get("replace_priorities") is not True or not digest or not _SHA256.fullmatch(digest):
                return "confirm replacement and supply the current priorities hash"
            argv = [command, ws, "--week", week, "--expected-sha", digest]
            count = 0
            for rank in (1, 2, 3):
                item = field(f"item_{rank}", 1000, default="")
                link = field(f"project_{rank}", 64, default="")
                if item is None or link is None or (link and not _PROJECT_ID.fullmatch(link)):
                    return "priorities must be bounded text with valid project ids"
                if item.strip():
                    argv += ["--item", item, "--project", link]
                    count += 1
                elif link:
                    return "a project link needs a priority"
            return argv if count else "name at least one priority"
        task_id, expected = field("id", 64), body.get("expected_status")
        if (not task_id or not _TASK_ID.fullmatch(task_id)
                or expected not in ("idea", "ready", "in_progress", "needs_judgment", "completed", "withdrawn")):
            return "task id and the reviewed status are required"
        argv = [command, ws, "--id", task_id, "--expected-status", expected]
        if command in ("task-move", "task-reopen"):
            target = body.get("status")
            if target not in ("idea", "ready", "in_progress", "needs_judgment"):
                return "choose an active target status"
            argv += ["--status", target]
        if command in ("task-reopen", "task-withdraw", "task-block"):
            reason = field("reason", 2000, default="")
            if reason is None:
                return "reason must be bounded text"
            argv += ["--reason", reason]
        if command == "task-complete":
            evidence = field("evidence", 2000)
            if evidence is None:
                return "completion evidence is required text"
            argv += ["--evidence", evidence]
        if command in ("task-block", "task-pause"):
            key = "blocked" if command == "task-block" else "paused"
            value = body.get(key)
            if type(value) is not bool:
                return f"{key} must be true or false"
            argv += [f"--{key}", "yes" if value else "no"]
        return argv
    if command == "brief":
        return ["brief", ws, "--week", week, "--today", today]
    if command == "accept":
        revision, sha = text("revision", 64), text("sha256", 64)
        if not revision or not _REVISION_ID.fullmatch(revision) or not sha or not _SHA256.fullmatch(sha):
            return "revision and sha256 are required"
        return ["accept", ws, "--revision", revision, "--reviewer", owner, "--sha", sha]
    if command == "assistant-local":
        model, endpoint = text("model", 100), text("endpoint", 200, required=False)
        if model is None or endpoint is None:
            return "model is required text; endpoint is optional text"
        argv = ["assistant-local", ws, "--model", model, "--by", owner]
        return argv + ["--endpoint", endpoint] if endpoint.strip() else argv
    if command in ("assistant-off", "assistants-stop", "assistants-resume"):
        return [command, ws, "--by", owner]
    if command == "pack-start":
        pack, template = text("pack", 60), text("template", 60)
        project_id = text("project_id", 64, required=False)
        if (not pack or not _PACK_PART.fullmatch(pack) or not template
                or not _PACK_PART.fullmatch(template) or project_id is None
                or (project_id and not _PROJECT_ID.fullmatch(project_id))):
            return "pack and template are required; project_id is optional"
        argv = ["pack-start", ws, "--pack", pack, "--template", template, "--today", today]
        return argv + (["--project", project_id] if project_id else [])
    if command == "document-save":
        document_id, base = text("document_id", 64), text("base_sha256", 64)
        content = text("body_markdown", MAX_DOCUMENT_CHARS + 1)
        if (not document_id or not _DOCUMENT_ID.fullmatch(document_id) or not base
                or not _SHA256.fullmatch(base) or content is None):
            return "document_id, body_markdown, and base_sha256 are required"
        return ["document-save", ws, "--id", document_id, "--body", content, "--base", base]
    if command in ("learning-add", "learning-start", "learning-complete"):
        hours = text("hours", 10, required=False)
        if hours is None or (hours and not _HOURS.fullmatch(hours)):
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
        if not learning_id or not _LEARNING_ID.fullmatch(learning_id):
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
    if command == "pilot-feedback-add":
        area, kind, summary = text("area", 40), text("kind", 20), text("summary", 2000)
        if area not in PILOT_AREAS or kind not in PILOT_KINDS or summary is None:
            return "area, kind, and summary are required"
        return ["pilot-feedback-add", ws, "--area", area, "--kind", kind, "--summary", summary]
    if command == "pilot-feedback-delete":
        feedback_id = text("feedback_id", 64)
        if not feedback_id or not _PILOT_ID.fullmatch(feedback_id):
            return "feedback_id is required"
        return ["pilot-feedback-delete", ws, "--id", feedback_id]
    if command == "pilot-feedback-export":
        # Bound to the preview the manager reviewed, like every AI request.
        sha = text("sha256", 64)
        if not sha or not _SHA256.fullmatch(sha):
            return "sha256 from the preview is required"
        return ["pilot-feedback-export", ws, "--reviewed-sha", sha, "--by", owner]
    if command == "memory-add":
        content, project_id = text("content", 1000), text("project_id", 64, required=False)
        expires = text("expires_on", 20, required=False)
        if (content is None or project_id is None
                or (project_id and not _PROJECT_ID.fullmatch(project_id))
                or expires is None or (expires and not _valid_date(expires))):
            return "content is required; project_id and expires_on (YYYY-MM-DD) are optional"
        argv = ["memory-add", ws, "--content", content, "--today", today]
        argv += ["--project", project_id] if project_id else []
        return argv + (["--expires", expires] if expires else [])
    if command in ("memory-correct", "memory-exclude", "memory-include", "memory-delete"):
        memory_id = text("memory_id", 64)
        if not memory_id or not _MEMORY_ID.fullmatch(memory_id):
            return "memory_id is required"
        argv = [command, ws, "--id", memory_id]
        if command == "memory-correct":
            content = text("content", 1000)
            if content is None:
                return "content is required"
            argv += ["--content", content]
        return argv if command == "memory-delete" else argv + ["--today", today]
    if command == "brief-schedule-set":
        enabled, weekday, hour = body.get("enabled"), body.get("weekday"), body.get("hour")
        if (not isinstance(enabled, bool) or type(weekday) is not int or not 0 <= weekday <= 6
                or type(hour) is not int or not 0 <= hour <= 23):
            return "enabled is true or false; weekday is 0 (Monday) to 6; hour is 0 to 23"
        return ["brief-schedule-set", ws, "--enabled", "yes" if enabled else "no",
                "--weekday", str(weekday), "--hour", str(hour), "--by", owner]
    if command == "contribution-add":
        title, kind = text("title", 400), text("kind", 40)
        my_part, shared = text("my_part", 2000), text("shared_credit", 400)
        project_id = text("project_id", 64, required=False)
        occurred = body.get("occurred_on", today)
        if (title is None or my_part is None or shared is None
                or kind not in ("improvement", "teaching", "committee", "presentation",
                                "publication")
                or project_id is None or (project_id and not _PROJECT_ID.fullmatch(project_id))
                or not isinstance(occurred, str) or not _valid_date(occurred)):
            return ("title, kind, my_part, shared_credit, and an occurred_on date are required;"
                    " project_id is optional")
        argv = ["contribution-add", ws, "--title", title, "--kind", kind, "--occurred", occurred,
                "--my-part", my_part, "--shared-credit", shared]
        return argv + (["--project", project_id] if project_id else [])
    if command == "contribution-verify":
        contribution_id, evidence = text("contribution_id", 64), text("evidence", 2000)
        if not contribution_id or not _CONTRIBUTION_ID.fullmatch(contribution_id) or evidence is None:
            return "contribution_id and evidence are required"
        return ["contribution-verify", ws, "--id", contribution_id, "--evidence", evidence]
    if command == "source-add":
        title, kind, reference = text("title", 400), text("kind", 40), text("reference", 1000)
        data_class, project_id = text("data_class", 4, required=False), text("project_id", 64, required=False)
        review = text("review_date", 20, required=False)
        if (title is None or reference is None or kind not in ("public", "synthetic", "personal_permitted")
                or data_class not in ("", "D0", "D1") or project_id is None
                or (project_id and not _PROJECT_ID.fullmatch(project_id)) or review is None
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
        if (not project_id or not _PROJECT_ID.fullmatch(project_id) or from_group is None
                or kind not in ("worked", "change", "question") or summary is None
                or not isinstance(received, str)
                or not _valid_date(received)):
            return "project_id, from_group, kind, summary, and a received_on date are required"
        return ["feedback-add", ws, "--project", project_id, "--from", from_group,
                "--kind", kind, "--summary", summary, "--received", received]
    if command == "feedback-address":
        feedback_id, response = text("feedback_id", 64), text("response", 2000)
        if not feedback_id or not _FEEDBACK_ID.fullmatch(feedback_id) or response is None:
            return "feedback_id and response are required"
        return ["feedback-address", ws, "--id", feedback_id, "--response", response]
    if command == "note-keep":
        request_id, project_id = text("request_id", 64), text("project_id", 64)
        question, answer = text("question", 2000), text("answer", 40000)
        if (not request_id or not _REQUEST_ID.fullmatch(request_id) or not project_id
                or not _PROJECT_ID.fullmatch(project_id) or question is None or answer is None):
            return "request_id, project_id, question, and answer are required"
        return ["note-keep", ws, "--request", request_id, "--project", project_id,
                "--question", question, "--answer", answer, "--by", owner]
    if command == "classifier-connect":
        limit = body.get("daily_request_limit")
        if limit is not None and (type(limit) is not int or not 0 <= limit <= 2000):
            return "daily_request_limit is a whole number from 0 to 2000"
        argv = ["classifier-connect", ws, "--by", owner, "--key-from", "stdin"]
        return argv + (["--daily-limit", str(limit)] if limit is not None else [])
    if command == "classifier-off":
        return ["classifier-off", ws, "--by", owner]
    if command == "classifier-jobs":
        argv = ["classifier-jobs", ws, "--by", owner]
        for job in ("action_review", "refusal_check", "routing", "attention"):
            value = body.get(job)
            if value is None:
                continue
            if not isinstance(value, bool):
                return f"{job} is true or false"
            argv += [f"--{job.replace('_', '-')}", "yes" if value else "no"]
        return argv
    if command in ("classifier-route", "classifier-order"):
        # Bound to the preview the manager reviewed, like every AI request.
        reviewed = text("request_sha256", 64)
        if not reviewed or not _SHA256.fullmatch(reviewed):
            return "request_sha256 from the preview is required"
        if command == "classifier-order":
            return ["classifier-order", ws, "--today", today, "--week", week, "--by", owner,
                    "--reviewed-sha", reviewed]
        request = text("request", 2000)
        if request is None:
            return "request is required text"
        return ["classifier-route", ws, "--request", request, "--by", owner,
                "--reviewed-sha", reviewed]
    # AI requests are always bound to the preview the manager reviewed.
    sha = text("prompt_sha256", 64)
    if sha is None or not (sha == "" or _SHA256.fullmatch(sha)):
        return "prompt_sha256 from the preview is required"
    if command == "assistant-project":
        project_id, question = text("id", 64), text("question", 2000)
        if not project_id or not _PROJECT_ID.fullmatch(project_id) or question is None:
            return "id and question are required"
        argv = ["assistant-project", ws, "--id", project_id, "--today", today,
                "--question", question, "--by", owner, "--reviewed-sha", sha]
        # JEV's refusal check, when on, is bound to its own reviewed preview.
        checked = text("classifier_sha256", 64, required=False)
        if checked is None or (checked and not _SHA256.fullmatch(checked)):
            return "classifier_sha256 is the sha256 from the preview, if JEV checks the question"
        return argv + (["--reviewed-classifier-sha", checked] if checked else [])
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
    for command in ("mission", "board", "table", "capture"):
        status, raw = call(f"/ipc/{command}")
        checks.append((f"{command} answers", status == 200 and json.loads(raw)["ok"]))
    for asset in ("capture.mjs", "people-rules.mjs"):
        status, raw = call(f"/{asset}")
        checks.append((f"{asset} is bundled", status == 200 and bool(raw)))
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
