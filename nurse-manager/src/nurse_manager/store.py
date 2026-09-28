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
    return conn


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
        for version, sql in _migrations():
            if version in applied:
                continue
            with self.transaction():
                for statement in _split_sql(sql):
                    self.conn.execute(statement)
                self.conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, self.clock()),
                )

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
            self.conn.execute("ROLLBACK")
            raise
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
        return safety

    def close(self) -> None:
        self.conn.close()


def _split_sql(sql: str) -> list[str]:
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]
