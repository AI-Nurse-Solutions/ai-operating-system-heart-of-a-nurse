-- Nurse AI OS Manager Edition — scoped memory (build step 5.2).
--
-- What the manager asks the assistant to remember: written by the manager
-- only (the assistant never adds to it), for the whole workspace or one
-- project, with its provenance and an optional expiry. The manager can see
-- all of it, correct it, exclude it (kept, never sent), and delete it.
-- A deleted memory is gone: its text is not kept anywhere, and the audit
-- log records only that it was deleted.

CREATE TABLE memories (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT REFERENCES projects(id),
    content      TEXT NOT NULL CHECK (length(trim(content)) > 0),
    provenance   TEXT NOT NULL CHECK (length(trim(provenance)) > 0),
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'excluded')),
    expires_on   TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE INDEX idx_memories_workspace ON memories(workspace_id, status)
