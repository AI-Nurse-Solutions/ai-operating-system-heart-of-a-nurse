-- Nurse AI OS Manager Edition — Pilot feedback (build step 6.3).
--
-- What a pilot manager writes about the app itself: what worked, a problem,
-- an idea, a question. It is kept in this workspace only. Nothing is sent
-- anywhere: the manager previews exactly what an export holds and saves it
-- as a file they share themselves. The text passes the capture rules like
-- every other record, and the export is screened again before it is made.
--
-- An export keeps its size, its hash, and when it was made, never its text:
-- the text is rebuilt from these rows, and deleting a row deletes it.

CREATE TABLE pilot_feedback (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    area         TEXT NOT NULL CHECK (area IN (
                     'getting_started', 'mission_control', 'weekly_brief', 'projects',
                     'ai_assistance', 'packs', 'other')),
    kind         TEXT NOT NULL CHECK (kind IN ('worked', 'problem', 'idea', 'question')),
    summary      TEXT NOT NULL CHECK (length(trim(summary)) > 0),
    created_at   TEXT NOT NULL,
    exported_at  TEXT
);

CREATE INDEX idx_pilot_feedback_workspace ON pilot_feedback(workspace_id, created_at);

CREATE TABLE pilot_feedback_exports (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    items        INTEGER NOT NULL CHECK (items > 0),
    sha256       TEXT NOT NULL CHECK (length(sha256) = 64),
    exported_by  TEXT NOT NULL,
    exported_at  TEXT NOT NULL
)
