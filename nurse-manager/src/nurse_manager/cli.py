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
from .brief import BriefService
from .sample import load_sample
from .services import ManagerError, ManagerWorkspace
from .views import board, mission_control, table


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

    return parser


def commands() -> tuple[str, ...]:
    """Every command the host can send; contracts/ipc/commands.json must match."""
    sub = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return tuple(sub.choices)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def ok(data: Any) -> int:
        _emit({"contract": CONTRACT, "command": args.command, "ok": True, "data": data})
        return 0

    def fail(exc: Exception, code: int) -> int:
        _emit({"contract": CONTRACT, "command": args.command, "ok": False,
               "error": {"type": type(exc).__name__, "message": str(exc)}})
        return code

    try:
        if args.command == "sample":
            ws, data = load_sample(args.workspace)
            return ok({"workspace": ws.info.__dict__, "week_of": data["week_of"],
                       "today": data["today"]})
        ws = ManagerWorkspace(args.workspace)
        if args.command == "init":
            return ok(ws.create(args.name, args.owner).__dict__)
        if args.command == "mission":
            return ok(mission_control(ws, today=args.today, week_of=args.week))
        if args.command == "board":
            return ok(board(ws))
        if args.command == "table":
            return ok(table(ws))
        briefs = BriefService(ws)
        if args.command == "brief":
            return ok(briefs.as_dict(briefs.draft_weekly_brief(args.week, args.today)))
        if args.command == "show":
            revision = briefs.revision(args.revision)
            return ok({"revision": briefs.as_dict(revision), "markdown": briefs.render(revision)})
        if args.command == "accept":
            return ok(briefs.as_dict(briefs.accept(args.revision, args.reviewer, args.sha)))
        boundary = ActionBoundary(ws)
        if args.command == "export":
            return ok(boundary.propose(
                "export_markdown", revision_id=args.revision, destination=args.file,
                purpose="Save the accepted weekly brief as a Markdown file", proposed_by=args.by,
            ).__dict__)
        if args.command == "approve":
            return ok(boundary.approve(
                args.action, args.approver, seen_sha256=args.sha,
                seen_destination=args.destination,
            ).__dict__)
        if args.command == "run":
            return ok(boundary.execute(args.action, args.actor))
        if args.command == "backup":
            return ok({"backup": str(ws.store.backup(args.dest))})
        if args.command == "restore":
            safety = ws.store.restore(args.src, allow_discarding_newer=args.discard_newer)
            return ok({"restored_from": str(args.src), "pre_restore_backup": str(safety)})
        raise AssertionError(f"unhandled command {args.command}")  # pragma: no cover
    except ManagerError as exc:
        return fail(exc, 2)
    except Exception as exc:  # noqa: BLE001 — surface a truthful state, never a traceback
        return fail(exc, 1)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
