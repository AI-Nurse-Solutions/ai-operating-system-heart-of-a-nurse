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
            # A retry carried over from last week ends at this week's time under
            # the settings in force when that time came. Record that before the
            # settings change, so a later hour cannot revive it; turning the
            # recurring brief off ends every pending retry.
            old = self.settings()
            now = self._now()
            stamp = _utc(now)
            week = monday_of(now.date())
            if not enabled:
                for row in db.execute(
                        "SELECT week_of FROM brief_runs WHERE workspace_id = ?"
                        " AND status = 'failed' AND next_attempt_at IS NOT NULL",
                        (self.ws.info.id,)).fetchall():
                    self._end_carried_retry(db, row["week_of"], stamp,
                                            "The recurring brief was turned off.")
            elif old["enabled"] and now >= self.due_at(week, old["weekday"], old["hour"]):
                self._end_carried_retry(db, (week - timedelta(days=7)).isoformat(), stamp)
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
        next_at = None
        if settings["enabled"]:
            now = self._now()
            _week_of, run, state, due = self._choose(settings, now)
            if state in ("waiting", "attempt") and run is not None and run["next_attempt_at"]:
                at = datetime.fromisoformat(run["next_attempt_at"]).astimezone(due.tzinfo)
            elif state == "attempt" and run is not None:
                at = now  # turned back on after a failure: at the next check
            elif state in ("done", "gave_up"):
                # This week is finished, whatever hour is chosen now.
                week = monday_of(now.date())
                at = self.due_at(week + timedelta(days=7), settings["weekday"], settings["hour"])
            else:  # not due yet, or due now
                at = due
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
        if not self.settings()["enabled"]:
            return _result("off")  # the common case, answered without taking the lock
        now = self._now()
        week_of = monday_of(now.date()).isoformat()
        try:
            # Claim, draft, and record in one transaction: all of it or none.
            # Everything that decides the run is read inside the write lock, so
            # a settings change saved while this waited for it governs the run.
            with self.ws.store.transaction() as db:
                settings = self.settings()
                if not settings["enabled"]:
                    return _result("off")
                now = self._now()
                stamp = _utc(now)
                week = monday_of(now.date())
                last_week = (week - timedelta(days=7)).isoformat()
                if (now >= self.due_at(week, settings["weekday"], settings["hour"])
                        or self._run(week.isoformat()) is not None):
                    # This week's turn has come: last week's pending retry ends
                    # here, for good, so moving the hour later cannot revive it.
                    self._end_carried_retry(db, last_week, stamp)
                week_of, run, state, _due = self._choose(settings, now)
                if state != "attempt":
                    return _result(state, week_of, run)
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

    def _choose(self, settings: dict[str, Any], now: datetime):
        """Which week a check acts on, and what to do: one set of rules for
        ``run_due`` and for the next time shown.

        1. This week has a run: its own retry times govern, not the chosen
           hour (a failure at 08:00 retries at 08:05 even if the hour moves
           to 21:00). A finished week is done.
        2. No run yet and this week's time has come: run this week.
        3. Not yet: a retry still pending from last week gets its turn;
           otherwise nothing is due.

        Returns ``(week_of, run, state, due)``; state is ``attempt``,
        ``waiting``, ``done``, ``gave_up``, or ``not_due``.
        """
        week = monday_of(now.date())
        due = self.due_at(week, settings["weekday"], settings["hour"])
        run = self._run(week.isoformat())
        if run is not None:
            return week.isoformat(), run, _state(run, now), due
        if now >= due:
            return week.isoformat(), None, "attempt", due
        last_week = (week - timedelta(days=7)).isoformat()
        carried = self._run(last_week)
        if _retry_pending(carried):
            return last_week, carried, _state(carried, now), due
        return week.isoformat(), None, "not_due", due

    def _end_carried_retry(self, db, week_of: str, stamp: str,
                           why: str = "The week ended before it could be tried again.") -> None:
        run = self._run(week_of)
        if _retry_pending(run):
            db.execute(
                "UPDATE brief_runs SET next_attempt_at = NULL, reason = ?, updated_at = ?"
                " WHERE workspace_id = ? AND week_of = ? AND status = 'failed'",
                (f"{run['reason']} {why}", stamp, self.ws.info.id, week_of),
            )
            self.ws.store.log("scheduler", "expired", "brief_run", week_of)

    def _failed(self, week_of: str, now: datetime, exc: Exception) -> dict[str, Any]:
        stamp = _utc(now)
        reason = f"{type(exc).__name__}: {exc}"[:300]
        with self.ws.store.transaction() as db:
            if not self.settings()["enabled"]:
                return _result("off")  # turned off meanwhile: nothing to retry
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


def _state(run, now: datetime) -> str:
    """What an existing run needs: nothing (done), nothing more (gave up), a
    wait for its retry time, or an attempt now."""
    if run["status"] != "failed":
        return "done"
    if run["attempts"] >= MAX_ATTEMPTS:
        return "gave_up"
    if run["next_attempt_at"] and datetime.fromisoformat(run["next_attempt_at"]) > now:
        return "waiting"
    return "attempt"


def _retry_pending(run) -> bool:
    return (run is not None and run["status"] == "failed" and run["attempts"] < MAX_ATTEMPTS
            and run["next_attempt_at"] is not None)


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
