-- Copyright 2026 Robert Domondon
-- SPDX-License-Identifier: Apache-2.0
-- Preserve every task while extending terminal states. No table references
-- tasks before this migration; the transition history is added afterwards.
CREATE TABLE tasks_before_0014 AS SELECT * FROM tasks;
DROP TABLE tasks;
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    project_id TEXT REFERENCES projects(id),
    title TEXT NOT NULL,
    owner TEXT NOT NULL,
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'idea'
        CHECK (status IN ('idea', 'ready', 'in_progress', 'needs_judgment', 'completed', 'withdrawn')),
    blocked INTEGER NOT NULL DEFAULT 0 CHECK (blocked IN (0, 1)),
    blocked_reason TEXT NOT NULL DEFAULT '',
    paused INTEGER NOT NULL DEFAULT 0 CHECK (paused IN (0, 1)),
    reviewer TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    completion_evidence TEXT NOT NULL DEFAULT '',
    withdrawal_reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (status != 'completed' OR length(trim(completion_evidence)) > 0),
    CHECK (status != 'withdrawn' OR length(trim(withdrawal_reason)) > 0)
);
INSERT INTO tasks (id, workspace_id, project_id, title, owner, due_date, status,
                   blocked, blocked_reason, paused, reviewer, next_action,
                   completion_evidence, created_at, updated_at)
SELECT id, workspace_id, project_id, title, owner, due_date, status,
       blocked, blocked_reason, paused, reviewer, next_action,
       completion_evidence, created_at, updated_at FROM tasks_before_0014;
DROP TABLE tasks_before_0014;
CREATE INDEX idx_tasks_workspace ON tasks(workspace_id, status);

-- Only transitions made after this migration are recorded here. Prior events
-- are preserved without manufacturing historical transitions.
CREATE TABLE task_transitions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    kind TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    previous_evidence TEXT NOT NULL DEFAULT '',
    completion_evidence TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (kind NOT IN ('reopen', 'withdraw') OR length(trim(reason)) > 0)
);
CREATE INDEX idx_task_transitions_task ON task_transitions(workspace_id, task_id);
CREATE TRIGGER task_transitions_no_update BEFORE UPDATE ON task_transitions
BEGIN SELECT RAISE(ABORT, 'task transition history is append-only'); END;
CREATE TRIGGER task_transitions_no_delete BEFORE DELETE ON task_transitions
BEGIN SELECT RAISE(ABORT, 'task transition history is append-only'); END;
