# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0

"""Shared HTTP transport primitives for the local app and development host.

This module translates validated reads and serves renderer assets. It does
not open workspaces, execute commands, bind sockets, or authorize requests.
Each host enforces its own authentication, origin, and method boundaries.
"""

from __future__ import annotations

import mimetypes
import re
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from . import resources

RENDERER = resources.manager_root() / "renderer"
READ_ONLY_COMMANDS = ("mission", "capture", "project", "board", "table", "weekly", "assistant",
                      "assistant-preview", "assistant-project-preview", "library",
                      "learning", "contributions", "memory", "packs", "document",
                      "pilot-feedback", "pilot-feedback-preview", "classifier",
                      "classifier-route-preview", "classifier-order-preview")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PROJECT_ID = re.compile(r"^prj-[0-9a-f]{12}$")
_DOCUMENT_ID = re.compile(r"^art-[0-9a-f]{12}$")

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


def bind_values(argv: list[str]) -> list[str]:
    """Join every option to its value (``--body=text``), so text a person typed
    is never read as another option, however it begins ("--todo", "-h")."""
    bound, rest = argv[:2], iter(argv[2:])
    for option in rest:
        bound.append(f"{option}={next(rest)}")
    return bound


def read_argv(command: str, workspace: Path, query: dict[str, list[str]],
              default_today: str) -> list[str] | str:
    """The CLI arguments for one read-only command, or a message saying what is wrong.

    Shared by the dev host and the local app. ``today`` defaults to the
    host's date and ``week`` to that week's Monday.
    """
    if command not in READ_ONLY_COMMANDS:
        return "Unknown or non-read-only command"
    argv = [command, str(workspace)]
    day = (query.get("today") or [default_today])[0]
    if not _valid_date(day):
        return "today must be a YYYY-MM-DD date"
    week = (query.get("week") or [monday_of(date.fromisoformat(day)).isoformat()])[0]
    if not _valid_date(week):
        return "week must be a YYYY-MM-DD date"
    if command in ("library", "learning", "contributions", "memory", "packs"):
        argv += ["--today", day]
    elif command == "document":
        document_id = (query.get("id") or [""])[0]
        if not _DOCUMENT_ID.fullmatch(document_id):
            return "id must be a document record id"
        argv += ["--id", document_id]
    elif command == "classifier-route-preview":
        request = (query.get("request") or [""])[0]
        if len(request) > 2000:
            return "request is too long"
        argv += ["--request", request]
    elif command in ("mission", "capture", "assistant-preview", "classifier-order-preview"):
        argv += ["--today", day, "--week", week]
    elif command == "weekly":
        argv += ["--week", week]
    elif command in ("project", "assistant-project-preview"):
        project_id = (query.get("id") or [""])[0]
        if not _PROJECT_ID.fullmatch(project_id):
            return "id must be a project record id"
        argv += ["--id", project_id, "--today", day]
        if command == "assistant-project-preview":
            question = (query.get("question") or [""])[0]
            if len(question) > 2000:
                return "question is too long"
            argv += ["--question", question]
    return argv


def _valid_date(value: str) -> bool:
    if not _DATE.fullmatch(value):
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
