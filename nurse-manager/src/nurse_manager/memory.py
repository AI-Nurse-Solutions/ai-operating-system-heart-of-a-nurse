"""Scoped memory (build step 5.2): what the manager asks the assistant to remember.

This is the Integration Contract's governed memory (``MemoryInterface``,
the same contract ``GovernedMemory`` implements), kept in the workspace
database so it survives a restart. It keeps the contract's rules: a
memory needs consent ("remember") and provenance, has a scope (the whole
workspace or one project), may expire, can be corrected and forgotten, and
can be quarantined, which the screens call **excluded**: kept, never sent.

The Personal Manager profile adds its own:

* **Only the manager writes it.** The assistant never adds to memory; a
  memory is always the manager's own words, with who wrote it and when.
* **Identifiers are refused, not stored redacted.** ``GovernedMemory``
  quarantines a redacted copy; here, as for every other record, the
  capture rules refuse it and nothing is stored.
* **Deleting is final.** The text is removed; the audit log records only
  that a memory was deleted.
* **Used only where it can be seen.** Active, unexpired memories for the
  workspace and for that project go into "Think with this project", each
  with its own citation, and the preview shows exactly that text.
"""

from __future__ import annotations

from typing import Any

from ._naio import VALID_CONSENT, MemoryInterface, MemoryRecord
from .services import ManagerError, ManagerWorkspace, _iso_date
from .store import new_id

MAX_MEMORY_CHARS = 500


class MemoryRefused(ManagerError):
    """A memory request the rules refuse (a ManagerError, so the CLI reports it)."""


