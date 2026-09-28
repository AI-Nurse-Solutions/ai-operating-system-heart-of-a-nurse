"""Read models for Mission Control, the board, and the table (NM-007 prep).

These are views of one product, not separate stores: every view reads the
same task rows by the same ids, so a card, a table row, and a brief line
can never disagree about a task's status. Views never write.

Empty, sample-data, and unavailable states are stated honestly — a
section with nothing in it says so instead of disappearing, and no view
shows a progress percentage without a defined denominator.
"""

from __future__ import annotations

import json
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


def _row(t: dict[str, Any]) -> dict[str, Any]:
    """One task as a table row: the same shape wherever tasks are listed."""
    return {
        "id": t["id"],
        "task": t["title"],
        "project": t["project_title"],
        "owner": t["owner"],
        "due_date": t["due_date"],
        "status": t["status"],
        "blocked": bool(t["blocked"]),
        "paused": bool(t["paused"]),
        "reviewer": t["reviewer"],
        "evidence": t["completion_evidence"],
        "next_action": t["next_action"],
    }


def _sort_rows(rows: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    # Absent values (null) sort last, whatever the column.
    return sorted(rows, key=lambda r: (r[sort_by] in (None, ""), str(r[sort_by] or ""), r["id"]))


def table(ws: ManagerWorkspace, *, sort_by: str = "due_date") -> dict[str, Any]:
    if sort_by not in TABLE_COLUMNS:
        raise ValueError(f"cannot sort by {sort_by}")
    rows = _sort_rows([_row(t) for t in _tasks(ws)], sort_by)
    return {"sample": ws.info.sample, "columns": list(TABLE_COLUMNS), "rows": rows}


def project_dashboard(ws: ManagerWorkspace, project_id: str, *, today: str) -> dict[str, Any]:
    """What will move this initiative forward? One project, from the same records.

    Readiness is a set of stated facts, never a score or a percentage: the
    plan forbids progress figures without a defined denominator.
    """
    project = ws._require_row("projects", project_id)
    db = ws.store.conn
    tasks = [t for t in _tasks(ws) if t["project_id"] == project_id]
    open_tasks = [t for t in tasks if t["status"] != "completed"]
    decisions = [
        {
            "id": d["id"],
            "question": d["question"],
            "decision": d["decision"],
            "decided_by": d["decided_by"],
            "decided_on": d["decided_on"],
            "rationale": d["rationale"],
        }
        for d in db.execute(
            "SELECT * FROM decisions WHERE workspace_id = ? AND project_id = ?"
            " ORDER BY decided_on DESC, id",
            (ws.info.id, project_id),
        )
    ]
    resources = [
        {
            "id": r["id"],
            "title": r["title"],
            "kind": r["kind"],
            "reference": r["reference"],
            "review_date": r["review_date"],
            "review_overdue": bool(r["review_date"] and r["review_date"] < today),
        }
        for r in db.execute(
            "SELECT * FROM sources WHERE workspace_id = ? AND project_id = ? ORDER BY title, id",
            (ws.info.id, project_id),
        )
    ]
    feedback = [
        _feedback(f)
        # Open feedback first; newest first within each.
        for f in db.execute(
            "SELECT * FROM project_feedback WHERE workspace_id = ? AND project_id = ?"
            " ORDER BY status = 'addressed', received_on DESC, id",
            (ws.info.id, project_id),
        )
    ]
    evidence = [
        {"task_id": t["id"], "task": t["title"], "evidence": t["completion_evidence"]}
        for t in tasks
        if t["status"] == "completed"
    ]
    return {
        "sample": ws.info.sample,
        "today": today,
        "project": {
            "id": project["id"],
            "title": project["title"],
            "purpose": project["purpose"],
            "owner": project["owner"],
            "next_milestone": project["next_milestone"],
            "status": project["status"],
        },
        "readiness": {
            "has_next_milestone": bool(project["next_milestone"].strip()),
            "open_tasks": len(open_tasks),
            "completed_tasks": len(tasks) - len(open_tasks),
            "blocked_tasks": sum(1 for t in open_tasks if t["blocked"]),
            "needs_judgment": sum(1 for t in open_tasks if t["status"] == "needs_judgment"),
            "overdue_tasks": sum(
                1 for t in open_tasks if t["due_date"] and t["due_date"] < today and not t["paused"]
            ),
            "open_feedback": sum(1 for f in feedback if f["status"] == "open"),
            "tasks_without_next_action": sum(
                1 for t in open_tasks if t["status"] in ("ready", "in_progress") and not t["next_action"]
            ),
        },
        "tasks": _sort_rows([_row(t) for t in tasks], "due_date"),
        "decisions": decisions,
        "resources": resources,
        "evidence": evidence,
        "feedback": feedback,
        # Kept AI answers, newest first. Each was kept by the manager on purpose.
        "notes": [
            note_dict(n)
            for n in db.execute(
                "SELECT * FROM project_notes WHERE workspace_id = ? AND project_id = ?"
                " ORDER BY kept_at DESC, id",
                (ws.info.id, project_id),
            )
        ],
    }


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
            "empty_message": _assistants_message(ws),
        },
        "recent_accepted_outputs": _section(accepted, "No accepted outputs yet."),
        "task_counts": {status: sum(1 for t in tasks if t["status"] == status)
                        for status in TASK_STATUSES},
    }


