-- Nurse AI OS Manager Edition — "Assistants at work" and the stop control (step 5.3).
--
-- One switch per workspace stops every assistant at once: nothing new is
-- sent to a model, a request already on its way is abandoned and its reply
-- discarded, and the recurring brief waits. Only the manager turns it on or
-- off. generation goes up with every stop, so a request that began before a
-- stop is recognised even if the manager has let assistants work again
-- since.
CREATE TABLE assistant_control (
    workspace_id TEXT PRIMARY KEY REFERENCES workspaces(id),
    stopped      INTEGER NOT NULL CHECK (stopped IN (0, 1)),
    generation   INTEGER NOT NULL CHECK (generation >= 0),
    changed_by   TEXT NOT NULL,
    changed_at   TEXT NOT NULL
);

-- The request ledger gains two outcomes, and finished_at: NULL while a
-- request is on its way to a model, which is how "Assistants at work"
-- knows what is running. 'stopped' was sent, then abandoned when the
-- manager stopped assistants (it counts against the budget);
-- 'refused_stopped' was never sent. SQLite cannot change a CHECK
-- constraint in place, so the table is rebuilt with every row kept.
--
-- project_notes refers to it, and foreign keys cannot be switched off
-- inside the migration's transaction. So the rows are copied aside, the
-- table is recreated under its own name, and the rows are put back: the
-- foreign-key check waits for the commit, when every note's request is in
-- place again.
PRAGMA defer_foreign_keys = ON;

CREATE TABLE assistant_requests_before_0010 AS SELECT * FROM assistant_requests;

DROP TABLE assistant_requests;

CREATE TABLE assistant_requests (
    id               TEXT PRIMARY KEY,
    workspace_id     TEXT NOT NULL REFERENCES workspaces(id),
    task             TEXT NOT NULL CHECK (task IN ('weekly_brief', 'project_question')),
    provider         TEXT NOT NULL,
    model            TEXT NOT NULL DEFAULT '',
    prompt_sha256    TEXT NOT NULL DEFAULT '',
    outcome          TEXT NOT NULL CHECK (outcome IN (
                         'drafted', 'answered', 'no_model', 'refused_data_rules',
                         'refused_policy', 'refused_budget', 'refused_stopped',
                         'provider_failed', 'output_refused', 'stopped')),
    reason           TEXT NOT NULL DEFAULT '',
    estimated_cents  INTEGER NOT NULL DEFAULT 0,
    cost_cents       INTEGER CHECK (cost_cents IS NULL OR cost_cents >= 0),
    revision_id      TEXT REFERENCES artifact_revisions(id),
    requested_by     TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    output_sha256    TEXT NOT NULL DEFAULT '',
    finished_at      TEXT
);

-- Every earlier request has finished, one way or another.
INSERT INTO assistant_requests (id, workspace_id, task, provider, model, prompt_sha256,
    outcome, reason, estimated_cents, cost_cents, revision_id, requested_by, created_at,
    output_sha256, finished_at)
SELECT id, workspace_id, task, provider, model, prompt_sha256, outcome, reason,
    estimated_cents, cost_cents, revision_id, requested_by, created_at, output_sha256,
    created_at
FROM assistant_requests_before_0010;

DROP TABLE assistant_requests_before_0010;

CREATE INDEX idx_assistant_requests_workspace ON assistant_requests(workspace_id, created_at);

CREATE INDEX idx_assistant_requests_running ON assistant_requests(workspace_id)
    WHERE finished_at IS NULL
