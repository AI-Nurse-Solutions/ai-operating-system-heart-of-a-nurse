"""Local transactional record store (NM-005).

SQLite behind one small port. A later managed database binding must
implement the same service contracts rather than become a second core.

Two rules are structural here:

* Migrations are ordered, recorded, and applied inside a transaction —
  a half-applied schema never opens.
* Restore never silently loses work. Before a backup replaces the live
  database, every audit event in the live database that the backup does
  not contain is counted; if any exist, restore refuses unless the caller
  explicitly accepts discarding them. A pre-restore backup is always
  taken first, so even an accepted discard is recoverable.
"""

from __future__ import annotations

import contextlib
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from . import resources

MIGRATIONS_DIR = resources.manager_root() / "src" / "nurse_manager" / "migrations"


class StoreError(RuntimeError):
    pass


class RestoreRefused(StoreError):
    """Restoring would discard records created after the backup."""

    def __init__(self, newer_events: int):
        super().__init__(
            f"restore refused: the live workspace holds {newer_events} change(s)"
            " that the backup does not contain. Restoring would discard them."
            " Export or back up the current workspace first, or restore with"
            " explicit permission to discard newer changes."
        )
        self.newer_events = newer_events


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _migrations() -> list[tuple[str, str]]:
    return [
        (path.stem, path.read_text(encoding="utf-8"))
        for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    ]


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Deleted or overwritten text is zeroed in the file, not just unlinked:
    # a deleted memory must not survive in free pages (step 5.2).
    conn.execute("PRAGMA secure_delete = ON")
    return conn


class MigrationFailed(StoreError):
    """An upgrade step failed. The workspace stays at the last step that
    finished; it is repaired forward by a release with a corrected step."""

    def __init__(self, version: str, reached: str, backup: Path | None, cause: Exception):
        self.version, self.reached, self.backup = version, reached, backup
        where = f" A copy from before the upgrade is at {backup}." if backup else ""
        super().__init__(
            f"upgrading this workspace stopped at step {version} ({type(cause).__name__})."
            f" Your records are intact at step {reached or 'none'}.{where}"
            " Install a release that corrects this step; never an older one.")


class UpgradeInterrupted(StoreError):
    """An upgrade step could not run for a reason outside it: the workspace
    was busy, the disk was full, or it could not be written. Try again."""

    _PLAIN = {"SQLITE_BUSY": "another copy of the app is using this workspace",
              "SQLITE_LOCKED": "another copy of the app is using this workspace",
              "SQLITE_FULL": "the disk is full",
              "SQLITE_READONLY": "the workspace cannot be written to",
              "SQLITE_CANTOPEN": "the workspace file could not be opened",
              "SQLITE_NOMEM": "the computer ran out of memory"}

    def __init__(self, version: str, reached: str, backup: Path | None, cause: Exception):
        self.version, self.reached, self.backup = version, reached, backup
        name = getattr(cause, "sqlite_errorname", "")
        reason = next((text for code, text in self._PLAIN.items() if name.startswith(code)),
                      "the workspace could not be read or written")
        where = f" A copy from before the upgrade is at {backup}." if backup else ""
        super().__init__(
            f"this workspace could not be upgraded just now: {reason}. Nothing of step"
            f" {version} was kept, and your records are intact at step {reached or 'none'}.{where}"
            " Close other copies of the app, make sure there is free disk space, and try again.")


_BACKUP_ATTEMPTS = 3


class _StaleBackup(Exception):
    """Another copy of the app wrote after the pre-upgrade copy was taken."""


# Errors that say the step could not run here and now, not that it is wrong.
_ENVIRONMENTAL = ("SQLITE_BUSY", "SQLITE_LOCKED", "SQLITE_FULL", "SQLITE_IOERR",
                  "SQLITE_READONLY", "SQLITE_CANTOPEN", "SQLITE_NOMEM", "SQLITE_INTERRUPT",
                  "SQLITE_PROTOCOL", "SQLITE_NOLFS")


def _environmental(exc: sqlite3.Error) -> bool:
    return getattr(exc, "sqlite_errorname", "").startswith(_ENVIRONMENTAL)


