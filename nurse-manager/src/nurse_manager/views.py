"""Read models for Mission Control, the board, and the table (NM-007 prep).

These are views of one product, not separate stores: every view reads the
same task rows by the same ids, so a card, a table row, and a brief line
can never disagree about a task's status. Views never write.

Empty, sample-data, and unavailable states are stated honestly — a
section with nothing in it says so instead of disappearing, and no view
shows a progress percentage without a defined denominator.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .services import TASK_STATUSES, ManagerWorkspace

BOARD_COLUMNS = (
    ("idea", "Ideas"),
    ("ready", "Ready"),
    ("in_progress", "In progress"),
    ("needs_judgment", "Needs my judgment"),
    ("completed", "Completed"),
)

TABLE_COLUMNS = (
    "task", "project", "owner", "due_date", "status", "reviewer", "evidence", "next_action",
)


def _section(items: list[dict[str, Any]], empty_message: str) -> dict[str, Any]:
    return {
        "state": "ok" if items else "empty",
        "items": items,
        "empty_message": "" if items else empty_message,
    }


def _tasks(ws: ManagerWorkspace) -> list[dict[str, Any]]:
    rows = ws.store.conn.execute(
        "SELECT t.*, p.title AS project_title FROM tasks t"
        " LEFT JOIN projects p ON p.id = t.project_id"
        " WHERE t.workspace_id = ? ORDER BY t.due_date IS NULL, t.due_date, t.created_at, t.id",
        (ws.info.id,),
    )
    return [dict(row) for row in rows]


def board(ws: ManagerWorkspace, *, show_paused: bool = True) -> dict[str, Any]:
    columns = []
    for status, label in BOARD_COLUMNS:
        cards = [
            {
                "id": t["id"],
                "title": t["title"],
                "owner": t["owner"],
                "due_date": t["due_date"],
                "project": t["project_title"],
                "blocked": bool(t["blocked"]),
                "blocked_reason": t["blocked_reason"],
                "paused": bool(t["paused"]),
            }
            for t in _tasks(ws)
            if t["status"] == status and (show_paused or not t["paused"])
        ]
        columns.append({"status": status, "label": label, "count": len(cards), "cards": cards})
    return {"sample": ws.info.sample, "columns": columns}


def table(ws: ManagerWorkspace, *, sort_by: str = "due_date") -> dict[str, Any]:
    if sort_by not in TABLE_COLUMNS:
        raise ValueError(f"cannot sort by {sort_by}")
    rows = [
        {
            "id": t["id"],
            "task": t["title"],
            "project": t["project_title"] or "",
            "owner": t["owner"],
            "due_date": t["due_date"] or "",
            "status": t["status"],
            "blocked": bool(t["blocked"]),
            "paused": bool(t["paused"]),
            "reviewer": t["reviewer"],
            "evidence": t["completion_evidence"],
            "next_action": t["next_action"],
        }
        for t in _tasks(ws)
    ]
    rows.sort(key=lambda r: (r[sort_by] == "", str(r[sort_by]), r["id"]))
    return {"sample": ws.info.sample, "columns": list(TABLE_COLUMNS), "rows": rows}


def mission_control(ws: ManagerWorkspace, *, today: str, week_of: str) -> dict[str, Any]:
    """What needs my attention? Answered from the same records as every view."""
    db = ws.store.conn
    wid = ws.info.id
    tasks = _tasks(ws)
    horizon = (date.fromisoformat(today) + timedelta(days=7)).isoformat()

    priorities = [
        {"rank": r["rank"], "text": r["text"], "project_id": r["project_id"]}
        for r in db.execute(
            "SELECT * FROM priorities WHERE workspace_id = ? AND week_of = ? ORDER BY rank",
            (wid, week_of),
        )
    ]

    judgment: list[dict[str, Any]] = [
        {"kind": "task", "id": t["id"], "title": t["title"], "owner": t["owner"]}
        for t in tasks
        if t["status"] == "needs_judgment"
    ]
    judgment += [
        {"kind": "draft", "id": r["id"], "title": f"Review draft: {r['title']}"}
        for r in db.execute(
            "SELECT rv.id, a.title FROM artifact_revisions rv"
            " JOIN artifacts a ON a.id = rv.artifact_id"
            " WHERE a.workspace_id = ? AND rv.status = 'draft'"
            " AND rv.revision_no = (SELECT max(revision_no) FROM artifact_revisions"
            "                       WHERE artifact_id = rv.artifact_id)"
            " ORDER BY rv.created_at, rv.id",
            (wid,),
        )
    ]
    judgment += [
        {"kind": "action", "id": r["id"], "title": f"Approve {r['effect']}: {r['purpose']}"}
        for r in db.execute(
            "SELECT * FROM actions WHERE workspace_id = ? AND status = 'awaiting_approval'"
            " ORDER BY created_at, id",
            (wid,),
        )
    ]

    projects = []
    for p in db.execute(
        "SELECT * FROM projects WHERE workspace_id = ? AND status = 'active'"
        " ORDER BY created_at, id",
        (wid,),
    ):
        mine = [t for t in tasks if t["project_id"] == p["id"]]
        projects.append(
            {
                "id": p["id"],
                "title": p["title"],
                "owner": p["owner"],
                "next_milestone": p["next_milestone"],
                "open_tasks": sum(1 for t in mine if t["status"] != "completed"),
                "completed_tasks": sum(1 for t in mine if t["status"] == "completed"),
                "blocked_tasks": sum(1 for t in mine if t["blocked"]),
            }
        )

    follow_ups = [
        {
            "id": t["id"],
            "title": t["title"],
            "owner": t["owner"],
            "due_date": t["due_date"],
            "overdue": t["due_date"] < today,
        }
        for t in tasks
        if t["status"] != "completed" and t["due_date"] and t["due_date"] <= horizon
        and not t["paused"]
    ]

    accepted = [
        {"id": r["id"], "title": r["title"], "accepted_by": r["accepted_by"],
         "accepted_at": r["accepted_at"]}
        for r in db.execute(
            "SELECT rv.id, a.title, rv.accepted_by, rv.accepted_at FROM artifact_revisions rv"
            " JOIN artifacts a ON a.id = rv.artifact_id"
            " WHERE a.workspace_id = ? AND rv.status = 'accepted'"
            " ORDER BY rv.accepted_at DESC, rv.id LIMIT 5",
            (wid,),
        )
    ]

    return {
        "workspace": ws.info.name,
        "sample": ws.info.sample,
        "today": today,
        "week_of": week_of,
        "priorities": _section(priorities, "No priorities set for this week yet."),
        "needs_my_judgment": _section(judgment, "Nothing is waiting on your judgment."),
        "projects_in_motion": _section(projects, "No active projects. Start one from an idea."),
        "follow_ups": _section(follow_ups, "No follow-ups due in the next seven days."),
        "assistants_at_work": {
            "state": "unavailable",
            "items": [],
            "empty_message": (
                "No assistant is connected. Planning, briefs, and exports work"
                " without one."
            ),
        },
        "recent_accepted_outputs": _section(accepted, "No accepted outputs yet."),
        "task_counts": {status: sum(1 for t in tasks if t["status"] == status)
                        for status in TASK_STATUSES},
    }
