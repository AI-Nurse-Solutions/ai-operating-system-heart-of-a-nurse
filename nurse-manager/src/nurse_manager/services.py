"""Manager domain services (NM-005): the one writer for workspace records.

Views (Mission Control, board, table, brief) read through ``views``; they
never write. Every write here passes the Personal Manager profile's data
rules first:

* Only public, synthetic, and explicitly permitted personal material
  (data classes D0 and D1). Patient information, employee performance
  records, and confidential employer material are outside this profile,
  and choosing a role or acknowledging a warning cannot change that.
* Free text is run through the existing privacy screen at capture. A
  finding refuses the capture — identifiers are not stored "redacted" in
  a personal workspace, they are simply not stored. The screen reduces
  risk; it does not detect names and never certifies content as clean.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ._naio import PrivacyScreen, privacy_screen
from .store import Store, new_id, utc_now

TASK_STATUSES = ("idea", "ready", "in_progress", "needs_judgment", "completed")
SOURCE_KINDS = ("public", "synthetic", "personal_permitted")
PERMITTED_DATA_CLASSES = ("D0", "D1")
FEEDBACK_KINDS = ("worked", "change", "question")
MAX_FEEDBACK_FROM = 80
MAX_FEEDBACK_TEXT = 1000
LEARNING_KINDS = ("course", "reading", "conference", "certification", "mentoring")


class ManagerError(ValueError):
    pass


class CaptureRefused(ManagerError):
    """Content failed the active profile's data rules and was not stored."""


@dataclass(frozen=True)
class WorkspaceInfo:
    id: str
    name: str
    profile: str
    owner: str
    sample: bool


