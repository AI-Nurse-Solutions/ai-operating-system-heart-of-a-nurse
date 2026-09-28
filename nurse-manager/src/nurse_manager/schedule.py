"""The recurring weekly brief (build step 5.1): "runs when this device is awake".

Each week, at a weekday and hour the manager chooses (local time), a
records-only draft of that week's brief is prepared, so it is waiting when
the manager opens the brief. There is no operating-system scheduler: the
running app asks ``run_due`` about once a minute, and once when it starts.
If the computer was off or asleep at the chosen time, the draft is prepared
the next time the app runs that week. Earlier weeks are never backfilled.

The guarantees the tests hold it to:

* **Off by default.** Nothing runs until the manager turns it on.
* **Records only.** A scheduled run never calls a model and never accepts
  anything; the draft waits for the manager like any other.
* **Once per week.** The week is claimed, the draft written, and the
  outcome recorded in one write transaction, keyed by the week. A crash
  leaves both or neither; a restart, a retry, or a second process cannot
  make a second draft.
* **The manager's own brief wins.** If the week already has a brief, the
  run records that it skipped and changes nothing.
* **Bounded retries.** A failed run is retried after 5 minutes, then 30,
  and gives up after the third attempt, saying so.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from .brief import BriefService
from .services import ManagerError, ManagerWorkspace

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MAX_ATTEMPTS = 3
RETRY_AFTER = (timedelta(minutes=5), timedelta(minutes=30))
DEFAULT_WEEKDAY = 0
DEFAULT_HOUR = 7


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


class BriefSchedule:
    """The one writer for ``brief_schedule`` and ``brief_runs``."""

    def __init__(self, ws: ManagerWorkspace, *, tz=None):
        self.ws = ws
        self.tz = tz  # the computer's local zone unless a test fixes one

    # -- settings ---------------------------------------------------------

    def settings(self) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            "SELECT * FROM brief_schedule WHERE workspace_id = ?", (self.ws.info.id,)
        ).fetchone()
        if row is None:
            return {"enabled": False, "weekday": DEFAULT_WEEKDAY, "hour": DEFAULT_HOUR}
        return {"enabled": bool(row["enabled"]), "weekday": row["weekday"], "hour": row["hour"]}

    def configure(self, *, enabled: bool, weekday: int, hour: int, by: str) -> None:
        """Turn the recurring brief on or off, and choose when. Owner only."""
        if by != self.ws.info.owner:
            raise ManagerError("only the workspace owner can change the recurring brief")
        if not isinstance(weekday, int) or not 0 <= weekday <= 6:
            raise ManagerError("weekday must be 0 (Monday) to 6 (Sunday)")
        if not isinstance(hour, int) or not 0 <= hour <= 23:
            raise ManagerError("hour must be 0 to 23")
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO brief_schedule (workspace_id, enabled, weekday, hour, updated_by,"
                " updated_at) VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (workspace_id) DO UPDATE SET enabled = excluded.enabled,"
                " weekday = excluded.weekday, hour = excluded.hour,"
                " updated_by = excluded.updated_by, updated_at = excluded.updated_at",
                (self.ws.info.id, int(enabled), weekday, hour, by, self.ws.clock()),
            )
            self.ws.store.log(by, "configure", "brief_schedule", self.ws.info.id)

    # -- when -------------------------------------------------------------

    def _now(self) -> datetime:
        """Now on this computer's clock, in its local time zone."""
        return datetime.fromisoformat(self.ws.clock()).astimezone(self.tz)

    def due_at(self, week_of: date, weekday: int, hour: int) -> datetime:
        """The chosen local hour on that day, with that day's own UTC offset,
        so a daylight-saving change between now and then is accounted for."""
        naive = datetime.combine(week_of + timedelta(days=weekday), time(hour))
        return naive.replace(tzinfo=self.tz) if self.tz else naive.astimezone()

    def view(self) -> dict[str, Any]:
        """The schedule as the brief screen shows it: settings, next time, last run."""
        settings = self.settings()
        now = self._now()
        week = monday_of(now.date())
        next_at = None
        if settings["enabled"]:
            at = self.due_at(week, settings["weekday"], settings["hour"])
            run = self._run(week.isoformat())
            if run is not None and run["status"] == "failed" and run["next_attempt_at"]:
                at = datetime.fromisoformat(run["next_attempt_at"]).astimezone(at.tzinfo)
            elif at <= now and run is not None:  # done, skipped, or given up this week
                at = self.due_at(week + timedelta(days=7), settings["weekday"], settings["hour"])
            next_at = at.replace(microsecond=0).isoformat()
        last = self.ws.store.conn.execute(
            "SELECT * FROM brief_runs WHERE workspace_id = ? ORDER BY week_of DESC LIMIT 1",
            (self.ws.info.id,),
        ).fetchone()
        return {**settings, "next_at": next_at, "last_run": _run_dict(last) if last else None}

    # -- running ----------------------------------------------------------

    def _run(self, week_of: str):
        return self.ws.store.conn.execute(
            "SELECT * FROM brief_runs WHERE workspace_id = ? AND week_of = ?",
            (self.ws.info.id, week_of),
        ).fetchone()

    def run_due(self) -> dict[str, Any]:
        """Prepare this week's draft if it is due and not done. Safe to call any time.

        Returns what happened: ``off``, ``not_due``, ``done`` (already
        drafted or skipped this week), ``waiting`` (a retry is not due yet),
        ``gave_up``, or the new run's status.
        """
        settings = self.settings()
        if not settings["enabled"]:
            return _result("off")
        now = self._now()
        week = monday_of(now.date())
        if now < self.due_at(week, settings["weekday"], settings["hour"]):
            return _result("not_due", week.isoformat())
        week_of = week.isoformat()
        stamp = _utc(now)
        try:
            # Claim, draft, and record in one transaction: all of it or none.
            with self.ws.store.transaction() as db:
                run = self._run(week_of)
                if run is not None:
                    if run["status"] != "failed":
                        return _result("done", week_of, run)
                    if run["attempts"] >= MAX_ATTEMPTS:
                        return _result("gave_up", week_of, run)
                    if (run["next_attempt_at"]
                            and datetime.fromisoformat(run["next_attempt_at"]) > now):
                        return _result("waiting", week_of, run)
                attempts = (run["attempts"] if run else 0) + 1
                existing = BriefService(self.ws).weekly(week_of)["current"]
                if existing is not None:
                    status, revision_id = "skipped", existing["revision"]["id"]
                    reason = "This week already has a brief, so nothing was changed."
                else:
                    revision = BriefService(self.ws).draft_weekly_brief(
                        week_of, now.date().isoformat())
                    status, revision_id, reason = "drafted", revision.id, ""
                self._record(db, week_of, status, attempts, revision_id, reason, None, stamp)
                self.ws.store.log("scheduler", status, "brief_run", week_of)
                return _result(status, week_of, self._run(week_of))
        except Exception as exc:  # noqa: BLE001 - any failure is recorded and retried
            return self._failed(week_of, now, exc)

    def _failed(self, week_of: str, now: datetime, exc: Exception) -> dict[str, Any]:
        stamp = _utc(now)
        reason = f"{type(exc).__name__}: {exc}"[:300]
        with self.ws.store.transaction() as db:
            run = self._run(week_of)
            if run is not None and run["status"] != "failed":
                # Another process finished the week meanwhile; its result stands.
                return _result("done", week_of, run)
            attempts = min((run["attempts"] if run else 0) + 1, MAX_ATTEMPTS)
            retry_at = _utc(now + RETRY_AFTER[attempts - 1]) if attempts < MAX_ATTEMPTS else None
            if retry_at is None:
                reason += " — gave up after 3 attempts; draft this week's brief by hand."
            self._record(db, week_of, "failed", attempts, None, reason, retry_at, stamp)
            self.ws.store.log("scheduler", "failed", "brief_run", week_of)
        return _result("failed" if retry_at else "gave_up", week_of, self._run(week_of))

    def _record(self, db, week_of, status, attempts, revision_id, reason, retry_at, stamp):
        db.execute(
            "INSERT INTO brief_runs (workspace_id, week_of, status, attempts, revision_id,"
            " reason, next_attempt_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (workspace_id, week_of) DO UPDATE SET status = excluded.status,"
            " attempts = excluded.attempts, revision_id = excluded.revision_id,"
            " reason = excluded.reason, next_attempt_at = excluded.next_attempt_at,"
            " updated_at = excluded.updated_at",
            (self.ws.info.id, week_of, status, attempts, revision_id, reason, retry_at, stamp),
        )


def _result(outcome: str, week_of: str | None = None, run=None) -> dict[str, Any]:
    return {"outcome": outcome, "week_of": week_of, "run": _run_dict(run) if run else None}


def _utc(moment: datetime) -> str:
    """Stored times are UTC, so a daylight-saving change cannot reorder them."""
    return moment.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _run_dict(row) -> dict[str, Any]:
    return {
        "week_of": row["week_of"],
        "status": row["status"],
        "attempts": row["attempts"],
        "revision_id": row["revision_id"],
        "reason": row["reason"],
        "next_attempt_at": row["next_attempt_at"],
        "at": row["updated_at"],
    }
