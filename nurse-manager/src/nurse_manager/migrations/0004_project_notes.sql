-- Nurse AI OS Manager Edition — keeping an AI answer as a project note (step 3.7c).
--
-- An answer about a project is not saved unless the manager keeps it.
-- The ledger stores only a hash binding (project, question, answer) when
-- the model answers; keeping a note must present text with that exact
-- hash, so a note is always what the model wrote and the checks passed,
-- never text edited afterwards.

ALTER TABLE assistant_requests ADD COLUMN output_sha256 TEXT NOT NULL DEFAULT '';

CREATE TABLE project_notes (
    id            TEXT PRIMARY KEY,
    workspace_id  TEXT NOT NULL REFERENCES workspaces(id),
    project_id    TEXT NOT NULL REFERENCES projects(id),
    request_id    TEXT NOT NULL UNIQUE REFERENCES assistant_requests(id),
    question      TEXT NOT NULL,
    body_markdown TEXT NOT NULL,
    body_sha256   TEXT NOT NULL,
    source_refs   TEXT NOT NULL DEFAULT '[]',
    written_by    TEXT NOT NULL,
    model         TEXT NOT NULL,
    kept_by       TEXT NOT NULL,
    kept_at       TEXT NOT NULL
);

CREATE INDEX idx_project_notes_project ON project_notes(project_id, kept_at)
