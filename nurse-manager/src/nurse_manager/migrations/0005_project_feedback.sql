-- Nurse AI OS Manager Edition — project feedback (build step 3.5c).
--
-- Feedback about a project's work: what worked, a change asked for, or a
-- question. It is attributed to a group or role, not a named person, and
-- it is never about an individual's performance (that is outside the
-- Personal Manager profile). Text passes the capture rules like every
-- other record. Like task completion, "addressed" needs a written response.

CREATE TABLE project_feedback (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT NOT NULL REFERENCES projects(id),
    from_group   TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('worked', 'change', 'question')),
    summary      TEXT NOT NULL,
    received_on  TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'addressed')),
    response     TEXT NOT NULL DEFAULT '',
    addressed_on TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    CHECK (status != 'addressed' OR length(trim(response)) > 0)
);

CREATE INDEX idx_project_feedback_project ON project_feedback(project_id, status)
