#!/usr/bin/env python3
"""Drive every CLI command once and capture its IPC envelope.

Used by the contract tests (Python and Node) so that what is validated
is what the real command surface prints, not a hand-written sample.

    python3 nurse-manager/tools/ipc_fixtures.py OUTDIR   # writes OUTDIR/<name>.json
"""

from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nurse_manager import cli  # noqa: E402

OWNER = "Sample Manager"
WEEK, TODAY = "2026-09-28", "2026-09-30"


def _run(*argv) -> tuple[int, dict]:
    return cli.run([str(a) for a in argv])


@contextmanager
def _stand_in_model():
    """A stand-in local model server that rewrites the brief faithfully."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            payload = json.dumps({"response": body["prompt"], "done": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def _closed_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def collect(workdir: Path) -> dict[str, dict]:
    """Return {fixture name: envelope}, covering every command at least once."""
    ws, empty = workdir / "ws", workdir / "empty"
    out: dict[str, dict] = {}

    def keep(name: str, *argv) -> dict:
        code, envelope = _run(*argv)
        if (code == 0) != envelope.get("ok"):
            raise RuntimeError(f"{name}: exit code {code} disagrees with envelope")
        out[name] = envelope
        return envelope.get("data", {})

    keep("sample", "sample", ws)
    keep("init", "init", empty, "--name", "Empty workspace", "--owner", "Test Manager")
    mission = keep("mission", "mission", ws, "--today", TODAY, "--week", WEEK)
    for item in mission["projects_in_motion"]["items"]:
        keep(f"project-{item['id']}", "project", ws, "--id", item["id"], "--today", TODAY)
    keep("error-project-unknown", "project", ws, "--id", "prj-000000000000", "--today", TODAY)
    keep("mission-empty", "mission", empty, "--today", TODAY, "--week", WEEK)
    huddle = next(i["id"] for i in mission["projects_in_motion"]["items"]
                  if i["title"].startswith("Huddle"))
    added = keep("feedback-add", "feedback-add", ws, "--project", huddle, "--from",
                 "Evening huddle (synthetic)", "--kind", "question", "--summary",
                 "Can the Dates slot include next week too?", "--received", "2026-09-27")
    keep("feedback-address", "feedback-address", ws, "--id", added["feedback"]["id"],
         "--response", "Yes: Dates now covers two weeks.")
    keep("error-feedback-address-again", "feedback-address", ws, "--id",
         added["feedback"]["id"], "--response", " ")
    keep("learning", "learning", ws, "--today", TODAY)
    keep("learning-empty", "learning", empty, "--today", TODAY)
    planned = keep("learning-add", "learning-add", ws, "--title",
                   "Budget basics for new managers (synthetic)", "--kind", "course",
                   "--target", "2026-11-30", "--hours", "4")
    keep("learning-start", "learning-start", ws, "--id", planned["item"]["id"])
    keep("error-learning-complete-no-takeaway", "learning-complete", ws, "--id",
         planned["item"]["id"], "--takeaway", " ", "--completed", "2026-09-27")
    keep("learning-complete", "learning-complete", ws, "--id", planned["item"]["id"],
         "--takeaway", "Read the variance report before the meeting, not during it.",
         "--completed", "2026-09-27")
    keep("library", "library", ws, "--today", TODAY)
    keep("source-add", "source-add", ws, "--title", "Huddle evaluation questions (synthetic)",
         "--kind", "synthetic", "--reference", "synthetic://samples/huddle-evaluation",
         "--project", huddle, "--review", "2027-01-31")
    keep("error-source-add-d2", "source-add", ws, "--title", "Staffing grid", "--kind",
         "public", "--reference", "internal://grid", "--review", "someday")
    keep("library-empty", "library", empty, "--today", TODAY)
    keep("board", "board", ws)
    keep("table", "table", ws)
    keep("weekly-empty", "weekly", ws, "--week", WEEK)
    draft = keep("brief", "brief", ws, "--week", WEEK, "--today", TODAY)
    keep("weekly-draft", "weekly", ws, "--week", WEEK)
    keep("show-draft", "show", ws, "--revision", draft["id"])
    keep("accept", "accept", ws, "--revision", draft["id"], "--reviewer", OWNER,
         "--sha", draft["sha256"])
    keep("show-accepted", "show", ws, "--revision", draft["id"])
    keep("mission-after-accept", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("export-denied", "export", ws, "--revision", draft["id"], "--file", "../escape.md",
         "--by", OWNER)
    action = keep("export", "export", ws, "--revision", draft["id"], "--file", "week.md",
                  "--by", OWNER)
    keep("mission-awaiting-approval", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("approve", "approve", ws, "--action", action["id"], "--approver", OWNER,
         "--sha", action["payload_sha256"], "--destination", "week.md")
    keep("run", "run", ws, "--action", action["id"], "--actor", OWNER)
    keep("backup", "backup", ws, workdir / "backup.sqlite")
    keep("restore", "restore", ws, workdir / "backup.sqlite")
    keep("error-accept", "accept", ws, "--revision", draft["id"], "--reviewer", "Someone Else",
         "--sha", draft["sha256"])
    keep("error-restore-missing", "restore", ws, workdir / "missing.sqlite")

    # Bounded assistance (ADR 0004): no model by default, then a local model.
    keep("assistant", "assistant", ws)
    keep("assistant-preview-no-model", "assistant-preview", ws, "--week", WEEK, "--today", TODAY)
    first_project = mission["projects_in_motion"]["items"][0]["id"]
    keep("assistant-project-no-model", "assistant-project", ws, "--id", first_project,
         "--today", TODAY, "--question", "What is blocking this?", "--by", OWNER)
    keep("assistant-brief-no-model", "assistant-brief", ws, "--week", WEEK, "--today", TODAY,
         "--by", OWNER)
    keep("error-assistant-not-owner", "assistant-local", ws, "--model", "llama3.2",
         "--by", "Someone Else")
    keep("assistant-local-offline", "assistant-local", ws, "--model", "llama3.2", "--by", OWNER,
         "--endpoint", f"http://127.0.0.1:{_closed_port()}")
    keep("assistant-brief-unavailable", "assistant-brief", ws, "--week", WEEK, "--today", TODAY,
         "--by", OWNER)
    with _stand_in_model() as endpoint:
        keep("assistant-local", "assistant-local", ws, "--model", "llama3.2", "--by", OWNER,
             "--endpoint", endpoint)
        preview = keep("assistant-preview", "assistant-preview", ws, "--week", WEEK,
                       "--today", TODAY)
        keep("error-assistant-brief-stale-preview", "assistant-brief", ws, "--week", WEEK,
             "--today", TODAY, "--by", OWNER, "--reviewed-sha", "0" * 64)
        keep("assistant-brief-drafted", "assistant-brief", ws, "--week", WEEK, "--today", TODAY,
             "--by", OWNER, "--reviewed-sha", preview["prompt_sha256"])
        keep("weekly-ai-draft", "weekly", ws, "--week", WEEK)
        project_id = mission["projects_in_motion"]["items"][0]["id"]
        question = "What should I do first?"
        asked = keep("assistant-project-preview", "assistant-project-preview", ws,
                     "--id", project_id, "--today", TODAY, "--question", question)
        answer = keep("assistant-project", "assistant-project", ws, "--id", project_id,
                      "--today", TODAY, "--question", question, "--by", OWNER,
                      "--reviewed-sha", asked["prompt_sha256"])
        keep("error-note-keep-edited", "note-keep", ws, "--request", answer["request_id"],
             "--project", project_id, "--question", question,
             "--answer", answer["answer"] + "\nAn added line.", "--by", OWNER)
        keep("note-keep", "note-keep", ws, "--request", answer["request_id"],
             "--project", project_id, "--question", answer["question"],
             "--answer", answer["answer"], "--by", OWNER)
        keep(f"project-with-note-{project_id}", "project", ws, "--id", project_id,
             "--today", TODAY)
    keep("error-assistant-project-empty-question", "assistant-project-preview", ws,
         "--id", project_id, "--today", TODAY, "--question", "  ")
    keep("mission-assistant-connected", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("assistant-off", "assistant-off", ws, "--by", OWNER)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(argv[0])
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, envelope in collect(Path(tmp)).items():
            (target / f"{name}.json").write_text(
                json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
