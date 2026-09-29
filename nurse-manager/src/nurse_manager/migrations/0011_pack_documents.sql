-- Nurse AI OS Manager Edition — education, committee, and communication packs (step 5.4).
--
-- A pack is a reviewed, versioned set of document templates. A document the
-- manager starts from one is an artifact like the weekly brief: draft
-- revisions, then acceptance of exactly the text reviewed. So artifacts gain
-- a kind, 'pack_document'. SQLite cannot change a CHECK constraint in place,
-- so the table is rebuilt with every row kept. artifact_revisions refers to
-- it, and foreign keys cannot be switched off inside the migration's
-- transaction, so the rows are copied aside and put back, and the
-- foreign-key check waits for the commit (as in 0010).
PRAGMA defer_foreign_keys = ON;

CREATE TABLE artifacts_before_0011 AS SELECT * FROM artifacts;

DROP TABLE artifacts;

CREATE TABLE artifacts (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT REFERENCES projects(id),
    kind         TEXT NOT NULL CHECK (kind IN ('weekly_brief', 'pack_document')),
    title        TEXT NOT NULL,
    week_of      TEXT,
    created_at   TEXT NOT NULL
);

INSERT INTO artifacts (id, workspace_id, project_id, kind, title, week_of, created_at)
SELECT id, workspace_id, project_id, kind, title, week_of, created_at
FROM artifacts_before_0011;

DROP TABLE artifacts_before_0011;

-- Which pack, at which version, and which template a document came from,
-- with the template's pinned hash: what the manager started from stays
-- known after the pack is updated.
CREATE TABLE pack_documents (
    artifact_id     TEXT PRIMARY KEY REFERENCES artifacts(id),
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    pack_id         TEXT NOT NULL,
    pack_version    TEXT NOT NULL,
    template_id     TEXT NOT NULL,
    template_sha256 TEXT NOT NULL CHECK (length(template_sha256) = 64)
)
