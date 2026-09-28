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

from .actions import ActionBoundary
from .assistant import DEFAULT_LOCAL_ENDPOINT, AssistantService
from .brief import BriefService
from .sample import load_sample
from .services import ManagerError, ManagerWorkspace
from .views import board, mission_control, project_dashboard, table


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
    p = ws_cmd("brief", "draft this week's brief from records (no model)")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
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
    p = ws_cmd("assistant-preview", "exactly what asking the model would send; sends nothing")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
    p = ws_cmd("assistant-brief", "draft this week's brief with the connected model, or without one")
    p.add_argument("--week", required=True)
    p.add_argument("--today", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--reviewed-sha", help="sha256 of the preview you reviewed; refuses if it changed")

    return parser


def commands() -> tuple[str, ...]:
    """Every command the host can send; contracts/ipc/commands.json must match."""
    sub = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return tuple(sub.choices)


def _dispatch(args: argparse.Namespace) -> Any:
    """Run one parsed command and return its data. The workspace is always closed."""
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
        if args.command.startswith("assistant"):
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
            if args.command == "assistant-brief":
                return assistant.draft_weekly_brief(
                    args.week, args.today, args.by, reviewed_prompt_sha256=args.reviewed_sha)
        briefs = BriefService(ws)
        if args.command == "brief":
            return briefs.as_dict(briefs.draft_weekly_brief(args.week, args.today))
        if args.command == "weekly":
            return briefs.weekly(args.week)
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
    args = build_parser().parse_args(argv)
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