class Store:
    """One workspace database file. Records live outside the app bundle."""

    def __init__(self, path: Path, clock: Callable[[], str] = utc_now):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.conn = _connect(self.path)
        self._migrate()

    # -- schema -----------------------------------------------------------

    def _migrate(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations"
            " (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {
            row["version"]
            for row in self.conn.execute("SELECT version FROM schema_migrations")
        }
        known = [version for version, _ in _migrations()]
        unknown = applied - set(known)
        if unknown:
            # A database written by a newer release must not be opened by an
            # older one: that is how records silently disappear.
            raise StoreError(
                "workspace was written by a newer schema: " + ", ".join(sorted(unknown))
            )
        pending = [version for version in known if version not in applied]
        # An existing workspace is copied before it is upgraded (build step 6.2):
        # records are never migrated without a way back to exactly what they were.
        # The copy is taken just before the first step's write lock; if another
        # copy of the app commits in between, it is taken again, so it always
        # holds everything the upgrade starts from.
        backup: Path | None = None
        unverified = bool(applied and pending)
        seen = 0
        for version, sql in _migrations():
            if version in applied:
                continue
            for _attempt in range(_BACKUP_ATTEMPTS):
                if unverified and backup is None:
                    seen = self._data_version()
                    backup = self._pre_migration_backup(max(applied), pending[-1])
                try:
                    with self.transaction():
                        if unverified and self._data_version() != seen:
                            raise _StaleBackup
                        unverified = False
                        # Checked again inside the write lock: another process opening
                        # the same workspace (the app's scheduler during onboarding, say)
                        # may have applied it since the read above.
                        if not self.conn.execute(
                                "SELECT 1 FROM schema_migrations WHERE version = ?",
                                (version,)).fetchone():
                            for statement in _split_sql(sql):
                                self.conn.execute(statement)
                            self.conn.execute(
                                "INSERT INTO schema_migrations (version, applied_at)"
                                " VALUES (?, ?)", (version, self.clock()))
                    break
                except _StaleBackup:
                    backup.unlink(missing_ok=True)
                    backup = None
                except sqlite3.Error as exc:
                    if _environmental(exc):
                        # Busy, full, or unwritable: nothing is wrong with the step,
                        # and nothing of it was kept. Trying again is the remedy.
                        raise UpgradeInterrupted(version, self.schema_version, backup,
                                                 exc) from exc
                    # Forward repair: each step is its own transaction, so the
                    # workspace stays at the last step that finished, intact. It is
                    # never downgraded; a release with a corrected step continues
                    # from here, and the backup holds the records as they were.
                    raise MigrationFailed(version, self.schema_version, backup, exc) from exc
            else:
                raise StoreError("this workspace kept changing while it was being copied"
                                 " before its upgrade; nothing was changed. Close other copies"
                                 " of the app and try again.")

    def _data_version(self) -> int:
        """Changes only when another connection commits to this workspace."""
        return self.conn.execute("PRAGMA data_version").fetchone()[0]

    def _pre_migration_backup(self, current: str, target: str) -> Path:
        stamp = self.clock().replace(":", "").replace("+", "Z")
        dest = (self.path.parent / "backups"
                / f"pre-migration-{current[:4]}-to-{target[:4]}-{stamp}-{uuid.uuid4().hex[:6]}.sqlite")
        try:
            self.backup(dest)
        except (OSError, sqlite3.Error, StoreError) as exc:
            raise StoreError("this workspace needs upgrading, but a backup could not be made"
                             f" first ({type(exc).__name__}); nothing was changed") from exc
        return dest

    @property
    def schema_version(self) -> str:
        row = self.conn.execute("SELECT max(version) AS v FROM schema_migrations").fetchone()
        return row["v"] or ""

    # -- transactions and audit -------------------------------------------

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        if self.conn.in_transaction:
            yield self.conn
            return
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
        except BaseException:
            # SQLite may already have rolled back by itself (a full disk, an I/O
            # error); a second ROLLBACK would then fail and hide the real error.
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK")
            raise
        self.conn.execute("COMMIT")

    @contextlib.contextmanager
    def snapshot(self) -> Iterator[sqlite3.Connection]:
        """Reads that must agree with each other. A deferred transaction holds
        its shared lock from the first read until it ends, so no other
        connection commits in between. Inside a transaction, that one serves."""
        if self.conn.in_transaction:
            yield self.conn
            return
        self.conn.execute("BEGIN")
        try:
            yield self.conn
        finally:
            self.conn.execute("COMMIT")

    def log(self, actor: str, kind: str, record_type: str, record_id: str) -> None:
        self.conn.execute(
            "INSERT INTO event_log (at, actor, kind, record_type, record_id)"
            " VALUES (?, ?, ?, ?, ?)",
            (self.clock(), actor, kind, record_type, record_id),
        )

    def events(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM event_log ORDER BY seq"))

    # -- backup and restore -----------------------------------------------

    def backup(self, dest: Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise StoreError(f"backup target already exists: {dest}")
        target = sqlite3.connect(str(dest))
        try:
            self.conn.backup(target)
        finally:
            target.close()
        return dest

    def restore(self, src: Path, *, allow_discarding_newer: bool = False) -> Path:
        """Replace the live database with ``src``; returns the pre-restore backup."""
        src = Path(src)
        if not src.is_file():
            raise StoreError(f"backup not found: {src}")
        source = _connect(src)
        try:
            check = source.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise StoreError("backup failed its integrity check; nothing was restored")
            versions = {
                row[0] for row in source.execute("SELECT version FROM schema_migrations")
            }
            known = {version for version, _ in _migrations()}
            if not versions or versions - known:
                raise StoreError("backup schema is not one this release can open")
            fingerprint = "SELECT seq, at, kind, record_type, record_id FROM event_log"
            backup_events = {tuple(row) for row in source.execute(fingerprint)}
            live_events = {tuple(row) for row in self.conn.execute(fingerprint)}
            newer = len(live_events - backup_events)
            if newer and not allow_discarding_newer:
                raise RestoreRefused(newer)
            stamp = self.clock().replace(":", "").replace("+", "Z")
            safety = self.path.parent / "backups" / f"pre-restore-{stamp}-{uuid.uuid4().hex[:6]}.sqlite"
            self.backup(safety)
            source.backup(self.conn)
        finally:
            source.close()
        self.conn.execute("PRAGMA foreign_keys = ON")
        # A backup from an earlier release is brought up to this schema now,
        # not on the next open.
        self._migrate()
        return safety

    def close(self) -> None:
        self.conn.close()


def _split_sql(sql: str) -> list[str]:
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]
