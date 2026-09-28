"""Headless command surface for the manager core.

This is what the desktop host will call over validated IPC; managers never
need a terminal. Every command prints JSON so the host can render it, and
every command reopens the workspace from disk — nothing is held in memory
between steps, which is how save → close → reopen is proven.
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


def _out(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
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

    args = parser.parse_args(argv)
    try:
        if args.command == "sample":
            ws, data = load_sample(args.workspace)
            _out({"workspace": ws.info.__dict__, "week_of": data["week_of"],
                  "today": data["today"]})
            return 0
        ws = ManagerWorkspace(args.workspace)
        if args.command == "init":
            _out(ws.create(args.name, args.owner).__dict__)
        elif args.command == "mission":
            _out(mission_control(ws, today=args.today, week_of=args.week))
        elif args.command == "board":
            _out(board(ws))
        elif args.command == "table":
            _out(table(ws))
        elif args.command == "brief":
            briefs = BriefService(ws)
            _out(briefs.as_dict(briefs.draft_weekly_brief(args.week, args.today)))
        elif args.command == "show":
            briefs = BriefService(ws)
            sys.stdout.write(briefs.render(briefs.revision(args.revision)))
        elif args.command == "accept":
            briefs = BriefService(ws)
            _out(briefs.as_dict(briefs.accept(args.revision, args.reviewer, args.sha)))
        elif args.command == "export":
            record = ActionBoundary(ws).propose(
                "export_markdown", revision_id=args.revision, destination=args.file,
                purpose="Save the accepted weekly brief as a Markdown file", proposed_by=args.by,
            )
            _out(record.__dict__)
        elif args.command == "approve":
            record = ActionBoundary(ws).approve(
                args.action, args.approver, seen_sha256=args.sha,
                seen_destination=args.destination,
            )
            _out(record.__dict__)
        elif args.command == "run":
            _out(ActionBoundary(ws).execute(args.action, args.actor))
        elif args.command == "backup":
            _out({"backup": str(ws.store.backup(args.dest))})
        elif args.command == "restore":
            safety = ws.store.restore(args.src, allow_discarding_newer=args.discard_newer)
            _out({"restored_from": str(args.src), "pre_restore_backup": str(safety)})
    except ManagerError as exc:
        _out({"error": str(exc), "type": type(exc).__name__})
        return 2
    except Exception as exc:  # noqa: BLE001 — surface a truthful state, never a traceback
        _out({"error": str(exc), "type": type(exc).__name__})
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
