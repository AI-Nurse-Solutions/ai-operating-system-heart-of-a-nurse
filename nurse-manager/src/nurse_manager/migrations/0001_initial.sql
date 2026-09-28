-- Nurse AI OS Manager Edition — initial record schema (NM-005).
--
-- One logical writer per record type (see docs/02-contract-map.md). The
-- renderer never writes here; it calls domain services. Every table is
-- workspace-scoped so personal and organizational records cannot merge.

CREATE TABLE workspaces (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    profile      TEXT NOT NULL CHECK (profile IN ('personal_manager')),
    owner        TEXT NOT NULL,
    sample       INTEGER NOT NULL DEFAULT 0 CHECK (sample IN (0, 1)),
    created_at   TEXT NOT NULL
);

CREATE TABLE projects (
    id             TEXT PRIMARY KEY,
    workspace_id   TEXT NOT NULL REFERENCES workspaces(id),
    title          TEXT NOT NULL,
    purpose        TEXT NOT NULL,
    owner          TEXT NOT NULL,
    next_milestone TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active', 'paused', 'completed')),
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE tasks (
    id                  TEXT PRIMARY KEY,
    workspace_id        TEXT NOT NULL REFERENCES workspaces(id),
    project_id          TEXT REFERENCES projects(id),
    title               TEXT NOT NULL,
    owner               TEXT NOT NULL,
    due_date            TEXT,
    status              TEXT NOT NULL DEFAULT 'idea'
                        CHECK (status IN ('idea', 'ready', 'in_progress',
                                          'needs_judgment', 'completed')),
    blocked             INTEGER NOT NULL DEFAULT 0 CHECK (blocked IN (0, 1)),
    blocked_reason      TEXT NOT NULL DEFAULT '',
    paused              INTEGER NOT NULL DEFAULT 0 CHECK (paused IN (0, 1)),
    reviewer            TEXT NOT NULL DEFAULT '',
    next_action         TEXT NOT NULL DEFAULT '',
    completion_evidence TEXT NOT NULL DEFAULT '',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    -- "Completed" requires the defined acceptance evidence.
    CHECK (status != 'completed' OR length(trim(completion_evidence)) > 0)
);

CREATE TABLE sources (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT REFERENCES projects(id),
    title        TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('public', 'synthetic', 'personal_permitted')),
    reference    TEXT NOT NULL,
    data_class   TEXT NOT NULL CHECK (data_class IN ('D0', 'D1')),
    review_date  TEXT,
    created_at   TEXT NOT NULL
);

CREATE TABLE decisions (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT REFERENCES projects(id),
    question     TEXT NOT NULL,
    decision     TEXT NOT NULL,
    decided_by   TEXT NOT NULL,
    decided_on   TEXT NOT NULL,
    rationale    TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL
);

CREATE TABLE priorities (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    week_of      TEXT NOT NULL,
    rank         INTEGER NOT NULL CHECK (rank BETWEEN 1 AND 3),
    text         TEXT NOT NULL,
    project_id   TEXT REFERENCES projects(id),
    UNIQUE (workspace_id, week_of, rank)
);

CREATE TABLE artifacts (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id   TEXT REFERENCES projects(id),
    kind         TEXT NOT NULL CHECK (kind IN ('weekly_brief')),
    title        TEXT NOT NULL,
    week_of      TEXT,
    created_at   TEXT NOT NULL
);

-- Revisions are append-only. An accepted revision is never edited; a
-- change creates a new draft revision and the old acceptance no longer
-- describes the current text.
CREATE TABLE artifact_revisions (
    id            TEXT PRIMARY KEY,
    artifact_id   TEXT NOT NULL REFERENCES artifacts(id),
    revision_no   INTEGER NOT NULL,
    body_markdown TEXT NOT NULL,
    body_sha256   TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('draft', 'accepted', 'superseded')),
    source_refs   TEXT NOT NULL DEFAULT '[]',
    created_by    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    accepted_by   TEXT,
    accepted_at   TEXT,
    UNIQUE (artifact_id, revision_no)
);

CREATE TABLE actions (
    id                   TEXT PRIMARY KEY,
    workspace_id         TEXT NOT NULL REFERENCES workspaces(id),
    origin               TEXT NOT NULL CHECK (origin IN ('human', 'assistant')),
    proposed_by          TEXT NOT NULL,
    effect               TEXT NOT NULL,
    purpose              TEXT NOT NULL,
    artifact_revision_id TEXT REFERENCES artifact_revisions(id),
    payload_sha256       TEXT NOT NULL,
    destination          TEXT NOT NULL,
    cost_limit_cents     INTEGER NOT NULL DEFAULT 0,
    expected_effect      TEXT NOT NULL,
    tier                 TEXT NOT NULL CHECK (tier IN ('green', 'yellow', 'red')),
    policy_decision      TEXT NOT NULL,
    policy_reasons       TEXT NOT NULL DEFAULT '[]',
    status               TEXT NOT NULL CHECK (status IN (
                             'denied', 'awaiting_approval', 'approved', 'executing',
                             'succeeded', 'failed', 'effect_unknown', 'stale')),
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);

-- An approval is bound to the exact payload, destination, actor,
-- workspace, and revision it saw. Any mismatch at execution is stale.
CREATE TABLE approvals (
    id                   TEXT PRIMARY KEY,
    action_id            TEXT NOT NULL UNIQUE REFERENCES actions(id),
    approver             TEXT NOT NULL,
    workspace_id         TEXT NOT NULL REFERENCES workspaces(id),
    artifact_revision_id TEXT,
    payload_sha256       TEXT NOT NULL,
    destination          TEXT NOT NULL,
    approved_at          TEXT NOT NULL
);

CREATE TABLE receipts (
    id          TEXT PRIMARY KEY,
    action_id   TEXT NOT NULL REFERENCES actions(id),
    outcome     TEXT NOT NULL CHECK (outcome IN ('succeeded', 'failed', 'effect_unknown')),
    detail      TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);

-- Metadata-only audit stream: what changed, never the content itself.
CREATE TABLE event_log (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    at          TEXT NOT NULL,
    actor       TEXT NOT NULL,
    kind        TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_id   TEXT NOT NULL
);

CREATE INDEX idx_tasks_workspace ON tasks(workspace_id, status);
CREATE INDEX idx_actions_workspace ON actions(workspace_id, status);
CREATE INDEX idx_revisions_artifact ON artifact_revisions(artifact_id, revision_no);
