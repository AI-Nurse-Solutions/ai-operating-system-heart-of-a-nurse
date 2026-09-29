"""Assistants at work, and the stop control (build step 5.3).

One place shows every assistant that is working or waiting to work in a
workspace, and one switch stops them all:

* **Nothing new is sent.** While assistants are stopped, every request to
  a model is refused before anything leaves the workspace.
* **Work already on its way is abandoned.** A request waiting for a model
  notices the stop within about half a second, returns at once, and
  whatever the model sends back afterwards is discarded, never saved or
  shown. (A model on this computer may still finish its own work; nothing
  it returns is used.)
* **The recurring brief waits.** A scheduled run does nothing while
  assistants are stopped.
* **Only the manager stops them, and only the manager lets them work
  again.** Stopping is always allowed, even twice; nothing restarts on its
  own.

Every decision is made inside a write transaction, so a stop and the
saving of a model's reply cannot interleave: either the reply was saved
before the stop, or it is discarded.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .services import ManagerError, ManagerWorkspace

# A request cannot outlast its timeout. One left without a finish time by a
# crash is not shown as working once this much time has passed.
RUNNING_GRACE = timedelta(seconds=30)

TASK_TITLES = {
    "weekly_brief": "Drafting this week's brief",
    "project_question": "Answering a question about a project",
}


class AssistantControl:
    """The one writer for ``assistant_control``."""

    def __init__(self, ws: ManagerWorkspace):
        self.ws = ws

    def state(self) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            "SELECT * FROM assistant_control WHERE workspace_id = ?", (self.ws.info.id,)
        ).fetchone()
        if row is None:
            return {"stopped": False, "generation": 0, "changed_by": "", "changed_at": None}
        return {"stopped": bool(row["stopped"]), "generation": row["generation"],
                "changed_by": row["changed_by"], "changed_at": row["changed_at"]}

    def stop(self, by: str) -> dict[str, Any]:
        """Stop every assistant now. Safe to repeat: each stop abandons what is running."""
        by = self._owner(by)
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO assistant_control (workspace_id, stopped, generation, changed_by,"
                " changed_at) VALUES (?, 1, 1, ?, ?)"
                " ON CONFLICT (workspace_id) DO UPDATE SET stopped = 1,"
                " generation = generation + 1, changed_by = excluded.changed_by,"
                " changed_at = excluded.changed_at",
                (self.ws.info.id, by, self.ws.clock()),
            )
            self.ws.store.log(by, "stop", "assistants", self.ws.info.id)
        return self.state()

    def resume(self, by: str) -> dict[str, Any]:
        """Let assistants work again. Nothing that was stopped restarts by itself."""
        by = self._owner(by)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "UPDATE assistant_control SET stopped = 0, changed_by = ?, changed_at = ?"
                " WHERE workspace_id = ? AND stopped = 1",
                (by, self.ws.clock(), self.ws.info.id),
            ).rowcount
            if changed != 1:
                raise ManagerError("assistants are not stopped")
            self.ws.store.log(by, "resume", "assistants", self.ws.info.id)
        return self.state()

    def running(self) -> list[dict[str, Any]]:
        """Requests on their way to a model right now, oldest first."""
        cutoff = (datetime.fromisoformat(self.ws.clock()) - _longest_request()).isoformat()
        return [dict(row) for row in self.ws.store.conn.execute(
            "SELECT id, task, provider, model, created_at FROM assistant_requests"
            " WHERE workspace_id = ? AND finished_at IS NULL AND created_at >= ?"
            " ORDER BY created_at, id",
            (self.ws.info.id, cutoff),
        )]

    def _owner(self, by: str) -> str:
        by = (by or "").strip()
        if by != self.ws.info.owner:
            raise ManagerError("only the accountable manager for this workspace can stop"
                               " or restart its assistants")
        return by


def _longest_request() -> timedelta:
    from .assistant import REQUEST_TIMEOUT_SECONDS  # noqa: PLC0415 - avoids an import cycle
    return timedelta(seconds=REQUEST_TIMEOUT_SECONDS) + RUNNING_GRACE


def assistants_at_work(ws: ManagerWorkspace) -> dict[str, Any]:
    """The Mission Control section: what is working, what waits, and the switch."""
    from .schedule import WEEKDAYS, BriefSchedule  # noqa: PLC0415 - avoids an import cycle

    control = AssistantControl(ws)
    state = control.state()
    stopped = state["stopped"]
    items: list[dict[str, Any]] = []
    for row in control.running():
        where = "this computer" if row["provider"] == "local" else row["provider"]
        items.append({
            "id": row["id"],
            "kind": "request",
            "title": TASK_TITLES[row["task"]],
            "detail": (f"Stopping: whatever {row['model']} sends back will be discarded."
                       if stopped else
                       f"Waiting for {row['model']} on {where}."),
            "since": row["created_at"],
        })
    schedule = BriefSchedule(ws).view()
    if schedule["enabled"]:
        when = f"{WEEKDAYS[schedule['weekday']]}s at {schedule['hour']:02d}:00"
        items.append({
            "id": "brief-schedule",
            "kind": "schedule",
            "title": "Recurring weekly brief (records only)",
            "detail": (f"Waiting while assistants are stopped ({when})." if stopped else
                       f"A draft from your records on {when}, while this app is open."),
            "since": None,
        })
    if stopped:
        empty = "Assistants are stopped. Nothing runs until you let them work again."
    else:
        empty = _idle_message(ws)
    return {
        "state": "ok" if items else "empty",
        "items": items,
        "empty_message": "" if items else empty,
        "stopped": stopped,
        "changed_by": state["changed_by"],
        "changed_at": state["changed_at"],
    }


def _idle_message(ws: ManagerWorkspace) -> str:
    row = ws.store.conn.execute(
        "SELECT provider FROM assistant_settings WHERE workspace_id = ?", (ws.info.id,)
    ).fetchone()
    if row is None or row["provider"] == "none":
        return "No assistant is connected. Planning, briefs, and exports work without one."
    return ("No assistant is running. A model on this computer drafts only when you"
            " ask it to.")


__all__ = ["AssistantControl", "assistants_at_work"]
