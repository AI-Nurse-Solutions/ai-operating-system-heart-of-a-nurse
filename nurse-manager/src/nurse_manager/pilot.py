"""Pilot feedback (build step 6.3): kept on this computer, shared only by the manager.

A pilot manager writes down what worked, a problem, an idea, or a question
about the app itself. The rules:

* **Local first.** Feedback is a workspace record like any other. Nothing
  is sent anywhere, now or later: there is no destination to send it to.
* **Screened like every other capture.** Each item passes the privacy
  screen when it is written, and the whole export is screened again before
  it is made. A finding refuses; identifiers are not "redacted" and kept.
  The screen does not detect names, so nothing here is ever described as
  free of patient information.
* **What is shared is what was shown.** ``preview`` returns the exact text
  and its sha256. ``export`` rebuilds it, and makes it only if it is the
  text the manager reviewed; any change in between refuses. The app never
  writes the file itself: the manager's browser saves the reviewed text,
  and the manager decides who receives it.
* **Only feedback crosses.** The export carries the app version, whether
  this is the synthetic sample, and the items. It never carries the
  workspace's name, the manager's name, record ids, or any other record.

An export always holds every item on the page, so a file that was not
saved is never lost: export again. Deleting an item deletes its text.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from . import __version__
from .services import CaptureRefused, ManagerError, ManagerWorkspace
from .store import new_id

AREAS = {
    "getting_started": "Getting started",
    "mission_control": "Mission Control",
    "weekly_brief": "Weekly brief",
    "projects": "Projects and tasks",
    "ai_assistance": "AI assistance",
    "packs": "Packs",
    "other": "Something else",
}
KINDS = {"worked": "Worked well", "problem": "Problem", "idea": "Idea", "question": "Question"}
MAX_PILOT_TEXT = 1000

HEADER = (
    "Written by a pilot manager on their own computer. Nothing was sent"
    " automatically: the manager reviewed this text, saved it as a file, and"
    " decides who receives it. It holds only the feedback below, never the"
    " workspace's records, its name, or the manager's name.\n\n"
    "The privacy screen checked every item. It catches identifiers such as"
    " record numbers, dates of birth, phone numbers, and email addresses. It"
    " does not detect people's names, and passing it does not mean the text is"
    " free of patient information."
)


class PilotFeedback:
    """The one writer for ``pilot_feedback`` and ``pilot_feedback_exports``."""

    def __init__(self, ws: ManagerWorkspace):
        self.ws = ws

    # -- writes ----------------------------------------------------------

    def add(self, area: str, kind: str, summary: str) -> str:
        if area not in AREAS:
            raise ManagerError(f"unknown part of the app: {area}")
        if kind not in KINDS:
            raise ManagerError(f"unknown feedback kind: {kind}")
        summary = self.ws._require(summary, "your feedback")
        if len(summary) > MAX_PILOT_TEXT:
            raise ManagerError(f"keep the feedback under {MAX_PILOT_TEXT} characters")
        self.ws._screen(feedback=summary)
        feedback_id = new_id("plf")
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO pilot_feedback (id, workspace_id, area, kind, summary, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (feedback_id, self.ws.info.id, area, kind, summary, self.ws.clock()),
            )
            self.ws.store.log(self.ws.info.owner, "create", "pilot_feedback", feedback_id)
        return feedback_id

    def delete(self, feedback_id: str) -> None:
        """Delete an item for good. Its text is gone, including from exports made later."""
        self.ws._require_row("pilot_feedback", feedback_id)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "DELETE FROM pilot_feedback WHERE id = ? AND workspace_id = ?",
                (feedback_id, self.ws.info.id),
            ).rowcount
            if changed != 1:
                raise ManagerError(f"pilot feedback {feedback_id} is not in this workspace")
            self.ws.store.log(self.ws.info.owner, "delete", "pilot_feedback", feedback_id)

    def export(self, reviewed_sha256: str, by: str) -> dict[str, Any]:
        """Make the export the manager reviewed, or refuse and change nothing."""
        if (by or "").strip() != self.ws.info.owner:
            raise ManagerError("only the accountable manager for this workspace can export"
                               " its pilot feedback")
        with self.ws.store.transaction() as db:
            # Rebuilt and checked inside the write lock, so what is recorded as
            # exported is exactly the text returned, with nothing added between.
            preview = self.preview()
            if not preview["items"]:
                raise ManagerError("there is no pilot feedback to export")
            if preview["sha256"] != reviewed_sha256:
                raise ManagerError("the feedback changed since you reviewed it; nothing was"
                                   " exported. Preview it again.")
            if not preview["can_export"]:
                raise CaptureRefused(preview["reason"])
            export_id, now = new_id("plx"), self.ws.clock()
            db.execute(
                "INSERT INTO pilot_feedback_exports (id, workspace_id, items, sha256,"
                " exported_by, exported_at) VALUES (?, ?, ?, ?, ?, ?)",
                (export_id, self.ws.info.id, preview["items"], preview["sha256"],
                 self.ws.info.owner, now),
            )
            db.execute("UPDATE pilot_feedback SET exported_at = ? WHERE workspace_id = ?",
                       (now, self.ws.info.id))
            self.ws.store.log(self.ws.info.owner, "export", "pilot_feedback", export_id)
        return {**preview, "id": export_id, "exported_at": now}

    # -- reads -----------------------------------------------------------

    def items(self) -> list[dict[str, Any]]:
        """Every item, oldest first: the order they are numbered in the export."""
        return [dict(row) for row in self.ws.store.conn.execute(
            "SELECT id, area, kind, summary, created_at, exported_at FROM pilot_feedback"
            " WHERE workspace_id = ? ORDER BY created_at, rowid",
            (self.ws.info.id,),
        )]

    def view(self) -> dict[str, Any]:
        items = self.items()
        last = self.ws.store.conn.execute(
            "SELECT items, exported_at FROM pilot_feedback_exports WHERE workspace_id = ?"
            " ORDER BY exported_at DESC, rowid DESC LIMIT 1",
            (self.ws.info.id,),
        ).fetchone()
        return {
            "sample": self.ws.info.sample,
            "items": list(reversed(items)),
            "not_yet_exported": sum(1 for i in items if i["exported_at"] is None),
            "last_export": dict(last) if last else None,
            "areas": [{"value": k, "label": v} for k, v in AREAS.items()],
            "kinds": [{"value": k, "label": v} for k, v in KINDS.items()],
        }

    def preview(self) -> dict[str, Any]:
        """Exactly what an export would hold, and whether it may be made. Sends nothing."""
        with self.ws.store.snapshot():
            items = self.items()
            today = self.ws.local_today()
        text = _render(items, today, sample=self.ws.info.sample)
        blocked: list[str] = []
        entity_types: set[str] = set()
        for number, item in enumerate(items, start=1):
            found = {f.entity_type for f in self.ws.privacy.analyze(item["summary"])}
            if found:
                blocked.append(f"item {number} ({', '.join(sorted(found))})")
                entity_types |= found
        entity_types |= {f.entity_type for f in self.ws.privacy.analyze(text)}
        if not items:
            reason = "There is no pilot feedback to export yet."
        elif entity_types:
            where = "; ".join(blocked) if blocked else "the export text"
            reason = ("The privacy screen found identifying details in " + where
                      + ". Delete that feedback and write it again without them.")
        else:
            reason = ""
        return {
            "text": text,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "items": len(items),
            "filename": f"nurse-ai-os-pilot-feedback-{today}.md",
            "can_export": bool(items) and not entity_types,
            "reason": reason,
            "findings": sorted(entity_types),
        }


def _local_day(timestamp: str) -> str:
    return datetime.fromisoformat(timestamp).astimezone().date().isoformat()


def _render(items: list[dict[str, Any]], today: str, *, sample: bool) -> str:
    lines = [
        "# Nurse AI OS pilot feedback",
        "",
        f"- App version: {__version__}",
        f"- Workspace: {'the synthetic sample' if sample else 'the manager’s own'}",
        f"- Prepared on: {today}",
        f"- Items: {len(items)}",
        "",
        HEADER,
    ]
    for number, item in enumerate(items, start=1):
        lines += [
            "",
            f"## {number}. {AREAS[item['area']]}: {KINDS[item['kind']]}"
            f" ({_local_day(item['created_at'])})",
            "",
            item["summary"],
        ]
    return "\n".join(lines) + "\n"


def pilot_item(ws: ManagerWorkspace, feedback_id: str) -> dict[str, Any]:
    ws._require_row("pilot_feedback", feedback_id)
    return next(i for i in PilotFeedback(ws).items() if i["id"] == feedback_id)


__all__ = ["AREAS", "KINDS", "PilotFeedback", "pilot_item"]