class WorkspaceMemory(MemoryInterface):
    """The one writer for ``memories``."""

    def __init__(self, ws: ManagerWorkspace):
        self.ws = ws

    # -- the manager's actions ----------------------------------------------

    def add(self, content: str, *, project_id: str | None = None,
            expires_on: str | None = None) -> str:
        """Remember something the manager wrote, for the workspace or one project."""
        record = MemoryRecord(
            memory_id=new_id("mem"),
            tenant=self.ws.info.id,
            role_scope="any",
            content=content,
            provenance=self._provenance("Written"),
            created_at=self.ws.clock(),
            expires_at=expires_on or None,
            project_scope=project_id or None,
        )
        return self.remember(record, consent="remember").memory_id

    def correct_text(self, memory_id: str, content: str) -> None:
        self.correct(self.ws.info.id, memory_id, content, self._provenance("Corrected"))

    def exclude(self, memory_id: str) -> None:
        """Keep it, but never send it."""
        if not self.quarantine(self.ws.info.id, memory_id, "excluded by the manager"):
            raise MemoryRefused("only a memory in use can be excluded")

    def include(self, memory_id: str) -> None:
        self._require(memory_id)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "UPDATE memories SET status = 'active', updated_at = ?"
                " WHERE id = ? AND workspace_id = ? AND status = 'excluded'",
                (self.ws.clock(), memory_id, self.ws.info.id),
            ).rowcount
            if changed != 1:
                raise MemoryRefused("only an excluded memory can be used again")
            self.ws.store.log(self.ws.info.owner, "include", "memory", memory_id)

    def delete(self, memory_id: str) -> None:
        self._require(memory_id)
        if not self.forget(self.ws.info.id, memory_id):
            raise MemoryRefused("this memory is already deleted")

    # -- MemoryInterface -----------------------------------------------------

    def remember(self, record: MemoryRecord, consent: str) -> MemoryRecord:
        if consent not in VALID_CONSENT:
            raise MemoryRefused(f"unknown consent verb: {consent}")
        if consent != "remember":
            raise MemoryRefused("nothing is remembered without the manager's say-so")
        if record.tenant != self.ws.info.id:
            raise MemoryRefused("a memory belongs to this workspace only")
        if not record.provenance.strip():
            raise MemoryRefused("a memory without provenance is not stored")
        # Governance fields are kept or refused, never silently broadened: a
        # Personal workspace has one person, so a narrower role cannot be
        # enforced here, and a quarantined record stays out of use.
        if record.role_scope != "any":
            raise MemoryRefused("a Personal workspace has one person: a memory is for any role"
                                f" here, so a {record.role_scope!r}-only memory is not stored")
        status = "excluded" if record.quarantined else "active"
        content = self._content(record.content)
        self.ws._require_row("projects", record.project_scope)
        expires = _iso_date(record.expires_at, "the expiry date") if record.expires_at else None
        if expires is not None and expires < self.ws.local_today():
            raise MemoryRefused("the expiry date has already passed")
        self.ws._screen(memory=content)
        now = self.ws.clock()
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO memories (id, workspace_id, project_id, content, provenance,"
                " status, expires_on, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (record.memory_id, self.ws.info.id, record.project_scope, content,
                 record.provenance, status, expires, now, now),
            )
            self.ws.store.log(self.ws.info.owner, "create", "memory", record.memory_id)
        # Return what was stored, not what was asked for: the workspace clock is
        # the authority for when a memory was stored, and the text and expiry
        # are normalized, so the result always matches a later recall().
        return _record(self._require(record.memory_id))

    def recall(self, tenant: str, role: str, query: str) -> tuple[MemoryRecord, ...]:
        """Active, unexpired memories whose text contains ``query``.

        Every stored memory is for any role (``remember`` refuses a narrower
        one), so ``role`` cannot narrow the result further here.
        """
        if tenant != self.ws.info.id:
            return ()
        today = self.ws.local_today()
        return tuple(
            _record(row) for row in self.ws.store.conn.execute(
                "SELECT * FROM memories WHERE workspace_id = ? AND status = 'active'"
                " AND (expires_on IS NULL OR expires_on >= ?) ORDER BY created_at, id",
                (tenant, today))
            if query.lower() in row["content"].lower()
        )

    def forget(self, tenant: str, memory_id: str) -> bool:
        if tenant != self.ws.info.id:
            return False
        with self.ws.store.transaction() as db:
            gone = db.execute("DELETE FROM memories WHERE id = ? AND workspace_id = ?",
                              (memory_id, tenant)).rowcount == 1
            if gone:
                self.ws.store.log(self.ws.info.owner, "delete", "memory", memory_id)
        return gone

    def correct(self, tenant: str, memory_id: str, content: str,
                provenance: str) -> MemoryRecord:
        if tenant != self.ws.info.id:
            raise MemoryRefused("a memory belongs to this workspace only")
        self._require(memory_id)
        content = self._content(content)
        self.ws._screen(memory=content)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "UPDATE memories SET content = ?, provenance = ?, updated_at = ?"
                " WHERE id = ? AND workspace_id = ?",
                (content, provenance, self.ws.clock(), memory_id, tenant),
            ).rowcount
            if changed != 1:
                raise MemoryRefused("this memory was deleted")
            self.ws.store.log(self.ws.info.owner, "correct", "memory", memory_id)
        return _record(self._require(memory_id))

    def quarantine(self, tenant: str, memory_id: str, reason: str) -> bool:
        if tenant != self.ws.info.id or not reason:
            return False
        self._require(memory_id)
        with self.ws.store.transaction() as db:
            changed = db.execute(
                "UPDATE memories SET status = 'excluded', updated_at = ?"
                " WHERE id = ? AND workspace_id = ? AND status = 'active'",
                (self.ws.clock(), memory_id, tenant),
            ).rowcount
            if changed == 1:
                self.ws.store.log(self.ws.info.owner, "exclude", "memory", memory_id)
        return changed == 1

    # -- what the assistant may see -------------------------------------------

    def for_project(self, project_id: str) -> list[dict[str, Any]]:
        """Active, unexpired memories for the whole workspace and for this project."""
        return [m for m in (memory_dict(r) for r in self.ws.store.conn.execute(
            "SELECT m.*, p.title AS project_title FROM memories m"
            " LEFT JOIN projects p ON p.id = m.project_id"
            " WHERE m.workspace_id = ? AND m.status = 'active'"
            " AND (m.project_id IS NULL OR m.project_id = ?)"
            " ORDER BY m.project_id IS NOT NULL, m.created_at, m.id",
            (self.ws.info.id, project_id)))
            if not _expired(m, self.ws.local_today())]

    # -- helpers ----------------------------------------------------------------

    def _provenance(self, verb: str) -> str:
        return f"{verb} by {self.ws.info.owner} on {self.ws.local_today()}"

    def _content(self, content: str) -> str:
        content = " ".join((content or "").split())
        if not content:
            raise MemoryRefused("write what the assistant should remember")
        if len(content) > MAX_MEMORY_CHARS:
            raise MemoryRefused(f"keep a memory under {MAX_MEMORY_CHARS} characters")
        return content

    def _require(self, memory_id: str):
        try:
            return self.ws._require_row("memories", memory_id)
        except ManagerError as exc:
            raise MemoryRefused("this memory is not in this workspace (it may be deleted)") from exc


def _expired(memory: dict[str, Any], today: str) -> bool:
    return bool(memory["expires_on"] and memory["expires_on"] < today)


def _record(row) -> MemoryRecord:
    return MemoryRecord(
        memory_id=row["id"], tenant=row["workspace_id"], role_scope="any",
        content=row["content"], provenance=row["provenance"], created_at=row["created_at"],
        expires_at=row["expires_on"], project_scope=row["project_id"],
        quarantined=row["status"] == "excluded",
    )


def memory_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "content": row["content"],
        "project_id": row["project_id"],
        "project_title": row["project_title"],
        "status": row["status"],
        "provenance": row["provenance"],
        "expires_on": row["expires_on"],
    }


__all__ = ["MemoryRefused", "WorkspaceMemory", "memory_dict"]
