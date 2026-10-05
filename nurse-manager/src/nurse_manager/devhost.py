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
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import cli

# Re-export the existing helper names for development-tool callers.
from .http_transport import (
    READ_ONLY_COMMANDS, RENDERER, SECURITY_HEADERS,
    _PROJECT_ID, _DOCUMENT_ID, _valid_date,
    bind_values, monday_of, read_argv, send, serve_static,
)


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
            _code, envelope = cli.run(bind_values(argv))
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