class ManagerWorkspace:
    """Domain commands over one local workspace database."""

    def __init__(
        self,
        root: Path,
        clock: Callable[[], str] = utc_now,
        privacy: PrivacyScreen | None = None,
    ):
        self.root = Path(root)
        self.store = Store(self.root / "workspace.sqlite", clock=clock)
        self.clock = clock
        self.privacy = privacy or privacy_screen()

    # -- workspace --------------------------------------------------------

    def create(self, name: str, owner: str, *, sample: bool = False) -> WorkspaceInfo:
        if self._workspace_row() is not None:
            raise ManagerError("this directory already holds a workspace")
        self._screen(name=name, owner=owner)
        ws_id = new_id("ws")
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO workspaces (id, name, profile, owner, sample, created_at)"
                " VALUES (?, ?, 'personal_manager', ?, ?, ?)",
                (ws_id, name.strip(), owner.strip(), int(sample), self.clock()),
            )
            self.store.log(owner, "create", "workspace", ws_id)
        return self.info

    @property
    def info(self) -> WorkspaceInfo:
        row = self._workspace_row()
        if row is None:
            raise ManagerError("no workspace has been created here yet")
        return WorkspaceInfo(
            id=row["id"],
            name=row["name"],
            profile=row["profile"],
            owner=row["owner"],
            sample=bool(row["sample"]),
        )

    def local_today(self) -> str:
        """Today on this computer's calendar: the day the app shows the manager.

        The workspace clock is UTC; date-only fields (a feedback date, the day
        it was addressed) follow the local day, or "today" would be refused as
        the future in time zones ahead of UTC.
        """
        return datetime.fromisoformat(self.clock()).astimezone().date().isoformat()

    def _workspace_row(self):
        return self.store.conn.execute("SELECT * FROM workspaces").fetchone()

    # -- capture rules ----------------------------------------------------

    def _screen(self, **fields: Any) -> None:
        flagged: dict[str, list[str]] = {}
        for key, value in fields.items():
            if value is None:
                continue
            findings = self.privacy.analyze(str(value))
            if findings:
                flagged[key] = sorted({f.entity_type for f in findings})
        if flagged:
            detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in sorted(flagged.items()))
            raise CaptureRefused(
                "not stored — the Personal Manager profile does not keep identifying"
                f" details ({detail}). Remove them and try again."
            )

    def _require(self, value: str, label: str) -> str:
        if not value or not value.strip():
            raise ManagerError(f"{label} is required")
        return value.strip()

    def _require_row(self, table: str, record_id: str | None):
        if record_id is None:
            return None
        row = self.store.conn.execute(
            f"SELECT * FROM {table} WHERE id = ? AND workspace_id = ?",  # noqa: S608
            (record_id, self.info.id),
        ).fetchone()
        if row is None:
            what = (table[:-1] if table.endswith("s") else table).replace("_", " ")
            raise ManagerError(f"{what} {record_id} is not in this workspace")
        return row

    # -- projects ---------------------------------------------------------

    def add_project(
        self, title: str, purpose: str, owner: str, next_milestone: str = ""
    ) -> str:
        title = self._require(title, "project title")
        purpose = self._require(purpose, "project purpose")
        owner = self._require(owner, "accountable owner")
        self._screen(title=title, purpose=purpose, owner=owner, next_milestone=next_milestone)
        project_id = new_id("prj")
        now = self.clock()
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO projects (id, workspace_id, title, purpose, owner,"
                " next_milestone, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, self.info.id, title, purpose, owner, next_milestone, now, now),
            )
            self.store.log(self.info.owner, "create", "project", project_id)
        return project_id

    # -- tasks ------------------------------------------------------------

    def add_task(
        self,
        title: str,
        owner: str,
        *,
        project_id: str | None = None,
        due_date: str | None = None,
        status: str = "idea",
        reviewer: str = "",
        next_action: str = "",
    ) -> str:
        title = self._require(title, "task title")
        owner = self._require(owner, "task owner")
        if status == "completed":
            raise ManagerError("a new task cannot start completed; use complete_task")
        if status not in TASK_STATUSES:
            raise ManagerError(f"unknown task status: {status}")
        self._require_row("projects", project_id)
        self._screen(title=title, owner=owner, reviewer=reviewer, next_action=next_action)
        task_id = new_id("tsk")
        now = self.clock()
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO tasks (id, workspace_id, project_id, title, owner, due_date,"
                " status, reviewer, next_action, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, self.info.id, project_id, title, owner, due_date, status,
                 reviewer, next_action, now, now),
            )
            self.store.log(self.info.owner, "create", "task", task_id)
        return task_id

    def move_task(self, task_id: str, status: str) -> None:
        """Board moves. Dragging a card can never complete it."""
        if status == "completed":
            raise ManagerError(
                "moving a card cannot complete it; completion needs recorded evidence"
                " (use complete_task)"
            )
        if status not in TASK_STATUSES:
            raise ManagerError(f"unknown task status: {status}")
        self._require_row("tasks", task_id)
        self._update_task(task_id, "move", status=status)

    def set_blocked(self, task_id: str, blocked: bool, reason: str = "") -> None:
        self._require_row("tasks", task_id)
        if blocked:
            reason = self._require(reason, "blocked reason")
            self._screen(reason=reason)
        self._update_task(task_id, "block" if blocked else "unblock",
                          blocked=int(blocked), blocked_reason=reason if blocked else "")

    def set_paused(self, task_id: str, paused: bool) -> None:
        self._require_row("tasks", task_id)
        self._update_task(task_id, "pause" if paused else "resume", paused=int(paused))

    def complete_task(self, task_id: str, evidence: str) -> None:
        evidence = self._require(evidence, "completion evidence")
        self._screen(evidence=evidence)
        self._require_row("tasks", task_id)
        self._update_task(task_id, "complete", status="completed",
                          completion_evidence=evidence, blocked=0, blocked_reason="")

    def _update_task(self, task_id: str, kind: str, **fields: Any) -> None:
        assignments = ", ".join(f"{column} = ?" for column in fields)
        with self.store.transaction() as db:
            db.execute(
                f"UPDATE tasks SET {assignments}, updated_at = ? WHERE id = ?",  # noqa: S608
                (*fields.values(), self.clock(), task_id),
            )
            self.store.log(self.info.owner, kind, "task", task_id)

    # -- sources, decisions, priorities -----------------------------------

    def add_source(
        self,
        title: str,
        kind: str,
        reference: str,
        *,
        data_class: str = "D0",
        project_id: str | None = None,
        review_date: str | None = None,
    ) -> str:
        title = self._require(title, "source title")
        reference = self._require(reference, "source reference")
        if kind not in SOURCE_KINDS:
            raise CaptureRefused(
                f"source kind '{kind}' is outside the Personal Manager profile"
                " (public, synthetic, or explicitly permitted personal material only)"
            )
        if data_class not in PERMITTED_DATA_CLASSES:
            raise CaptureRefused(
                f"data class {data_class} is outside the Personal Manager profile;"
                " confidential employer, workforce, or patient material needs an"
                " administrator-provisioned organization workspace"
            )
        if len(title) > 200 or len(reference) > 500:
            raise ManagerError("keep a source's title under 200 characters and its reference"
                               " under 500")
        if review_date:
            review_date = _iso_date(review_date, "the review date")
        self._require_row("projects", project_id)
        self._screen(title=title, reference=reference)
        source_id = new_id("src")
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO sources (id, workspace_id, project_id, title, kind, reference,"
                " data_class, review_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (source_id, self.info.id, project_id, title, kind, reference, data_class,
                 review_date, self.clock()),
            )
            self.store.log(self.info.owner, "create", "source", source_id)
        return source_id

    def record_decision(
        self,
        question: str,
        decision: str,
        decided_by: str,
        decided_on: str,
        *,
        rationale: str = "",
        project_id: str | None = None,
    ) -> str:
        question = self._require(question, "decision question")
        decision = self._require(decision, "decision")
        decided_by = self._require(decided_by, "decision owner")
        decided_on = self._require(decided_on, "decision date")
        self._require_row("projects", project_id)
        self._screen(question=question, decision=decision, decided_by=decided_by,
                     rationale=rationale)
        decision_id = new_id("dec")
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO decisions (id, workspace_id, project_id, question, decision,"
                " decided_by, decided_on, rationale, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (decision_id, self.info.id, project_id, question, decision, decided_by,
                 decided_on, rationale, self.clock()),
            )
            self.store.log(self.info.owner, "create", "decision", decision_id)
        return decision_id

    def set_priorities(
        self, week_of: str, items: list[str], project_ids: list[str | None] | None = None
    ) -> None:
        """Today's (this week's) three priorities — never more than three."""
        items = [item.strip() for item in items if item and item.strip()]
        if not items:
            raise ManagerError("name at least one priority")
        if len(items) > 3:
            raise ManagerError("choose at most three priorities; the rest can wait")
        project_ids = list(project_ids or [None] * len(items))
        if len(project_ids) != len(items):
            raise ManagerError("project links must match priorities one-to-one")
        for project_id in project_ids:
            self._require_row("projects", project_id)
        self._screen(**{f"priority_{i + 1}": text for i, text in enumerate(items)})
        with self.store.transaction() as db:
            db.execute(
                "DELETE FROM priorities WHERE workspace_id = ? AND week_of = ?",
                (self.info.id, week_of),
            )
            for rank, (text, project_id) in enumerate(zip(items, project_ids), start=1):
                pid = new_id("pri")
                db.execute(
                    "INSERT INTO priorities (id, workspace_id, week_of, rank, text, project_id)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (pid, self.info.id, week_of, rank, text, project_id),
                )
            self.store.log(self.info.owner, "set", "priorities", week_of)

    # -- project feedback -------------------------------------------------

    def add_feedback(self, project_id: str, from_group: str, kind: str, summary: str,
                     received_on: str) -> str:
        """Feedback about a project's work, from a group or role.

        Never about a named person or anyone's performance: that is outside
        the Personal Manager profile. The privacy screen checks the text; it
        cannot detect names, so the screens say the rule plainly.
        """
        self._require_row("projects", project_id)
        from_group = self._require(from_group, "who the feedback came from")
        summary = self._require(summary, "the feedback")
        if kind not in FEEDBACK_KINDS:
            raise ManagerError(f"unknown feedback kind: {kind}")
        if len(from_group) > MAX_FEEDBACK_FROM:
            raise ManagerError(
                f"keep 'from' to a group or role, under {MAX_FEEDBACK_FROM} characters")
        if len(summary) > MAX_FEEDBACK_TEXT:
            raise ManagerError(f"keep the feedback under {MAX_FEEDBACK_TEXT} characters")
        received_on = _iso_date(received_on, "the date it was received")
        if received_on > self.local_today():
            raise ManagerError("feedback cannot be received in the future")
        self._screen(from_group=from_group, feedback=summary)
        feedback_id = new_id("fbk")
        now = self.clock()
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO project_feedback (id, workspace_id, project_id, from_group, kind,"
                " summary, received_on, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (feedback_id, self.info.id, project_id, from_group, kind, summary,
                 received_on, now, now),
            )
            self.store.log(self.info.owner, "create", "feedback", feedback_id)
        return feedback_id

    def address_feedback(self, feedback_id: str, response: str) -> None:
        """Close feedback. Like completing a task, it needs a written response."""
        row = self._require_row("project_feedback", feedback_id)
        if row["status"] == "addressed":
            raise ManagerError("this feedback is already addressed")
        response = self._require(response, "how the feedback was addressed")
        if len(response) > MAX_FEEDBACK_TEXT:
            raise ManagerError(f"keep the response under {MAX_FEEDBACK_TEXT} characters")
        self._screen(response=response)
        with self.store.transaction() as db:
            # Only open feedback changes, decided inside the write transaction:
            # two requests racing to address it cannot both succeed.
            changed = db.execute(
                "UPDATE project_feedback SET status = 'addressed', response = ?,"
                " addressed_on = ?, updated_at = ? WHERE id = ? AND status = 'open'",
                (response, self.local_today(), self.clock(), feedback_id),
            ).rowcount
            if changed != 1:
                raise ManagerError("this feedback is already addressed")
            self.store.log(self.info.owner, "address", "feedback", feedback_id)

    # -- learning and growth ----------------------------------------------

    def add_learning(self, title: str, kind: str, *, target_date: str | None = None,
                     hours: float | None = None) -> str:
        """Plan a piece of the manager's own professional learning."""
        title = self._require(title, "what you plan to learn")
        if kind not in LEARNING_KINDS:
            raise ManagerError(f"unknown learning kind: {kind}")
        if len(title) > 200:
            raise ManagerError("keep the title under 200 characters")
        if target_date:
            target_date = _iso_date(target_date, "the target date")
        hours = _hours(hours)
        self._screen(title=title)
        learning_id = new_id("lrn")
        now = self.clock()
        with self.store.transaction() as db:
            db.execute(
                "INSERT INTO learning_items (id, workspace_id, title, kind, target_date, hours,"
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (learning_id, self.info.id, title, kind, target_date or None, hours, now, now),
            )
            self.store.log(self.info.owner, "create", "learning", learning_id)
        return learning_id

    def start_learning(self, learning_id: str) -> None:
        self._require_row("learning_items", learning_id)
        with self.store.transaction() as db:
            changed = db.execute(
                "UPDATE learning_items SET status = 'in_progress', updated_at = ?"
                " WHERE id = ? AND status = 'planned'",
                (self.clock(), learning_id),
            ).rowcount
            if changed != 1:
                raise ManagerError("only planned learning can be started")
            self.store.log(self.info.owner, "start", "learning", learning_id)

    def complete_learning(self, learning_id: str, takeaway: str, completed_on: str, *,
                          hours: float | None = None) -> None:
        """Completion needs what you took away and when, like a task needs evidence."""
        self._require_row("learning_items", learning_id)
        takeaway = self._require(takeaway, "what you took away")
        if len(takeaway) > 1000:
            raise ManagerError("keep the takeaway under 1000 characters")
        completed_on = _iso_date(completed_on, "the completion date")
        if completed_on > self.local_today():
            raise ManagerError("learning cannot be completed in the future")
        hours = _hours(hours)
        self._screen(takeaway=takeaway)
        with self.store.transaction() as db:
            # Decided inside the write, so two requests cannot both complete it.
            changed = db.execute(
                "UPDATE learning_items SET status = 'completed', takeaway = ?,"
                " completed_on = ?, hours = coalesce(?, hours), updated_at = ?"
                " WHERE id = ? AND status != 'completed'",
                (takeaway, completed_on, hours, self.clock(), learning_id),
            ).rowcount
            if changed != 1:
                raise ManagerError("this learning is already completed")
            self.store.log(self.info.owner, "complete", "learning", learning_id)

    def close(self) -> None:
        self.store.close()


def _hours(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        hours = float(value)
    except (TypeError, ValueError) as exc:
        raise ManagerError("hours must be a number") from exc
    if not 0 <= hours <= 500:
        raise ManagerError("hours must be between 0 and 500")
    return hours


def _iso_date(value: str, label: str) -> str:
    from datetime import date

    try:
        return date.fromisoformat(value.strip()).isoformat()
    except (AttributeError, ValueError) as exc:
        raise ManagerError(f"{label} must be a YYYY-MM-DD date") from exc
