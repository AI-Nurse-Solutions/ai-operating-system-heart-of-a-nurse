"""Weekly manager brief (NM-008): the first integrated mission.

Prepare and review my weekly manager brief — capture priorities, organize
commitments, draft the brief, decide, save the accepted artifact, and
reopen it reliably. This module is the no-model path: the draft is
composed deterministically from workspace records, so the same records
always produce the same brief and every line traces to a record id.

"Draft ready", "Accepted", "Saved", and "Sent" are distinct:

* ``draft_weekly_brief`` saves a *draft* revision. Generation never makes
  content final.
* ``accept`` records the manager's acceptance of one exact revision,
  bound to its text hash. Any later edit is a new draft revision.
* Exporting is an action with a receipt (see ``actions``). Nothing here
  sends anything anywhere.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from ._naio import SYNTHETIC_BANNER
from .services import ManagerError, ManagerWorkspace
from .store import new_id


# Deliberately not the deliverable studio's "AI-generated scaffold" banner:
# this draft was composed from records without a model, and the banner
# must say what actually happened.
BRIEF_DRAFT_BANNER = (
    "> **DRAFT — composed from your workspace records.** Not accepted. Review,"
    " edit, and accept it before it is used anywhere; composing a draft never"
    " makes it final."
)


class StaleRevision(ManagerError):
    """The revision changed after the reviewer saw it."""


@dataclass(frozen=True)
class Revision:
    id: str
    artifact_id: str
    revision_no: int
    body_markdown: str
    body_sha256: str
    status: str
    source_refs: tuple[str, ...]
    created_by: str
    created_at: str
    accepted_by: str | None
    accepted_at: str | None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _window(week_of: str) -> tuple[str, str]:
    start = date.fromisoformat(week_of)
    return start.isoformat(), (start + timedelta(days=6)).isoformat()


def compose_weekly_brief(ws: ManagerWorkspace, week_of: str, today: str) -> tuple[str, list[str]]:
    """Return (markdown, record ids used). Deterministic for fixed records."""
    db = ws.store.conn
    wid = ws.info.id
    start, end = _window(week_of)
    horizon = (date.fromisoformat(end) + timedelta(days=7)).isoformat()
    refs: list[str] = []

    def cite(record_id: str) -> str:
        refs.append(record_id)
        return f"`{record_id}`"

    lines = [f"# Weekly Manager Brief — week of {week_of}", ""]
    lines += [
        f"**Workspace:** {ws.info.name} · **Prepared:** {today} from local records"
        " (no AI model was used for this draft).",
        "",
    ]

    lines += ["## This week's priorities", ""]
    priorities = list(db.execute(
        "SELECT pr.*, p.title AS project_title FROM priorities pr"
        " LEFT JOIN projects p ON p.id = pr.project_id"
        " WHERE pr.workspace_id = ? AND pr.week_of = ? ORDER BY pr.rank",
        (wid, week_of),
    ))
    if priorities:
        for p in priorities:
            project = f" — {p['project_title']} {cite(p['project_id'])}" if p["project_id"] else ""
            lines.append(f"{p['rank']}. {p['text']}{project}")
    else:
        lines.append("_No priorities recorded for this week._")
    lines.append("")

    lines += ["## Decisions made", ""]
    decisions = list(db.execute(
        "SELECT * FROM decisions WHERE workspace_id = ? AND decided_on BETWEEN ? AND ?"
        " ORDER BY decided_on, id",
        (wid, start, end),
    ))
    if decisions:
        for d in decisions:
            why = f" Rationale: {d['rationale']}" if d["rationale"] else ""
            lines.append(
                f"- **{d['question']}** — {d['decision']} (decided by {d['decided_by']},"
                f" {d['decided_on']}) {cite(d['id'])}.{why}"
            )
    else:
        lines.append("_No decisions were recorded this week._")
    lines.append("")

    tasks = [dict(t) for t in db.execute(
        "SELECT t.*, p.title AS project_title FROM tasks t"
        " LEFT JOIN projects p ON p.id = t.project_id WHERE t.workspace_id = ?"
        " ORDER BY t.due_date IS NULL, t.due_date, t.id",
        (wid,),
    )]
    open_tasks = [t for t in tasks if t["status"] != "completed"]

    lines += ["## Blockers", ""]
    blocked = [t for t in open_tasks if t["blocked"]]
    if blocked:
        for t in blocked:
            lines.append(
                f"- {t['title']} (owner: {t['owner']}) — {t['blocked_reason']} {cite(t['id'])}"
            )
    else:
        lines.append("_No open task is marked blocked._")
    lines.append("")

    lines += ["## Needs my judgment", ""]
    judgment = [t for t in open_tasks if t["status"] == "needs_judgment"]
    if judgment:
        for t in judgment:
            lines.append(f"- {t['title']} (owner: {t['owner']}) {cite(t['id'])}")
    else:
        lines.append("_Nothing is waiting on a decision._")
    lines.append("")

    lines += ["## Next steps", ""]
    upcoming = [
        t for t in open_tasks
        if t["due_date"] and t["due_date"] <= horizon and not t["paused"]
    ]
    if upcoming:
        for t in upcoming:
            overdue = " **(overdue)**" if t["due_date"] < today else ""
            action = f" Next: {t['next_action']}." if t["next_action"] else ""
            lines.append(
                f"- {t['due_date']}{overdue} — {t['title']} (owner: {t['owner']})"
                f"{action} {cite(t['id'])}"
            )
    else:
        lines.append("_No open tasks are due in the next two weeks._")
    lines.append("")

    lines += ["## Completed this week", ""]
    done = [t for t in tasks if t["status"] == "completed" and start <= t["updated_at"][:10] <= end]
    if done:
        for t in done:
            lines.append(f"- {t['title']} — evidence: {t['completion_evidence']} {cite(t['id'])}")
    else:
        lines.append("_No tasks were completed with recorded evidence this week._")
    lines.append("")

    lines += ["## Sources", ""]
    sources = list(db.execute(
        "SELECT * FROM sources WHERE workspace_id = ? ORDER BY title, id", (wid,)
    ))
    if sources:
        for s in sources:
            stale = (
                f" **Review overdue since {s['review_date']}.**"
                if s["review_date"] and s["review_date"] < today else ""
            )
            lines.append(f"- {s['title']} — {s['kind']} source: {s['reference']} {cite(s['id'])}{stale}")
    else:
        lines.append("_No sources are linked to this workspace yet._")
    lines.append("")

    lines.append(
        f"_Built from {len(tasks)} task(s), {len(decisions)} decision(s), and"
        f" {len(sources)} source(s) — the same records Mission Control shows._"
    )
    unique_refs = list(dict.fromkeys(refs))
    return "\n".join(lines) + "\n", unique_refs


class BriefService:
    """The one writer for artifacts and artifact revisions."""

    def __init__(self, ws: ManagerWorkspace):
        self.ws = ws

    # -- write path -------------------------------------------------------

    def draft_weekly_brief(self, week_of: str, today: str) -> Revision:
        body, refs = compose_weekly_brief(self.ws, week_of, today)
        artifact = self.ws.store.conn.execute(
            "SELECT * FROM artifacts WHERE workspace_id = ? AND kind = 'weekly_brief'"
            " AND week_of = ?",
            (self.ws.info.id, week_of),
        ).fetchone()
        with self.ws.store.transaction() as db:
            if artifact is None:
                artifact_id = new_id("art")
                db.execute(
                    "INSERT INTO artifacts (id, workspace_id, kind, title, week_of, created_at)"
                    " VALUES (?, ?, 'weekly_brief', ?, ?, ?)",
                    (artifact_id, self.ws.info.id, f"Weekly brief — {week_of}", week_of,
                     self.ws.clock()),
                )
                self.ws.store.log(self.ws.info.owner, "create", "artifact", artifact_id)
            else:
                artifact_id = artifact["id"]
            return self._add_revision(artifact_id, body, refs, self.ws.info.owner)

    def revise(self, artifact_id: str, body_markdown: str, editor: str) -> Revision:
        """A human edit. Always a new draft; an acceptance never follows the text."""
        if not body_markdown.strip():
            raise ManagerError("a revision needs content")
        self._artifact(artifact_id)
        self.ws._screen(body=body_markdown)
        latest = self.latest(artifact_id)
        refs = list(latest.source_refs) if latest else []
        with self.ws.store.transaction():
            return self._add_revision(artifact_id, body_markdown, refs, editor)

    def accept(self, revision_id: str, reviewer: str, seen_sha256: str) -> Revision:
        """The manager accepts exactly the text they reviewed."""
        revision = self.revision(revision_id)
        if reviewer.strip() != self.ws.info.owner:
            raise ManagerError(
                "only the accountable manager for this workspace can accept its outputs"
            )
        if revision.status != "draft":
            raise ManagerError(f"revision is {revision.status}, not a draft awaiting review")
        latest = self.latest(revision.artifact_id)
        if latest is None or latest.id != revision.id:
            raise StaleRevision("a newer revision exists; review that one instead")
        if seen_sha256 != revision.body_sha256:
            raise StaleRevision("the text changed after it was reviewed; review it again")
        now = self.ws.clock()
        with self.ws.store.transaction() as db:
            db.execute(
                "UPDATE artifact_revisions SET status = 'superseded'"
                " WHERE artifact_id = ? AND status = 'accepted'",
                (revision.artifact_id,),
            )
            db.execute(
                "UPDATE artifact_revisions SET status = 'accepted', accepted_by = ?,"
                " accepted_at = ? WHERE id = ?",
                (reviewer.strip(), now, revision_id),
            )
            self.ws.store.log(reviewer.strip(), "accept", "artifact_revision", revision_id)
        return self.revision(revision_id)

    def _add_revision(
        self, artifact_id: str, body: str, refs: list[str], author: str
    ) -> Revision:
        db = self.ws.store.conn
        row = db.execute(
            "SELECT coalesce(max(revision_no), 0) AS n FROM artifact_revisions"
            " WHERE artifact_id = ?",
            (artifact_id,),
        ).fetchone()
        # Older unaccepted drafts are superseded by the new draft; an
        # accepted revision stays accepted until a new one is accepted.
        db.execute(
            "UPDATE artifact_revisions SET status = 'superseded'"
            " WHERE artifact_id = ? AND status = 'draft'",
            (artifact_id,),
        )
        revision_id = new_id("rev")
        db.execute(
            "INSERT INTO artifact_revisions (id, artifact_id, revision_no, body_markdown,"
            " body_sha256, status, source_refs, created_by, created_at)"
            " VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?)",
            (revision_id, artifact_id, row["n"] + 1, body, sha256_text(body),
             json.dumps(refs), author, self.ws.clock()),
        )
        self.ws.store.log(author, "draft", "artifact_revision", revision_id)
        return self.revision(revision_id)

    # -- read path --------------------------------------------------------

    def _artifact(self, artifact_id: str):
        row = self.ws.store.conn.execute(
            "SELECT * FROM artifacts WHERE id = ? AND workspace_id = ?",
            (artifact_id, self.ws.info.id),
        ).fetchone()
        if row is None:
            raise ManagerError(f"artifact {artifact_id} is not in this workspace")
        return row

    def revision(self, revision_id: str) -> Revision:
        row = self.ws.store.conn.execute(
            "SELECT rv.* FROM artifact_revisions rv JOIN artifacts a ON a.id = rv.artifact_id"
            " WHERE rv.id = ? AND a.workspace_id = ?",
            (revision_id, self.ws.info.id),
        ).fetchone()
        if row is None:
            raise ManagerError(f"revision {revision_id} is not in this workspace")
        return _revision(row)

    def latest(self, artifact_id: str) -> Revision | None:
        row = self.ws.store.conn.execute(
            "SELECT * FROM artifact_revisions WHERE artifact_id = ?"
            " ORDER BY revision_no DESC LIMIT 1",
            (artifact_id,),
        ).fetchone()
        return _revision(row) if row else None

    def accepted(self, artifact_id: str) -> Revision | None:
        row = self.ws.store.conn.execute(
            "SELECT * FROM artifact_revisions WHERE artifact_id = ? AND status = 'accepted'",
            (artifact_id,),
        ).fetchone()
        return _revision(row) if row else None

    def history(self, artifact_id: str) -> list[Revision]:
        self._artifact(artifact_id)
        return [
            _revision(row)
            for row in self.ws.store.conn.execute(
                "SELECT * FROM artifact_revisions WHERE artifact_id = ? ORDER BY revision_no",
                (artifact_id,),
            )
        ]

    def render(self, revision: Revision) -> str:
        """The only rendering path. A draft cannot render without its banner."""
        title, _, rest = revision.body_markdown.partition("\n")
        banners: list[str] = []
        if self.ws.info.sample:
            banners.append(SYNTHETIC_BANNER)
        if revision.status == "accepted":
            banners.append(
                f"> **Accepted.** Reviewed and accepted by {revision.accepted_by} on"
                f" {revision.accepted_at} (revision {revision.revision_no},"
                f" sha256 {revision.body_sha256[:12]}). Acceptance was a human decision."
            )
        elif revision.status == "superseded":
            banners.append(
                f"> **Superseded.** Revision {revision.revision_no} is kept for history"
                " and is not the current text."
            )
        else:
            banners.append(BRIEF_DRAFT_BANNER)
        return "\n\n".join([title, *banners, rest.lstrip("\n")])

    def as_dict(self, revision: Revision) -> dict[str, Any]:
        return {
            "id": revision.id,
            "artifact_id": revision.artifact_id,
            "revision_no": revision.revision_no,
            "status": revision.status,
            "sha256": revision.body_sha256,
            "source_refs": list(revision.source_refs),
            "accepted_by": revision.accepted_by,
            "accepted_at": revision.accepted_at,
        }


def _revision(row) -> Revision:
    return Revision(
        id=row["id"],
        artifact_id=row["artifact_id"],
        revision_no=row["revision_no"],
        body_markdown=row["body_markdown"],
        body_sha256=row["body_sha256"],
        status=row["status"],
        source_refs=tuple(json.loads(row["source_refs"])),
        created_by=row["created_by"],
        created_at=row["created_at"],
        accepted_by=row["accepted_by"],
        accepted_at=row["accepted_at"],
    )
