-- Nurse AI OS Manager Edition — questions about one project (build step 3.7b).
--
-- The request ledger gains a task ('project_question') and an outcome
-- ('answered'). SQLite cannot change a CHECK constraint in place, so the
-- table is rebuilt with every existing row kept. The answer itself is
-- never stored: it is shown to the manager as an unsaved suggestion, and
-- the ledger keeps metadata only, as before.

CREATE TABLE assistant_requests_v3 (
    id               TEXT PRIMARY KEY,
    workspace_id     TEXT NOT NULL REFERENCES workspaces(id),
    task             TEXT NOT NULL CHECK (task IN ('weekly_brief', 'project_question')),
    provider         TEXT NOT NULL,
    model            TEXT NOT NULL DEFAULT '',
    prompt_sha256    TEXT NOT NULL DEFAULT '',
    outcome          TEXT NOT NULL CHECK (outcome IN (
                         'drafted', 'answered', 'no_model', 'refused_data_rules',
                         'refused_policy', 'refused_budget', 'provider_failed',
                         'output_refused')),
    reason           TEXT NOT NULL DEFAULT '',
    estimated_cents  INTEGER NOT NULL DEFAULT 0,
    cost_cents       INTEGER CHECK (cost_cents IS NULL OR cost_cents >= 0),
    revision_id      TEXT REFERENCES artifact_revisions(id),
    requested_by     TEXT NOT NULL,
    created_at       TEXT NOT NULL
);

INSERT INTO assistant_requests_v3 (id, workspace_id, task, provider, model, prompt_sha256,
    outcome, reason, estimated_cents, cost_cents, revision_id, requested_by, created_at)
SELECT id, workspace_id, task, provider, model, prompt_sha256, outcome, reason,
    estimated_cents, cost_cents, revision_id, requested_by, created_at
FROM assistant_requests;

DROP TABLE assistant_requests;

ALTER TABLE assistant_requests_v3 RENAME TO assistant_requests;

CREATE INDEX idx_assistant_requests_workspace ON assistant_requests(workspace_id, created_at)
