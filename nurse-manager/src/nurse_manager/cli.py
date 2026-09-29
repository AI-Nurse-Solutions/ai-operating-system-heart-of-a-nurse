"""Headless command surface for the manager core.

This is what the desktop host will call over validated IPC; managers never
need a terminal. Every command reopens the workspace from disk — nothing is
held in memory between steps, which is how save → close → reopen is proven.

Every command prints exactly one JSON envelope, versioned by ``CONTRACT``
and described by ``contracts/ipc/`` (schema plus generated TypeScript):

    {"contract": ..., "command": ..., "ok": true,  "data": {...}}
    {"contract": ..., "command": ..., "ok": false, "error": {"type": ..., "message": ...}}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import update
from .actions import ActionBoundary
from .assistant import DEFAULT_LOCAL_ENDPOINT, AssistantService
from .brief import BriefService
from .control import AssistantControl, assistants_at_work
from .sample import load_sample
from .memory import WorkspaceMemory
from .packs import PackService
from .pilot import AREAS as PILOT_AREAS, KINDS as PILOT_KINDS, PilotFeedback, pilot_item
from .schedule import BriefSchedule
from .services import ManagerError, ManagerWorkspace, _iso_date
from .views import (
    board,
    contribution_item,
    contributions,
    feedback_item,
    learning,
    learning_item,
    memory,
    memory_item,
    library,
    mission_control,
    packs,
    project_dashboard,
    table,
)


CONTRACT = "nurse-manager-ipc@1"


def _emit(envelope: dict[str, Any]) -> None:
    json.dump(envelope, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nurse-manager")
    sub = parser.add_subparsers(dest="command", required=True)

    def ws_cmd(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("workspace", type=Path)
        return p

    p = ws_cmd("init", "create an empty Personal Manager workspace")
    p.add_argument("--name", required=True)
    p.add_argument("--owner", required=True)
    ws_cmd("sample", "create the synthetic sample workspace")
    p = ws_cmd("mission", "Mission Control: what needs my attention?")
    p.add_argument("--today", required=True)
    p.add_argument("--week", required=True)
    p = ws_cmd("project", "one project's dashboard: what will move it forward?")
    p.add_argument("--id", required=True)
    p.add_argument("--today", required=True)
    ws_cmd("board", "task board")
    ws_cmd("table", "task table")
    p = ws_cmd("learning", "your own learning: in progress, planned, completed")
    p.add_argument("--today", required=True)
    p = ws_cmd("learning-add", "plan a piece of your own professional learning")
    p.add_argument("--title", required=True)
    p.add_argument("--kind", required=True,
                   choices=("course", "reading", "conference", "certification", "mentoring"))
    p.add_argument("--target", help="YYYY-MM-DD")
    p.add_argument("--hours", help="continuing-education hours, if any")
    p = ws_cmd("learning-start", "start planned learning")
    p.add_argument("--id", required=True)
    p = ws_cmd("learning-complete", "complete learning, with what you took away")
    p.add_argument("--id", required=True)
    p.add_argument("--takeaway", required=True)
    p.add_argument("--completed", required=True, help="YYYY-MM-DD")
    p.add_argument("--hours")
    p = ws_cmd("contributions", "your contributions: drafts awaiting evidence, then verified")
    p.add_argument("--today", required=True)
    p = ws_cmd("contribution-add", "record a contribution as a draft, with who shares the credit")
    p.add_argument("--title", required=True)
    p.add_argument("--kind", required=True,
                   choices=("improvement", "teaching", "committee", "presentation", "publication"))
    p.add_argument("--occurred", required=True, help="YYYY-MM-DD")
    p.add_argument("--my-part", required=True, dest="my_part")
    p.add_argument("--shared-credit", required=True, dest="shared_credit",
                   help="teams, groups or roles; never named colleagues")
    p.add_argument("--project")
    p = ws_cmd("contribution-verify", "verify a draft with the evidence that shows it happened")
    p.add_argument("--id", required=True)
    p.add_argument("--evidence", required=True)
    p = ws_cmd("memory", "what the assistant is asked to remember, and what it is sent")
    p.add_argument("--today", required=True)
    p = ws_cmd("memory-add", "remember something you wrote, for all work or one project")
    p.add_argument("--content", required=True)
    p.add_argument("--project")
    p.add_argument("--expires", help="YYYY-MM-DD; after it, the memory is not sent")
    p.add_argument("--today", required=True)
    for name, help_text in (("memory-correct", "correct a memory's text"),
                            ("memory-exclude", "keep a memory but never send it"),
                            ("memory-include", "use an excluded memory again"),
                            ("memory-delete", "delete a memory for good")):
        p = ws_cmd(name, help_text)
        p.add_argument("--id", required=True)
        if name == "memory-correct":
            p.add_argument("--content", required=True)
        if name != "memory-delete":
            p.add_argument("--today", required=True)
    p = ws_cmd("packs", "education, committee, and communication packs, and documents from them")
    p.add_argument("--today", required=True)
    p = ws_cmd("pack-start", "start a draft document from one template of a current pack")
    p.add_argument("--pack", required=True)
    p.add_argument("--template", required=True)
    p.add_argument("--project")
    p.add_argument("--today", required=True)
    p = ws_cmd("document", "one document started from a pack: its current text and acceptance")
    p.add_argument("--id", required=True)
    p = ws_cmd("document-save", "save an edit to a pack document as a new draft")
    p.add_argument("--id", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--base", required=True, help="sha256 of the text you edited")
    p = ws_cmd("library", "every source in the workspace; overdue reviews first")
    p.add_argument("--today", required=True)
    p = ws_cmd("source-add", "add a source (public, synthetic, or permitted personal material)")
    p.add_argument("--title", required=True)
    p.add_argument("--kind", required=True, choices=("public", "synthetic", "personal_permitted"))
    p.add_argument("--reference", required=True)
    p.add_argument("--data-class", default="D0", choices=("D0", "D1"))
    p.add_argument("--project")
    p.add_argument("--review", help="YYYY-MM-DD: when to check it is still current")
    p = ws_cmd("feedback-add", "record feedback about a project's work (from a group or role)")
    p.add_argument("--project", required=True)
    p.add_argument("--from", dest="from_group", required=True)
    p.add_argument("--kind", required=True, choices=("worked", "change", "question"))
    p.add_argument("--summary", required=True)
    p.add_argument("--received", required=True, help="YYYY-MM-DD")
    p = ws_cmd("feedback-address", "mark feedback addressed, with a written response")
    p.add_argument("--id", required=True)
    p.add_argument("--response", required=True)
    p = ws_cmd("brief", "draft this week's brief from records (no model)")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
    p = ws_cmd("brief-schedule-set", "turn the recurring weekly brief on or off (records only)")
    p.add_argument("--enabled", required=True, choices=("yes", "no"))
    p.add_argument("--weekday", required=True, type=int, choices=range(7),
                   help="0 (Monday) to 6 (Sunday), local time")
    p.add_argument("--hour", required=True, type=int, choices=range(24), help="0 to 23, local time")
    p.add_argument("--by", required=True)
    ws_cmd("brief-run-due", "prepare this week's recurring draft if it is due (safe to repeat)")
    p = ws_cmd("show", "render one revision")
    p.add_argument("--revision", required=True)
    p = ws_cmd("accept", "accept exactly the revision you reviewed")
    p.add_argument("--revision", required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--sha", required=True, help="sha256 of the text you reviewed")
    p = ws_cmd("export", "propose exporting an accepted revision")
    p.add_argument("--revision", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--by", required=True)
    p = ws_cmd("approve", "approve a proposed action")
    p.add_argument("--action", required=True)
    p.add_argument("--approver", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--destination", required=True)
    p = ws_cmd("run", "run an approved action (rechecks first)")
    p.add_argument("--action", required=True)
    p.add_argument("--actor", required=True)
    p = ws_cmd("reconcile", "after a crash: settle any export that was interrupted"
                            " (checks the file; never runs it again)")
    ws_cmd("pilot-feedback", "your pilot feedback, kept on this computer")
    p = ws_cmd("pilot-feedback-add", "write pilot feedback about the app (never sent anywhere)")
    p.add_argument("--area", required=True, choices=tuple(PILOT_AREAS))
    p.add_argument("--kind", required=True, choices=tuple(PILOT_KINDS))
    p.add_argument("--summary", required=True)
    p = ws_cmd("pilot-feedback-delete", "delete one piece of pilot feedback for good")
    p.add_argument("--id", required=True)
    ws_cmd("pilot-feedback-preview", "exactly what exporting pilot feedback would share;"
                                     " exports nothing")
    p = ws_cmd("pilot-feedback-export", "export the pilot feedback you reviewed, as text you save"
                                        " and share yourself")
    p.add_argument("--reviewed-sha", required=True, help="sha256 of the preview you reviewed")
    p.add_argument("--by", required=True)
    p = ws_cmd("backup", "copy the workspace database")
    p.add_argument("dest", type=Path)
    p = ws_cmd("restore", "restore from a backup (refuses to discard newer work)")
    p.add_argument("src", type=Path)
    p.add_argument("--discard-newer", action="store_true")
    p = ws_cmd("weekly", "this week's brief: the current revision and the accepted one")
    p.add_argument("--week", required=True)
    ws_cmd("assistant", "AI settings, usage, and the gates every provider passes")
    p = ws_cmd("assistant-local", "connect a model on this computer (never preselected)")
    p.add_argument("--model", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--endpoint", default=DEFAULT_LOCAL_ENDPOINT)
    p.add_argument("--daily-limit", type=int)
    p = ws_cmd("assistant-off", "disconnect the AI model; back to no model")
    p.add_argument("--by", required=True)
    p = ws_cmd("assistants-stop", "stop every assistant now: nothing is sent, running work is"
                                  " abandoned, the recurring brief waits")
    p.add_argument("--by", required=True)
    p = ws_cmd("assistants-resume", "let assistants work again (nothing restarts by itself)")
    p.add_argument("--by", required=True)
    p = ws_cmd("assistant-preview", "exactly what asking the model would send; sends nothing")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
    p = ws_cmd("assistant-brief", "draft this week's brief with the connected model, or without one")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--reviewed-sha", help="sha256 of the preview you reviewed; refuses if it changed")
    p = ws_cmd("assistant-project-preview",
               "exactly what asking about one project would send; sends nothing")
    p.add_argument("--id", required=True)
    p.add_argument("--today", required=True)
    p.add_argument("--question", required=True)
    p = ws_cmd("note-keep", "keep an AI answer as a project note, exactly as the model gave it")
    p.add_argument("--request", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--answer", required=True)
    p.add_argument("--by", required=True)
    p = ws_cmd("assistant-project", "ask the connected model about one project; nothing is saved")
    p.add_argument("--id", required=True)
    p.add_argument("--today", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--reviewed-sha", help="sha256 of the preview you reviewed; refuses if it changed")

    # Not a workspace command: it checks this installation's release.
    p = sub.add_parser("update-check", help="check the signed update feed (never installs)")
    p.add_argument("--feed", type=Path, help="a feed file you were given, instead of the feed address")
    p.add_argument("--signature", type=Path, help="that feed's signature file")
    # Deliberately no way to choose the pinned keys, the record of feeds seen,
    # or today's date: each would let the caller undo a trust check.

    return parser


def commands() -> tuple[str, ...]:
    """Every command the host can send; contracts/ipc/commands.json must match."""
    sub = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return tuple(sub.choices)


def _dispatch(args: argparse.Namespace) -> Any:
    """Run one parsed command and return its data. The workspace is always closed."""
    # Every "today" and "week" is a real YYYY-MM-DD date before any view uses it:
    # the envelope promises IsoDate, and views derive years and windows from it.
    for name in ("today", "week"):
        value = getattr(args, name, None)
        if value is not None:
            setattr(args, name, _iso_date(value, f"--{name}"))
    if args.command == "update-check":
        return update.check(feed_file=args.feed, signature_file=args.signature)
    if args.command == "sample":
        ws, data = load_sample(args.workspace)
        try:
            return {"workspace": ws.info.__dict__, "week_of": data["week_of"], "today": data["today"]}
        finally:
            ws.close()
    ws = ManagerWorkspace(args.workspace)
    try:
        if args.command == "init":
            return ws.create(args.name, args.owner).__dict__
        if args.command == "mission":
            return mission_control(ws, today=args.today, week_of=args.week)
        if args.command == "project":
            return project_dashboard(ws, args.id, today=args.today)
        if args.command == "board":
            return board(ws)
        if args.command == "table":
            return table(ws)
        if args.command == "library":
            return library(ws, today=args.today)
        if args.command == "learning":
            return learning(ws, today=args.today)
        if args.command == "learning-add":
            item_id = ws.add_learning(args.title, args.kind, target_date=args.target,
                                      hours=args.hours)
            return {"item": learning_item(ws, item_id)}
        if args.command == "learning-start":
            ws.start_learning(args.id)
            return {"item": learning_item(ws, args.id)}
        if args.command == "learning-complete":
            ws.complete_learning(args.id, args.takeaway, args.completed, hours=args.hours)
            return {"item": learning_item(ws, args.id)}
        if args.command == "memory":
            return memory(ws, today=args.today)
        if args.command.startswith("memory-"):
            memories = WorkspaceMemory(ws)
            if args.command == "memory-add":
                item_id = memories.add(args.content, project_id=args.project,
                                       expires_on=args.expires)
                return {"item": memory_item(ws, item_id, today=args.today)}
            if args.command == "memory-delete":
                memories.delete(args.id)
                return {"deleted": args.id}
            {"memory-correct": lambda: memories.correct_text(args.id, args.content),
             "memory-exclude": lambda: memories.exclude(args.id),
             "memory-include": lambda: memories.include(args.id)}[args.command]()
            return {"item": memory_item(ws, args.id, today=args.today)}
        if args.command == "packs":
            return packs(ws, today=args.today)
        if args.command in ("pack-start", "document", "document-save"):
            documents = PackService(ws)
            if args.command == "pack-start":
                document_id = documents.start(args.pack, args.template,
                                              project_id=args.project, today=args.today)
            else:
                document_id = args.id
            if args.command == "document-save":
                documents.save(document_id, args.body, args.base)
            return documents.view(document_id)
        if args.command.startswith("pilot-feedback"):
            pilot = PilotFeedback(ws)
            if args.command == "pilot-feedback-add":
                return {"item": pilot_item(ws, pilot.add(args.area, args.kind, args.summary))}
            if args.command == "pilot-feedback-delete":
                pilot.delete(args.id)
                return {"deleted": args.id}
            if args.command == "pilot-feedback-preview":
                return pilot.preview()
            if args.command == "pilot-feedback-export":
                return pilot.export(args.reviewed_sha, args.by)
            return pilot.view()
        if args.command == "contributions":
            return contributions(ws, today=args.today)
        if args.command == "contribution-add":
            item_id = ws.add_contribution(args.title, args.kind, args.occurred, args.my_part,
                                          args.shared_credit, project_id=args.project)
            return {"item": contribution_item(ws, item_id)}
        if args.command == "contribution-verify":
            ws.verify_contribution(args.id, args.evidence)
            return {"item": contribution_item(ws, args.id)}
        if args.command == "source-add":
            source_id = ws.add_source(args.title, args.kind, args.reference,
                                      data_class=args.data_class, project_id=args.project,
                                      review_date=args.review)
            return {"source": next(i for i in library(ws, today=ws.local_today())["items"]
                                   if i["id"] == source_id)}
        if args.command in ("feedback-add", "feedback-address"):
            if args.command == "feedback-add":
                feedback_id = ws.add_feedback(args.project, args.from_group, args.kind,
                                              args.summary, args.received)
            else:
                feedback_id = ws.address_feedback(args.id, args.response) or args.id
            return {"feedback": feedback_item(ws, feedback_id)}
        if args.command in ("assistants-stop", "assistants-resume"):
            control = AssistantControl(ws)
            if args.command == "assistants-stop":
                control.stop(args.by)
            else:
                control.resume(args.by)
            return assistants_at_work(ws)
        if args.command.startswith("assistant") or args.command == "note-keep":
            assistant = AssistantService(ws)
            if args.command == "assistant":
                return assistant.status()
            if args.command == "assistant-local":
                return assistant.connect_local(args.by, args.model, endpoint=args.endpoint,
                                               daily_request_limit=args.daily_limit)
            if args.command == "assistant-off":
                return assistant.disconnect(args.by)
            if args.command == "assistant-preview":
                return assistant.preview_weekly_brief(args.week, args.today)
            if args.command == "note-keep":
                return assistant.keep_project_note(args.request, args.project, args.question,
                                                   args.answer, args.by)
            if args.command == "assistant-project-preview":
                return assistant.preview_project_question(args.id, args.question, args.today)
            if args.command == "assistant-project":
                return assistant.answer_project_question(
                    args.id, args.question, args.today, args.by,
                    reviewed_prompt_sha256=args.reviewed_sha)
            if args.command == "assistant-brief":
                return assistant.draft_weekly_brief(
                    args.week, args.today, args.by, reviewed_prompt_sha256=args.reviewed_sha)
        briefs = BriefService(ws)
        if args.command == "brief":
            return briefs.as_dict(briefs.draft_weekly_brief(args.week, args.today))
        if args.command == "weekly":
            return {**briefs.weekly(args.week), "schedule": BriefSchedule(ws).view()}
        if args.command == "brief-schedule-set":
            schedule = BriefSchedule(ws)
            schedule.configure(enabled=args.enabled == "yes", weekday=args.weekday,
                               hour=args.hour, by=args.by)
            return schedule.view()
        if args.command == "brief-run-due":
            return BriefSchedule(ws).run_due()
        if args.command == "show":
            revision = briefs.revision(args.revision)
            return {"revision": briefs.as_dict(revision), "markdown": briefs.render(revision)}
        if args.command == "accept":
            return briefs.as_dict(briefs.accept(args.revision, args.reviewer, args.sha))
        boundary = ActionBoundary(ws)
        if args.command == "export":
            return boundary.propose(
                "export_markdown", revision_id=args.revision, destination=args.file,
                purpose="Save the accepted weekly brief as a Markdown file", proposed_by=args.by,
            ).__dict__
        if args.command == "approve":
            return boundary.approve(
                args.action, args.approver, seen_sha256=args.sha,
                seen_destination=args.destination,
            ).__dict__
        if args.command == "run":
            return boundary.execute(args.action, args.actor)
        if args.command == "reconcile":
            return {"settled": boundary.reconcile()}
        if args.command == "backup":
            return {"backup": str(ws.store.backup(args.dest))}
        if args.command == "restore":
            safety = ws.store.restore(args.src, allow_discarding_newer=args.discard_newer)
            return {"restored_from": str(args.src), "pre_restore_backup": str(safety)}
        raise AssertionError(f"unhandled command {args.command}")  # pragma: no cover
    finally:
        ws.close()


def run(argv: list[str]) -> tuple[int, dict[str, Any]]:
    """Run one command and return (exit code, envelope) without printing.

    The in-process entry point for hosts (the dev host, tests): no global
    stdout redirection, so it is safe to call from several threads.
    """
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        if not exc.code:
            raise  # --help: argparse has printed it
        # Arguments argparse cannot parse are answered like any other refusal,
        # never with an exit that leaves a host without a reply.
        return 2, {"contract": CONTRACT, "command": argv[0] if argv else "", "ok": False,
                   "error": {"type": "UsageError",
                             "message": "the command's arguments were not understood"}}
    base = {"contract": CONTRACT, "command": args.command}
    try:
        # Round-trip through JSON so in-process callers receive exactly the
        # types the printed envelope carries (lists, not tuples).
        data = json.loads(json.dumps(_dispatch(args)))
        return 0, {**base, "ok": True, "data": data}
    except Exception as exc:  # noqa: BLE001 — surface a truthful state, never a traceback
        code = 2 if isinstance(exc, ManagerError) else 1
        return code, {**base, "ok": False,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}


def main(argv: list[str] | None = None) -> int:
    code, envelope = run(sys.argv[1:] if argv is None else argv)
    _emit(envelope)
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
