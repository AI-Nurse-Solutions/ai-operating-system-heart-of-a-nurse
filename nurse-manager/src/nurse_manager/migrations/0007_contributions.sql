-- Nurse AI OS Manager Edition — Contributions (build step 3.6c).
--
-- The manager's own verified contributions and who shares the credit: an
-- improvement, teaching, committee work, a presentation, a publication.
-- This is the manager's own permitted material (D1). Credit is shared with
-- a team, group or role, never a ranking of named colleagues, and the text
-- passes the capture rules like every other record. A contribution starts
-- as a draft and counts only once the manager has written the evidence
-- that shows it happened, enforced here too.

CREATE TABLE contributions (
    id            TEXT PRIMARY KEY,
    workspace_id  TEXT NOT NULL REFERENCES workspaces(id),
    project_id    TEXT REFERENCES projects(id),
    title         TEXT NOT NULL,
    kind          TEXT NOT NULL CHECK (kind IN (
                      'improvement', 'teaching', 'committee', 'presentation', 'publication')),
    occurred_on   TEXT NOT NULL,
    my_part       TEXT NOT NULL CHECK (length(trim(my_part)) > 0),
    shared_credit TEXT NOT NULL CHECK (length(trim(shared_credit)) > 0),
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'verified')),
    evidence      TEXT NOT NULL DEFAULT '',
    verified_on   TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    CHECK (status != 'verified'
           OR (length(trim(evidence)) > 0 AND verified_on IS NOT NULL))
);

CREATE INDEX idx_contributions_workspace ON contributions(workspace_id, status)
