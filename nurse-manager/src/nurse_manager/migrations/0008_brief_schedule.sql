-- Nurse AI OS Manager Edition — the recurring weekly brief (build step 5.1).
--
-- A records-only draft of the week's brief, prepared at a time the manager
-- chooses, while Nurse AI OS is open on this computer ("runs when this
-- device is awake"). Off until the manager turns it on. It never calls a
-- model and never accepts anything: the draft waits for the manager.

-- One row per workspace, written only when the manager changes it.
-- weekday is 0 (Monday) to 6 (Sunday); hour is 0 to 23, both in the
-- computer's local time.
CREATE TABLE brief_schedule (
    workspace_id TEXT PRIMARY KEY REFERENCES workspaces(id),
    enabled      INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
    weekday      INTEGER NOT NULL DEFAULT 0 CHECK (weekday BETWEEN 0 AND 6),
    hour         INTEGER NOT NULL DEFAULT 7 CHECK (hour BETWEEN 0 AND 23),
    updated_by   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

-- At most one scheduled run per week (the primary key), whatever restarts,
-- retries, or second processes happen. A run's draft and this row are
-- written in one transaction, so a crash leaves either both or neither.
CREATE TABLE brief_runs (
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    week_of         TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('drafted', 'skipped', 'failed')),
    attempts        INTEGER NOT NULL CHECK (attempts BETWEEN 1 AND 3),
    revision_id     TEXT REFERENCES artifact_revisions(id),
    reason          TEXT NOT NULL DEFAULT '',
    next_attempt_at TEXT,
    updated_at      TEXT NOT NULL,
    PRIMARY KEY (workspace_id, week_of),
    CHECK (status != 'drafted' OR revision_id IS NOT NULL)
)
