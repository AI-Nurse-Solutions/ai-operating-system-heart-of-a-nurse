-- Nurse AI OS Manager Edition — Learning and Growth (build step 3.6b).
--
-- The manager's own professional learning: courses, reading, conferences,
-- certifications, mentoring. This is the manager's own permitted material
-- (D1); nothing about patients or colleagues belongs here, and the text
-- passes the capture rules like every other record. Completing an item
-- needs a written takeaway and a completion date, enforced here too.

CREATE TABLE learning_items (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    title        TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN (
                     'course', 'reading', 'conference', 'certification', 'mentoring')),
    status       TEXT NOT NULL DEFAULT 'planned'
                 CHECK (status IN ('planned', 'in_progress', 'completed')),
    target_date  TEXT,
    hours        REAL CHECK (hours IS NULL OR (hours >= 0 AND hours <= 500)),
    takeaway     TEXT NOT NULL DEFAULT '',
    completed_on TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    CHECK (status != 'completed'
           OR (length(trim(takeaway)) > 0 AND completed_on IS NOT NULL))
);

CREATE INDEX idx_learning_items_workspace ON learning_items(workspace_id, status)
