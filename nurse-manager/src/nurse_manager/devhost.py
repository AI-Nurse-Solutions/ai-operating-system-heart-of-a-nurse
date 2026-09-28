"""Local development host for the manager screens (build step 3.5).

Stands in for the Hermes desktop host until G1: it serves the renderer and
answers read-only IPC calls over HTTP on the loopback interface, returning
exactly the envelopes the CLI prints. It is a development tool, not the
product's transport, and it is deliberately narrow:

* Binds 127.0.0.1 only; there is no option to listen elsewhere.
* Rejects any request whose Host header is not this loopback origin, which
  closes DNS-rebinding access from web pages.
* Answers only the read-only commands ``mission``, ``project``, ``board``, and
  ``table``.
  Anything that writes (brief, accept, export, approve, run, restore) is not
  reachable from a browser here.
* Sends a Content-Security-Policy that allows only same-origin scripts and
  styles, no inline code, and no framing.

    python3 -m nurse_manager.devhost WORKSPACE [--port 0] [--today YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import cli, resources

RENDERER = resources.manager_root() / "renderer"
READ_ONLY_COMMANDS = ("mission", "project", "board", "table", "weekly", "assistant",
                      "assistant-preview", "assistant-project-preview")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PROJECT_ID = re.compile(r"^prj-[0-9a-f]{12}$")

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self';"
        " img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def read_argv(command: str, workspace: Path, query: dict[str, list[str]],
              default_today: str) -> list[str] | str:
    """The CLI arguments for one read-only command, or a message saying what is wrong.

    Shared by the dev host and the local app. ``today`` defaults to the
    host's date and ``week`` to that week's Monday.
    """
    argv = [command, str(workspace)]
    day = (query.get("today") or [default_today])[0]
    if not _valid_date(day):
        return "today must be a YYYY-MM-DD date"
    week = (query.get("week") or [monday_of(date.fromisoformat(day)).isoformat()])[0]
    if not _valid_date(week):
        return "week must be a YYYY-MM-DD date"
    if command in ("mission", "assistant-preview"):
        argv += ["--today", day, "--week", week]
    elif command == "weekly":
        argv += ["--week", week]
    elif command in ("project", "assistant-project-preview"):
        project_id = (query.get("id") or [""])[0]
        if not _PROJECT_ID.match(project_id):
            return "id must be a project record id"
        argv += ["--id", project_id, "--today", day]
        if command == "assistant-project-preview":
            question = (query.get("question") or [""])[0]
            if len(question) > 2000:
                return "question is too long"
            argv += ["--question", question]
    return argv


def _valid_date(value: str) -> bool:
    if not _DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def send(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str,
         extra_headers: dict[str, str] | None = None) -> None:
    """Every response from a local host carries the same security headers."""
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    for name, value in {**SECURITY_HEADERS, **(extra_headers or {})}.items():
        handler.send_header(name, value)
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(body)


_CONTENT_TYPES = {
    ".mjs": "text/javascript; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def serve_static(handler: BaseHTTPRequestHandler, path: str) -> None:
    """Serve a renderer file. Paths cannot leave the renderer directory."""
    if path in ("", "/"):
        path = "/index.html"
    base = RENDERER.resolve()
    target = (base / path.lstrip("/")).resolve()
    if base not in target.parents or not target.is_file():
        return send(handler, 404, b"Not found", "text/plain; charset=utf-8")
    content_type = _CONTENT_TYPES.get(
        target.suffix, mimetypes.guess_type(target.name)[0] or "application/octet-stream")
    send(handler, 200, target.read_bytes(), content_type)


def make_handler(workspace: Path, today: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "nurse-manager-devhost"
        sys_version = ""

        def log_message(self, fmt, *args):  # quiet by default; no request bodies exist
            pass

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            send(self, status, body, content_type)

        def _text(self, status: int, message: str) -> None:
            self._send(status, message.encode("utf-8"), "text/plain; charset=utf-8")

        def _host_ok(self) -> bool:
            port = self.server.server_address[1]
            return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def do_GET(self):  # noqa: N802 — http.server naming
            if not self._host_ok():
                return self._text(421, "Misdirected request")
            url = urlparse(self.path)
            if url.path == "/app/status":
                # Says plainly what this is, so the screens stay read-only here.
                body = json.dumps({"app": "nurse-manager-devhost", "read_only": True}).encode("utf-8")
                return self._send(200, body, "application/json; charset=utf-8")
            if url.path.startswith("/ipc/"):
                return self._ipc(url.path[len("/ipc/"):], parse_qs(url.query))
            return self._static(url.path)

        do_HEAD = do_GET

        def do_POST(self):  # noqa: N802
            self._text(405, "This host is read-only")

        do_PUT = do_DELETE = do_PATCH = do_POST

        def _ipc(self, command: str, query: dict[str, list[str]]) -> None:
            if command not in READ_ONLY_COMMANDS:
                return self._text(404, "Unknown or non-read-only command")
            argv = read_argv(command, workspace, query, today or date.today().isoformat())
            if isinstance(argv, str):
                return self._text(400, argv)
            _code, envelope = cli.run(argv)
            body = json.dumps(envelope, sort_keys=True).encode("utf-8")
            # The envelope carries success or failure; HTTP only says it was delivered.
            self._send(200, body, "application/json; charset=utf-8")

        def _static(self, path: str) -> None:
            serve_static(self, path)

    return Handler


def serve(workspace: Path, port: int = 0, today: str | None = None) -> ThreadingHTTPServer:
    if today is not None and not _valid_date(today):
        raise ValueError("--today must be a YYYY-MM-DD date")
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Path(workspace), today))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nurse-manager-devhost")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--today", help="pin 'today' (YYYY-MM-DD), e.g. for the sample week")
    args = parser.parse_args(argv)
    server = serve(args.workspace, args.port, args.today)
    host, port = server.server_address[:2]
    # First line is machine-readable so test harnesses can find the port.
    print(f"http://{host}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
