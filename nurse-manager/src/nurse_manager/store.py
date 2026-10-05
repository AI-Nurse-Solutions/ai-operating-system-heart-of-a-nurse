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
import hashlib
import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from . import resources

MIGRATIONS_DIR = resources.manager_root() / "src" / "nurse_manager" / "migrations"
_EMPTY_HEAD = "0" * 64
_CHECKPOINT_FIELDS = ("format", "legacy_through", "legacy_count", "chained_count",
                      "head_seq", "head_sha256")


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
    conn.create_function("audit_event_sha256", 7, lambda *values: _event_digest(dict(zip(
        ("seq", "at", "actor", "kind", "record_type", "record_id", "previous_sha256"),
        values))), deterministic=True)
    return conn


def _event_digest(row) -> str:
    body = {key: row[key] for key in (
        "seq", "at", "actor", "kind", "record_type", "record_id", "previous_sha256")}
    body["format"] = "nurse-manager-event-v1"
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _audit_report(conn: sqlite3.Connection, checkpoint: dict | None = None) -> dict:
    """Inspect a consistent caller-owned snapshot, optionally against a saved head.

    A privileged editor can rewrite history AND its local head. Only a
    separately retained trusted checkpoint can detect that substitution.
    Legacy content has no retrospective hash guarantee.
    """
    report = {"format": "nurse-manager-audit-v1", "ok": True, "error": "",
              "legacy_through": 0, "legacy_count": 0, "chained_count": 0,
              "head_seq": 0, "head_sha256": _EMPTY_HEAD}
    try:
        rows = conn.execute("SELECT * FROM event_log ORDER BY seq").fetchall()
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(event_log)")}
        if "event_sha256" not in columns:
            report.update(legacy_count=len(rows), legacy_through=rows[-1]["seq"] if rows else 0,
                          head_seq=rows[-1]["seq"] if rows else 0)
        else:
            expected_guards = {}
            for statement in _split_sql((MIGRATIONS_DIR / "0016_event_chain.sql").read_text(encoding="utf-8")):
                if statement.startswith("CREATE TRIGGER "):
                    expected_guards[statement.split()[2]] = " ".join(statement.rstrip(";").split())
            actual_guards = {row["name"]: " ".join(row["sql"].rstrip(";").split())
                             for row in conn.execute("SELECT name,sql FROM sqlite_master"
                                                     " WHERE type='trigger' AND tbl_name='event_log'")}
            if any(actual_guards.get(name) != sql for name, sql in expected_guards.items()):
                raise StoreError("audit append-only guards are missing or changed")
            state = conn.execute("SELECT * FROM audit_chain_state WHERE singleton=1").fetchone()
            if state is None:
                raise StoreError("audit chain state is missing")
            if (any(type(state[key]) is not int or state[key] < 0
                    for key in ("legacy_through", "legacy_count", "head_seq"))
                or state["head_seq"] < state["legacy_through"]
                or not isinstance(state["head_sha256"], str)
                or len(state["head_sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in state["head_sha256"])):
                raise StoreError("audit chain state is malformed")
            report.update(legacy_through=state["legacy_through"], legacy_count=state["legacy_count"])
            previous, sequence, legacy_seen, legacy_last = _EMPTY_HEAD, state["legacy_through"], 0, 0
            for row in rows:
                if row["seq"] <= state["legacy_through"]:
                    if row["event_sha256"] is not None or row["previous_sha256"] is not None:
                        raise StoreError("legacy audit event was relabeled as chained")
                    legacy_seen += 1
                    legacy_last = row["seq"]
                    continue
                if (row["seq"] <= sequence or row["previous_sha256"] != previous
                        or row["event_sha256"] != _event_digest(row)):
                    raise StoreError("audit event link or hash does not match")
                previous, sequence = row["event_sha256"], row["seq"]
                report["chained_count"] += 1
            if legacy_seen != state["legacy_count"] or legacy_last != state["legacy_through"]:
                raise StoreError("legacy audit event count changed")
            if sequence != state["head_seq"] or previous != state["head_sha256"]:
                raise StoreError("audit history does not reach its recorded head")
            report.update(head_seq=sequence, head_sha256=previous)
        if checkpoint is not None and (
            not isinstance(checkpoint, dict)
            or any(checkpoint.get(key) != report[key] for key in _CHECKPOINT_FIELDS)
        ):
            raise StoreError("audit history does not match the retained checkpoint")
    except (sqlite3.Error, StoreError, OSError) as exc:
        report.update(ok=False, error=str(exc) if isinstance(exc, StoreError)
                      else "audit history cannot be read")
    return report


def _checkpoint_path(path: Path) -> Path:
    return Path(str(path) + ".audit.json")


def _head_path(path: Path) -> Path:
    return Path(str(path) + ".audit-head.json")


def _chain_enabled(conn: sqlite3.Connection) -> bool:
    return any(row["name"] == "event_sha256" for row in conn.execute("PRAGMA table_info(event_log)"))


def _point(report: dict) -> dict:
    return {key: report[key] for key in _CHECKPOINT_FIELDS}


def _write_head(path: Path, committed: dict | None, pending: dict | None = None) -> None:
    """Atomic separate-file checkpoint. A pending commit is not a valid anchor."""
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".audit-head-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"format": "nurse-manager-anchor-v1", "committed": committed,
                       "pending": pending}, handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _anchor_report(path: Path, report: dict) -> dict:
    report = dict(report)
    report["anchor_status"] = "not_checked"
    if not report["ok"]:
        return report
    try:
        anchor = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(anchor, dict) or anchor.get("format") != "nurse-manager-anchor-v1":
            raise StoreError("audit anchor is malformed")
        if anchor.get("pending") is not None:
            raise StoreError("audit anchor has an interrupted commit; recovery review is required")
        if anchor.get("committed") != _point(report):
            raise StoreError("audit history does not match its outside anchor")
        report["anchor_status"] = "matched"
    except FileNotFoundError:
        report.update(ok=False, anchor_status="missing", error="audit anchor is missing")
    except (OSError, UnicodeError, ValueError, StoreError) as exc:
        report.update(ok=False, anchor_status="unverified",
                      error=str(exc) if isinstance(exc, StoreError) else "audit anchor cannot be read")
    return report


def _discard_backup(path: Path) -> None:
    path.unlink(missing_ok=True)
    _checkpoint_path(path).unlink(missing_ok=True)


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

    def __init__(self, progressed: bool):
        super().__init__()
        self.progressed = progressed  # whether a step had committed from that copy


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
        try:
            self._migrate()
        except BaseException:
            self.conn.close()  # no Store is returned, so nobody else would close it
            raise

    # -- schema -----------------------------------------------------------

    def _migrate(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations"
            " (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        # An existing workspace is copied before it is upgraded (build step 6.2):
        # records are never migrated without a way back to exactly what they were.
        # Each step takes the write lock and releases it when it commits, so
        # every step first checks that no other copy of the app has committed
        # since the latest copy was taken. If one has, everything is read again
        # and a fresh copy is taken before the next step: every record a step
        # transforms is in a copy as it was before that step. Copies of steps
        # already committed are kept; one no step ran from is discarded (and none
        # is taken if what the other copy committed was the upgrade itself).
        stale = 0
        while True:
            try:
                self._migrate_once()
                return
            except _StaleBackup as exc:
                stale = 0 if exc.progressed else stale + 1
                if stale >= _BACKUP_ATTEMPTS:
                    raise StoreError("this workspace kept changing while it was being"
                                     " copied before its upgrade; nothing more was changed."
                                     " Close other copies of the app and try again.") from None

    def _migrate_once(self) -> None:
        # Taken before anything is read, so a commit by another copy of the app
        # at any point after this (even between the read below and the copy) is
        # caught by the check each step makes.
        seen = self._data_version()  # this connection's own commits leave it as is
        applied = {
            row["version"]
            for row in self.conn.execute("SELECT version FROM schema_migrations")
        }
        # A pre-chain database beside a newer retained head may be a rollback,
        # not an upgrade. Only an explicitly checked restore establishes a
        # matching legacy anchor; never replace an unexpected anchor at genesis.
        if not _chain_enabled(self.conn) and _head_path(self.path).exists():
            anchored = _anchor_report(_head_path(self.path), _audit_report(self.conn))
            if not anchored["ok"]:
                raise StoreError("legacy database disagrees with the retained audit anchor: "
                                 + anchored["error"])
        known = [version for version, _ in _migrations()]
        unknown = applied - set(known)
        if unknown:
            # A database written by a newer release must not be opened by an
            # older one: that is how records silently disappear.
            raise StoreError(
                "workspace was written by a newer schema: " + ", ".join(sorted(unknown))
            )
        pending = [version for version in known if version not in applied]
        backup: Path | None = None
        guarded = bool(applied and pending)
        if guarded:
            backup = self._pre_migration_backup(max(applied), pending[-1])
        progressed = False
        for version, sql in _migrations():
            if version in applied:
                continue
            try:
                with self.transaction():
                    if guarded and self._data_version() != seen:
                        raise _StaleBackup(progressed)
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
                progressed = True
            except _StaleBackup:
                if not progressed:
                    _discard_backup(backup)  # no step ran from it
                raise
            except sqlite3.Error as exc:
                if not progressed and backup is not None:
                    # No step ran from this copy, so the workspace is exactly as it
                    # was and the copy restores nothing. Keeping it would leave one
                    # more full copy each time the app retries a failing step.
                    _discard_backup(backup)
                    backup = None
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
        before = None
        prepared = False
        try:
            if _chain_enabled(self.conn):
                before = _audit_report(self.conn)
                anchored = _anchor_report(_head_path(self.path), before)
                if not anchored["ok"]:
                    raise StoreError(anchored["error"])
            yield self.conn
            if _chain_enabled(self.conn):
                after = _audit_report(self.conn)
                if not after["ok"]:
                    raise StoreError(after["error"])
                if before is None or _point(after) != _point(before):
                    _write_head(_head_path(self.path), _point(before) if before else None, _point(after))
                    prepared = True
        except BaseException:
            # SQLite may already have rolled back by itself (a full disk, an I/O
            # error); a second ROLLBACK would then fail and hide the real error.
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK")
            if prepared:
                _write_head(_head_path(self.path), _point(before) if before else None)
            raise
        try:
            self.conn.execute("COMMIT")
        except BaseException:
            # A COMMIT held off by a reader (SQLITE_BUSY) leaves the transaction
            # open and its lock held; roll it back so nothing half-done stays
            # visible on this connection and the lock is released.
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK")
            if prepared:
                _write_head(_head_path(self.path), _point(before) if before else None)
            raise
        if prepared:
            # If this final atomic write fails, the pending anchor remains and
            # subsequent gated writes fail closed. Do not silently bless a head.
            _write_head(_head_path(self.path), _point(after))

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
        with self.transaction() as conn:
            report = _audit_report(conn)
            if not report["ok"]:
                raise StoreError(report["error"])
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(event_log)")}
            if "event_sha256" not in columns:
                # Used only while testing/opening a genuinely older schema.
                conn.execute("INSERT INTO event_log (at,actor,kind,record_type,record_id)"
                             " VALUES (?,?,?,?,?)", (self.clock(), actor, kind, record_type, record_id))
                return
            counter = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='event_log'").fetchone()
            sequence = max(report["head_seq"], counter[0] if counter else 0) + 1
            row = dict(seq=sequence, at=self.clock(), actor=actor, kind=kind,
                       record_type=record_type, record_id=record_id,
                       previous_sha256=report["head_sha256"])
            conn.execute("INSERT INTO event_log (seq,at,actor,kind,record_type,record_id,"
                         "previous_sha256,event_sha256) VALUES (?,?,?,?,?,?,?,?)",
                         (*row.values(), _event_digest(row)))
            after = _audit_report(conn)
            if not after["ok"] or after["head_seq"] != sequence:
                raise StoreError("audit append did not produce a verified head")

    def verify_events(self, checkpoint: dict | None = None) -> dict:
        with self.snapshot() as conn:
            report = _audit_report(conn, checkpoint)
            if checkpoint is not None:
                return dict(report, anchor_status="matched" if report["ok"] else "unverified")
            if not _chain_enabled(conn) and not _head_path(self.path).exists():
                return dict(report, anchor_status="legacy_unchained")
            return _anchor_report(_head_path(self.path), report)

    def events(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM event_log ORDER BY seq"))

    # -- backup and restore -----------------------------------------------

    def backup(self, dest: Path) -> Path:
        if self.conn.in_transaction:
            raise StoreError("finish the current record transaction before backing up")
        report = self.verify_events()
        if not report["ok"]:
            raise StoreError("backup refused: " + report["error"])
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        sidecar = _checkpoint_path(dest)
        if dest.exists() or sidecar.exists():
            raise StoreError(f"backup target already exists: {dest}")
        # Reserve ownership before creating the SQLite copy. Do not overwrite
        # a concurrently created backup or someone else's checkpoint.
        dest.touch(exist_ok=False)
        target = None
        owns_sidecar = False
        try:
            target = _connect(dest)
            self.conn.backup(target)
            report = _audit_report(target)
            if not report["ok"]:
                raise StoreError("backup audit verification failed: " + report["error"])
            if _chain_enabled(target) or _head_path(self.path).exists():
                anchored = _anchor_report(_head_path(self.path), report)
                if not anchored["ok"]:
                    raise StoreError("backup did not match the retained audit anchor; retry when"
                                     " the workspace is stable: " + anchored["error"])
            with sidecar.open("x", encoding="utf-8") as handle:
                owns_sidecar = True
                json.dump({key: report[key] for key in _CHECKPOINT_FIELDS}, handle,
                          sort_keys=True, separators=(",", ":"))
                handle.write("\n")
        except BaseException:
            # A copy that failed partway (a full disk, say) is not a backup;
            # leaving it would invite restoring from it.
            if target is not None:
                target.close()
            dest.unlink(missing_ok=True)
            if owns_sidecar:
                sidecar.unlink(missing_ok=True)
            raise
        target.close()
        return dest

    def restore(self, src: Path, *, allow_discarding_newer: bool = False) -> Path:
        if self.conn.in_transaction:
            raise StoreError("finish the current record change before restoring")
        if Path(src).resolve() == self.path.resolve():
            raise StoreError("restore requires a separate backup file")
        # SQLite backup cannot write a destination in an open transaction.
        # Exclusive locking mode retains the lock after COMMIT, ordering the
        # safety copy and replacement against all other SQLite writers.
        original_mode = self.conn.execute("PRAGMA locking_mode").fetchone()[0]
        self.conn.execute("PRAGMA locking_mode=EXCLUSIVE")
        try:
            self.conn.execute("BEGIN EXCLUSIVE")
            self.conn.execute("COMMIT")
            return self._restore_locked(src, allow_discarding_newer=allow_discarding_newer)
        finally:
            if self.conn.in_transaction:
                self.conn.execute("ROLLBACK")
            self.conn.execute(f"PRAGMA locking_mode={original_mode}")
            # A transaction end releases the retained lock after returning to
            # normal mode, including on refused/failed restores.
            self.conn.execute("BEGIN")
            self.conn.execute("SELECT 1 FROM schema_migrations LIMIT 1").fetchone()
            self.conn.execute("COMMIT")

    def _restore_locked(self, src: Path, *, allow_discarding_newer: bool = False) -> Path:
        """Replace the live database with ``src``; returns the pre-restore backup."""
        src = Path(src)
        if not src.is_file():
            raise StoreError(f"backup not found: {src}")
        source = _connect(src)
        try:
            # Every source check and the copy must observe one snapshot.
            source.execute("BEGIN")
            check = source.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise StoreError("backup failed its integrity check; nothing was restored")
            versions = {
                row[0] for row in source.execute("SELECT version FROM schema_migrations")
            }
            known = {version for version, _ in _migrations()}
            if not versions or versions - known:
                raise StoreError("backup schema is not one this release can open")
            columns = {row["name"] for row in source.execute("PRAGMA table_info(event_log)")}
            sidecar = _checkpoint_path(src)
            checkpoint = None
            if sidecar.exists():
                try:
                    checkpoint = json.loads(sidecar.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, ValueError) as exc:
                    raise StoreError("backup audit checkpoint cannot be read; nothing was restored") from exc
                if (not isinstance(checkpoint, dict)
                    or any(type(checkpoint.get(key)) is not int or checkpoint[key] < 0
                           for key in ("legacy_through", "legacy_count", "chained_count", "head_seq"))
                    or checkpoint.get("format") != "nurse-manager-audit-v1"
                    or not isinstance(checkpoint.get("head_sha256"), str)):
                    raise StoreError("backup audit checkpoint is malformed; nothing was restored")
            elif "event_sha256" in columns:
                raise StoreError("backup audit checkpoint is missing; nothing was restored")
            # Hold the source snapshot through verification AND copying.
            report = _audit_report(source, checkpoint)
            if not report["ok"]:
                raise StoreError("backup audit verification failed; nothing was restored: " + report["error"])
            fingerprint = "SELECT seq, at, kind, record_type, record_id FROM event_log"
            backup_events = {tuple(row) for row in source.execute(fingerprint)}
            live_events = {tuple(row) for row in self.conn.execute(fingerprint)}
            newer = len(live_events - backup_events)
            if newer and not allow_discarding_newer:
                raise RestoreRefused(newer)
            stamp = self.clock().replace(":", "").replace("+", "Z")
            safety = self.path.parent / "backups" / f"pre-restore-{stamp}-{uuid.uuid4().hex[:6]}.sqlite"
            self.backup(safety)
            prior = _point(_audit_report(self.conn))
            _write_head(_head_path(self.path), prior, _point(report))
            source.backup(self.conn)
            _write_head(_head_path(self.path), _point(report))
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
    # Trigger bodies and quoted strings can contain semicolons. Use SQLite's
    # parser to find boundaries; executescript would commit our transaction.
    statements, pending = [], ""
    for character in "\n".join(lines):
        pending += character
        if character == ";" and sqlite3.complete_statement(pending):
            statements.append(pending.strip())
            pending = ""
    if pending.strip():
        statements.append(pending.strip())
    return statements