def _assistants_message(ws: ManagerWorkspace) -> str:
    row = ws.store.conn.execute(
        "SELECT provider FROM assistant_settings WHERE workspace_id = ?", (ws.info.id,)
    ).fetchone()
    if row is None or row["provider"] == "none":
        return "No assistant is connected. Planning, briefs, and exports work without one."
    # A model is connected, but nothing runs in the background (G5).
    return ("No assistant is running. A model on this computer drafts only when you"
            " ask it to.")


def note_dict(row) -> dict[str, Any]:
    """A kept project note, in the contract's ProjectNote shape."""
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "request_id": row["request_id"],
        "question": row["question"],
        "body_markdown": row["body_markdown"],
        "sha256": row["body_sha256"],
        "source_refs": json.loads(row["source_refs"]),
        "written_by": row["written_by"],
        "model": row["model"],
        "kept_by": row["kept_by"],
        "kept_at": row["kept_at"],
    }


def _feedback(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "from_group": row["from_group"],
        "kind": row["kind"],
        "summary": row["summary"],
        "received_on": row["received_on"],
        "status": row["status"],
        "response": row["response"],
        "addressed_on": row["addressed_on"],
    }


def feedback_item(ws: ManagerWorkspace, feedback_id: str) -> dict[str, Any]:
    return _feedback(ws._require_row("project_feedback", feedback_id))


def library(ws: ManagerWorkspace, *, today: str) -> dict[str, Any]:
    """Every source in the workspace, whichever project it belongs to.

    Sources whose review date has passed come first: an out-of-date source
    should be checked before it is relied on again.
    """
    rows = ws.store.conn.execute(
        "SELECT s.*, p.title AS project_title FROM sources s"
        " LEFT JOIN projects p ON p.id = s.project_id WHERE s.workspace_id = ?",
        (ws.info.id,),
    ).fetchall()
    items = [
        {
            "id": r["id"],
            "title": r["title"],
            "kind": r["kind"],
            "reference": r["reference"],
            "data_class": r["data_class"],
            "project_id": r["project_id"],
            "project": r["project_title"],
            "review_date": r["review_date"],
            "review_overdue": bool(r["review_date"] and r["review_date"] < today),
        }
        for r in rows
    ]
    items.sort(key=lambda i: (not i["review_overdue"], i["title"].lower(), i["id"]))
    return {
        "sample": ws.info.sample,
        "today": today,
        "items": items,
        "review_overdue": sum(1 for i in items if i["review_overdue"]),
        "projects": [
            {"id": p["id"], "title": p["title"]}
            for p in ws.store.conn.execute(
                "SELECT id, title FROM projects WHERE workspace_id = ? ORDER BY title, id",
                (ws.info.id,))
        ],
    }


def _learning(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "kind": row["kind"],
        "status": row["status"],
        "target_date": row["target_date"],
        "hours": row["hours"],
        "takeaway": row["takeaway"],
        "completed_on": row["completed_on"],
    }


def learning_item(ws: ManagerWorkspace, learning_id: str) -> dict[str, Any]:
    return _learning(ws._require_row("learning_items", learning_id))


def learning(ws: ManagerWorkspace, *, today: str) -> dict[str, Any]:
    """The manager's own learning: in progress, planned, then completed.

    Stated facts only: counts and completed hours this year, never a score.
    """
    rows = [_learning(r) for r in ws.store.conn.execute(
        "SELECT * FROM learning_items WHERE workspace_id = ?", (ws.info.id,))]
    def by_target(r):  # soonest target first, undated last
        return (r["target_date"] or "9999-12-31", r["title"].lower(), r["id"])

    completed = sorted((r for r in rows if r["status"] == "completed"),
                       key=lambda r: (r["completed_on"], r["id"]), reverse=True)
    rows = (sorted((r for r in rows if r["status"] == "in_progress"), key=by_target)
            + sorted((r for r in rows if r["status"] == "planned"), key=by_target)
            + completed)
    year = today[:4]
    done_this_year = [r for r in rows if r["status"] == "completed"
                      and (r["completed_on"] or "").startswith(year)]
    return {
        "sample": ws.info.sample,
        "today": today,
        "items": rows,
        "in_progress": sum(1 for r in rows if r["status"] == "in_progress"),
        "planned": sum(1 for r in rows if r["status"] == "planned"),
        "completed_this_year": len(done_this_year),
        "hours_this_year": round(sum(r["hours"] or 0 for r in done_this_year), 1),
        "past_target": sum(1 for r in rows if r["status"] != "completed"
                           and r["target_date"] and r["target_date"] < today),
    }
