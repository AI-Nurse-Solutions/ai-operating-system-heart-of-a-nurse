#!/usr/bin/env python3
"""Drive every CLI command once and capture its IPC envelope.

Used by the contract tests (Python and Node) so that what is validated
is what the real command surface prints, not a hand-written sample.

    python3 nurse-manager/tools/ipc_fixtures.py OUTDIR   # writes OUTDIR/<name>.json
"""

from __future__ import annotations

import json
import socket
import sqlite3
import sys
import tempfile
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nurse_manager import classifier, cli, credentials, update  # noqa: E402

OWNER = "me"
# A throwaway key for the stand-in JEV server; never a real TypeSafe key.
JEV_TEST_KEY = "ts-test-key-0123456789abcdef"
WEEK, TODAY = "2026-09-28", "2026-09-30"


def _run(*argv, secret: str | None = None) -> tuple[int, dict]:
    return cli.run([str(a) for a in argv], secret=secret)


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


@contextmanager
def _stand_in_jev():
    """A stand-in JEV server: answers every question within the contract.

    It refuses a question that asks to rank people, holds every action it is
    asked about (deny, confidently), routes messages to the communication
    pack, and scores approvals as most urgent.
    """

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.headers.get("Authorization") != f"Bearer {JEV_TEST_KEY}":
                self.send_response(401)
                self.end_headers()
                return
            state = body["state"]
            text = json.dumps(state).lower()
            answers = {}
            for qid, q in body["questions"].items():
                if q["type"] == "noul":
                    yes = 0.95 if qid == "named_person_judgment" and "rank" in text else 0.02
                    answers[qid] = {"type": "noul", "noul": yes}
                elif q["type"] == "choice":
                    options = list(q["criteria"])
                    pick = ("deny" if "deny" in options else
                            "pack_communication" if "message" in text else options[0])
                    rest = (1 - 0.9) / (len(options) - 1)
                    answers[qid] = {"type": "choice", "choice": pick, "confidence": 0.9,
                                    "probabilities": {o: 0.9 if o == pick else rest
                                                      for o in options}}
                else:
                    n = int(qid.split("_")[1])
                    kind = state["items"][n - 1]["kind"]
                    level = 4 if "approve" in kind else 2
                    probs = {str(i): (0.85 if i == level else 0.05) for i in range(1, 5)}
                    answers[qid] = {"type": "score", "score": level, "confidence": 0.8,
                                    "legend": {str(i): c for i, c in
                                               enumerate(q["criteria"], start=1)},
                                    "probabilities": probs}
            payload = json.dumps({"model": body["model"], "answers": answers,
                                  "usage": {"input_tokens": 64, "output_tokens": 0}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/v1/systemone"
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

    def keep(name: str, *argv, secret: str | None = None) -> dict:
        code, envelope = _run(*argv, secret=secret)
        if (code == 0) != envelope.get("ok"):
            raise RuntimeError(f"{name}: exit code {code} disagrees with envelope")
        out[name] = envelope
        return envelope.get("data", {})

    keep("sample", "sample", ws)
    keep("init", "init", empty, "--name", "Empty workspace", "--owner", "me")
    capture = workdir / "capture"
    keep("capture-init", "init", capture, "--name", "Synthetic capture", "--owner", "me")
    captured_project = keep("project-add", "project-add", capture, "--title", "Planning exercise",
                            "--purpose", "Practice clear follow-through", "--owner", "me")["id"]
    captured_task = keep("task-add", "task-add", capture, "--title", "Review the outline",
                        "--owner", "me", "--project", captured_project,
                        "--status", "ready", "--due", TODAY)["task"]["id"]
    keep("task-move", "task-move", capture, "--id", captured_task, "--expected-status", "ready",
         "--status", "in_progress")
    keep("task-block", "task-block", capture, "--id", captured_task,
         "--expected-status", "in_progress", "--blocked", "yes", "--reason", "Awaiting review")
    keep("task-pause", "task-pause", capture, "--id", captured_task,
         "--expected-status", "in_progress", "--paused", "yes")
    keep("task-complete", "task-complete", capture, "--id", captured_task,
         "--expected-status", "in_progress", "--evidence", "Outline reviewed")
    keep("task-reopen", "task-reopen", capture, "--id", captured_task,
         "--expected-status", "completed", "--reason", "A second review is needed")
    keep("task-withdraw", "task-withdraw", capture, "--id", captured_task,
         "--expected-status", "ready", "--reason", "The exercise ended")
    keep("decision-add", "decision-add", capture, "--question", "Which outline?",
         "--decision", "Use the reviewed outline", "--by", "me", "--on", TODAY,
         "--project", captured_project)
    keep("priorities-set", "priorities-set", capture, "--week", WEEK,
         "--item", "Review the outline", "--project", captured_project)
    keep("error-task-stale", "task-move", capture, "--id", captured_task,
         "--expected-status", "ready", "--status", "in_progress")
    keep("error-task-due", "task-add", capture, "--title", "Synthetic task",
         "--owner", "me", "--due", "2026-02-30")
    keep("error-decision-date", "decision-add", capture, "--question", "Which outline?",
         "--decision", "Use the reviewed outline", "--by", "me", "--on", "not-a-date")
    keep("capture", "capture", capture, "--today", TODAY, "--week", WEEK)
    mission = keep("mission", "mission", ws, "--today", TODAY, "--week", WEEK)
    for item in mission["projects_in_motion"]["items"]:
        keep(f"project-{item['id']}", "project", ws, "--id", item["id"], "--today", TODAY)
    keep("error-project-unknown", "project", ws, "--id", "prj-000000000000", "--today", TODAY)
    keep("mission-empty", "mission", empty, "--today", TODAY, "--week", WEEK)
    huddle = next(i["id"] for i in mission["projects_in_motion"]["items"]
                  if i["title"].startswith("Huddle"))
    added = keep("feedback-add", "feedback-add", ws, "--project", huddle, "--from",
                 "Team", "--kind", "question", "--summary",
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
    keep("memory", "memory", ws, "--today", TODAY)
    keep("memory-empty", "memory", empty, "--today", TODAY)
    kept = keep("memory-add", "memory-add", ws, "--content",
                "Council agendas go out two days ahead (synthetic).", "--project", huddle,
                "--expires", "2027-06-30", "--today", TODAY)["item"]["id"]
    keep("error-memory-add-identifier", "memory-add", ws, "--content",
         "Email the educator at educator@example.org", "--today", TODAY)
    keep("memory-correct", "memory-correct", ws, "--id", kept, "--content",
         "Council agendas go out three days ahead (synthetic).", "--today", TODAY)
    keep("memory-exclude", "memory-exclude", ws, "--id", kept, "--today", TODAY)
    keep("error-memory-exclude-again", "memory-exclude", ws, "--id", kept, "--today", TODAY)
    keep("memory-include", "memory-include", ws, "--id", kept, "--today", TODAY)
    keep("memory-delete", "memory-delete", ws, "--id", kept)
    keep("error-memory-delete-again", "memory-delete", ws, "--id", kept)
    keep("packs-empty", "packs", empty, "--today", TODAY)
    keep("error-pack-start-unknown-template", "pack-start", ws, "--pack", "committee",
         "--template", "education-plan", "--today", TODAY)
    keep("error-pack-start-due-for-review", "pack-start", ws, "--pack", "committee",
         "--template", "meeting-pack", "--today", "2027-04-01")
    keep("packs-due-for-review", "packs", ws, "--today", "2027-04-01")
    started = keep("pack-start", "pack-start", ws, "--pack", "committee", "--template",
                   "meeting-pack", "--project", huddle, "--today", TODAY)
    document_id = started["document"]["id"]
    keep("error-document-save-stale", "document-save", ws, "--id", document_id, "--body",
         "# Meeting pack\n\nAgenda: dates first.\n", "--base", "0" * 64)
    saved = keep("document-save", "document-save", ws, "--id", document_id, "--body",
                 started["current"]["body_markdown"].replace(
                     "_Write this section._", "Council members agree dates first.", 1),
                 "--base", started["current"]["revision"]["sha256"])
    keep("accept-pack-document", "accept", ws, "--revision", saved["current"]["revision"]["id"],
         "--reviewer", OWNER, "--sha", saved["current"]["revision"]["sha256"])
    keep("document", "document", ws, "--id", document_id)
    keep("error-document-unknown", "document", ws, "--id", "art-000000000000")
    keep("packs", "packs", ws, "--today", TODAY)
    keep("contributions", "contributions", ws, "--today", TODAY)
    keep("contributions-empty", "contributions", empty, "--today", TODAY)
    drafted = keep("contribution-add", "contribution-add", ws, "--title",
                   "Rewrote the council agenda template (synthetic)", "--kind", "committee",
                   "--occurred", "2026-09-21", "--my-part", "Drafted the template.",
                   "--shared-credit", "Unit Based Council members", "--project", huddle)
    keep("error-contribution-verify-no-evidence", "contribution-verify", ws, "--id",
         drafted["item"]["id"], "--evidence", " ")
    keep("contribution-verify", "contribution-verify", ws, "--id", drafted["item"]["id"],
         "--evidence", "Template adopted in the council minutes (synthetic).")
    # Pilot feedback (step 6.3): kept here, screened, exported only as reviewed.
    keep("pilot-feedback-empty", "pilot-feedback", empty)
    keep("pilot-feedback-preview-empty", "pilot-feedback-preview", empty)
    keep("error-pilot-feedback-export-nothing", "pilot-feedback-export", empty,
         "--reviewed-sha", "0" * 64, "--by", "me")
    noted = keep("pilot-feedback-add", "pilot-feedback-add", ws, "--area", "weekly_brief",
                 "--kind", "problem", "--summary",
                 "The Accept button was hard to find on a small screen.")["item"]["id"]
    keep("error-pilot-feedback-add-identifier", "pilot-feedback-add", ws, "--area", "other",
         "--kind", "question", "--summary", "Call the pilot desk at 555-010-4477?")
    keep("pilot-feedback", "pilot-feedback", ws)
    shown = keep("pilot-feedback-preview", "pilot-feedback-preview", ws)
    keep("error-pilot-feedback-export-stale", "pilot-feedback-export", ws, "--reviewed-sha",
         "0" * 64, "--by", OWNER)
    keep("error-pilot-feedback-export-not-owner", "pilot-feedback-export", ws, "--reviewed-sha",
         shown["sha256"], "--by", "Someone Else")
    keep("pilot-feedback-export", "pilot-feedback-export", ws, "--reviewed-sha",
         shown["sha256"], "--by", OWNER)
    keep("pilot-feedback-after-export", "pilot-feedback", ws)
    keep("pilot-feedback-delete", "pilot-feedback-delete", ws, "--id", noted)
    keep("error-pilot-feedback-delete-again", "pilot-feedback-delete", ws, "--id", noted)
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
    # A crash mid-export: the action is left executing and no file was written.
    # Reconcile settles it by checking the disk, and never runs it again.
    _, second = _run("export", ws, "--revision", draft["id"], "--file", "week-again.md",
                     "--by", OWNER)
    _run("approve", ws, "--action", second["data"]["id"], "--approver", OWNER, "--sha",
         second["data"]["payload_sha256"], "--destination", "week-again.md")
    with sqlite3.connect(ws / "workspace.sqlite") as db:
        db.execute("UPDATE actions SET status = 'executing' WHERE id = ?", (second["data"]["id"],))
    keep("reconcile", "reconcile", ws)
    keep("reconcile-nothing-interrupted", "reconcile", ws)
    keep("backup", "backup", ws, workdir / "backup.sqlite")
    keep("restore", "restore", ws, workdir / "backup.sqlite")
    keep("error-accept", "accept", ws, "--revision", draft["id"], "--reviewer", "Someone Else",
         "--sha", draft["sha256"])
    keep("error-restore-missing", "restore", ws, workdir / "missing.sqlite")
    # The update check (step 6.2), from signed test feeds and a throwaway key. The
    # command offers no way to choose its keys or state, so they are set here.
    feeds, state = SRC.parent / "tests" / "fixtures" / "update", workdir / "update-state.sqlite"
    with mock.patch.object(update, "state_path", return_value=state):
        keep("update-check-not-configured", "update-check")
        with mock.patch.object(update, "config_path", return_value=feeds / "config.json"):
            keep("update-check-available", "update-check", "--feed", feeds / "feed-seq5.json",
                 "--signature", feeds / "feed-seq5.json.sig")
            keep("update-check-current", "update-check", "--feed", feeds / "feed-current.json",
                 "--signature", feeds / "feed-current.json.sig")
            keep("error-update-check-replayed", "update-check", "--feed",
                 feeds / "feed-seq4.json", "--signature", feeds / "feed-seq4.json.sig")
            keep("error-update-check-no-signature", "update-check", "--feed",
                 feeds / "feed-seq5.json")

    _collect_classifier(workdir, keep)

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
        # Stopped assistants send nothing: the brief falls back to records, the
        # question is refused, and both say why.
        keep("error-assistants-stop-not-owner", "assistants-stop", ws, "--by", "Someone Else")
        keep("assistants-stop", "assistants-stop", ws, "--by", OWNER)
        keep("assistant-brief-stopped", "assistant-brief", ws, "--week", WEEK,
             "--today", TODAY, "--by", OWNER)
        keep("assistant-project-stopped", "assistant-project", ws, "--id", project_id,
             "--today", TODAY, "--question", question, "--by", OWNER)
        keep("assistants-resume", "assistants-resume", ws, "--by", OWNER)
        keep("error-assistants-resume-not-stopped", "assistants-resume", ws, "--by", OWNER)
    keep("error-assistant-project-empty-question", "assistant-project-preview", ws,
         "--id", project_id, "--today", TODAY, "--question", "  ")
    keep("mission-assistant-connected", "mission", ws, "--today", TODAY, "--week", WEEK)
    keep("assistant-off", "assistant-off", ws, "--by", OWNER)
    # The recurring brief runs on the real clock, so it gets a workspace of its
    # own: whatever the date, it cannot change the fixtures above.
    scheduled = workdir / "scheduled"
    keep("sample-scheduled", "sample", scheduled)
    keep("brief-run-due-off", "brief-run-due", scheduled)
    keep("error-brief-schedule-set-not-owner", "brief-schedule-set", scheduled, "--enabled",
         "yes", "--weekday", "0", "--hour", "0", "--by", "Someone Else")
    keep("brief-schedule-set", "brief-schedule-set", scheduled, "--enabled", "yes",
         "--weekday", "0", "--hour", "0", "--by", "me")
    keep("brief-run-due", "brief-run-due", scheduled)
    keep("brief-run-due-again", "brief-run-due", scheduled)
    keep("weekly-with-schedule", "weekly", scheduled, "--week", WEEK)
    keep("mission-with-schedule", "mission", scheduled, "--today", TODAY, "--week", WEEK)
    keep("assistants-stop-scheduled", "assistants-stop", scheduled, "--by", OWNER)
    keep("brief-run-due-stopped", "brief-run-due", scheduled)
    keep("mission-stopped", "mission", scheduled, "--today", TODAY, "--week", WEEK)
    keep("weekly-stopped", "weekly", scheduled, "--week", WEEK)
    return out



def _collect_classifier(workdir: Path, keep) -> None:
    """JEV as a classifier (ADR 0006), in a workspace of its own, against stand-ins."""
    ws = workdir / "jev"
    data = keep("sample-jev", "sample", ws)
    week, today = data["week_of"], data["today"]
    project_id = keep("mission-jev", "mission", ws, "--today", today, "--week", week)[
        "projects_in_motion"]["items"][0]["id"]
    request = "Draft a huddle message about the new hand hygiene audit"
    keys = credentials.MemoryKeyStore()
    with _stand_in_model() as model_endpoint, _stand_in_jev() as jev_endpoint, \
            mock.patch.object(classifier, "default_keystore", return_value=keys), \
            mock.patch.object(classifier, "JEV_ENDPOINT", jev_endpoint):
        keep("classifier", "classifier", ws)
        keep("classifier-route-preview-off", "classifier-route-preview", ws, "--request", request)
        keep("classifier-route-off", "classifier-route", ws, "--request", request, "--by", OWNER,
             "--reviewed-sha", "0" * 64)
        keep("error-classifier-jobs-not-connected", "classifier-jobs", ws, "--by", OWNER,
             "--routing", "yes")
        keep("error-classifier-connect-bad-key", "classifier-connect", ws, "--by", OWNER,
             "--key-from", "stdin", secret="not a key")
        keep("error-classifier-connect-not-owner", "classifier-connect", ws, "--by",
             "Someone Else", "--key-from", "stdin", secret=JEV_TEST_KEY)
        keep("classifier-connect", "classifier-connect", ws, "--by", OWNER, "--key-from",
             "stdin", secret=JEV_TEST_KEY)
        keep("classifier-jobs", "classifier-jobs", ws, "--by", OWNER, "--action-review", "yes",
             "--refusal-check", "yes", "--routing", "yes", "--attention", "yes")
        # Routing: a suggestion bound to the preview; the manager chooses.
        routed = keep("classifier-route-preview", "classifier-route-preview", ws,
                      "--request", request)
        keep("error-classifier-route-stale", "classifier-route", ws, "--request", request,
             "--by", OWNER, "--reviewed-sha", "0" * 64)
        keep("classifier-route", "classifier-route", ws, "--request", request, "--by", OWNER,
             "--reviewed-sha", routed["request_sha256"])
        # The refusal check runs only when the question would reach a model.
        keep("assistant-local-jev", "assistant-local", ws, "--model", "llama3.2", "--by", OWNER,
             "--endpoint", model_endpoint)
        for name, question in (("refused-intake", "Rank my staff from strongest to weakest"),
                               ("checked", "What should I do first?")):
            asked = keep(f"assistant-project-preview-{name}", "assistant-project-preview", ws,
                         "--id", project_id, "--today", today, "--question", question)
            keep(f"assistant-project-{name}", "assistant-project", ws, "--id", project_id,
                 "--today", today, "--question", question, "--by", OWNER, "--reviewed-sha",
                 asked["prompt_sha256"], "--reviewed-classifier-sha",
                 asked["classifier"]["request_sha256"])
        keep("error-assistant-project-classifier-unreviewed", "assistant-project", ws, "--id",
             project_id, "--today", today, "--question", "What should I do first?", "--by",
             OWNER)
        # Action review: a confident, stricter suggestion holds the approval.
        draft = keep("brief-jev", "brief", ws, "--week", week, "--today", today)
        keep("accept-jev", "accept", ws, "--revision", draft["id"], "--reviewer", OWNER,
             "--sha", draft["sha256"])
        action = keep("export-jev", "export", ws, "--revision", draft["id"], "--file",
                      "week.md", "--by", OWNER)
        ordered = keep("classifier-order-preview", "classifier-order-preview", ws,
                       "--today", today, "--week", week)
        keep("classifier-order", "classifier-order", ws, "--today", today, "--week", week,
             "--by", OWNER, "--reviewed-sha", ordered["request_sha256"])
        reviewed = keep("classifier-action-preview", "classifier-action-preview", ws,
                        "--action", action["id"])
        keep("classifier-action", "classifier-action", ws, "--action", action["id"], "--by",
             OWNER, "--reviewed-sha", reviewed["request_sha256"])
        keep("error-classifier-action-again", "classifier-action", ws, "--action", action["id"],
             "--by", OWNER, "--reviewed-sha", reviewed["request_sha256"])
        keep("error-approve-held-by-jev", "approve", ws, "--action", action["id"], "--approver",
             OWNER, "--sha", action["payload_sha256"], "--destination", "week.md")
        keep("classifier-acknowledge", "classifier-acknowledge", ws, "--action", action["id"],
             "--by", OWNER)
        keep("error-classifier-acknowledge-again", "classifier-acknowledge", ws, "--action",
             action["id"], "--by", OWNER)
        keep("approve-after-jev-hold", "approve", ws, "--action", action["id"], "--approver",
             OWNER, "--sha", action["payload_sha256"], "--destination", "week.md")
        keep("classifier-used", "classifier", ws)
        keep("mission-jev-after", "mission", ws, "--today", today, "--week", week)
        # Unreachable: nothing changes, and the manager is told why.
        with mock.patch.object(classifier, "JEV_ENDPOINT",
                               f"http://127.0.0.1:{_closed_port()}/v1/systemone"):
            down = keep("classifier-route-preview-unreachable", "classifier-route-preview", ws,
                        "--request", request)
            keep("classifier-route-unavailable", "classifier-route", ws, "--request", request,
                 "--by", OWNER, "--reviewed-sha", down["request_sha256"])
        keep("classifier-off", "classifier-off", ws, "--by", OWNER)

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
