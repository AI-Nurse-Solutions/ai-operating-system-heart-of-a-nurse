-- Nurse AI OS Manager Edition — JEV as a classifier (ADR 0006).
--
-- JEV answers typed questions (yes/no, a choice, a score) about text the
-- manager has reviewed. It advises and can only tighten: it never approves
-- anything, never lowers a tier, and never removes a review step.
--
-- Settings: off by default. Each job is switched on separately, and only
-- while JEV is connected. The key is never stored here: it lives in the
-- operating system's credential store (credentials.py), so no backup,
-- export, or copy of this file carries it.
CREATE TABLE classifier_settings (
    workspace_id        TEXT PRIMARY KEY REFERENCES workspaces(id),
    provider            TEXT NOT NULL CHECK (provider IN ('none', 'jev')),
    model               TEXT NOT NULL DEFAULT '',
    job_action_review   INTEGER NOT NULL DEFAULT 0 CHECK (job_action_review IN (0, 1)),
    job_refusal_check   INTEGER NOT NULL DEFAULT 0 CHECK (job_refusal_check IN (0, 1)),
    job_routing         INTEGER NOT NULL DEFAULT 0 CHECK (job_routing IN (0, 1)),
    job_attention       INTEGER NOT NULL DEFAULT 0 CHECK (job_attention IN (0, 1)),
    daily_request_limit INTEGER NOT NULL CHECK (daily_request_limit BETWEEN 0 AND 2000),
    updated_by          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    -- No job runs while JEV is not connected.
    CHECK (provider = 'jev'
           OR job_action_review + job_refusal_check + job_routing + job_attention = 0)
);

-- The ledger: one row per request JEV was asked, or refused before asking.
-- Metadata only: the hash of what was reviewed and sent, the outcome, the
-- result as a fixed key (an option, a category, a route), and a confidence.
-- Never the text. finished_at is NULL while a request is on its way, which
-- is how "Assistants at work" shows it and the stop control can abandon it.
CREATE TABLE classifier_requests (
    id            TEXT PRIMARY KEY,
    workspace_id  TEXT NOT NULL REFERENCES workspaces(id),
    job           TEXT NOT NULL CHECK (job IN (
                      'action_review', 'refusal_check', 'routing', 'attention')),
    provider      TEXT NOT NULL CHECK (provider IN ('jev')),
    model         TEXT NOT NULL,
    state_sha256  TEXT NOT NULL,
    outcome       TEXT NOT NULL CHECK (outcome IN (
                      'answered', 'refused_data_rules', 'refused_policy', 'refused_budget',
                      'refused_stopped', 'provider_failed', 'output_refused', 'stopped')),
    reason        TEXT NOT NULL DEFAULT '',
    result        TEXT NOT NULL DEFAULT '',
    confidence    REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    input_tokens  INTEGER CHECK (input_tokens IS NULL OR input_tokens >= 0),
    requested_by  TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    finished_at   TEXT
);

CREATE INDEX idx_classifier_requests_workspace ON classifier_requests(workspace_id, created_at);

CREATE INDEX idx_classifier_requests_running ON classifier_requests(workspace_id)
    WHERE finished_at IS NULL;

-- JEV's suggestion beside the policy decision for one proposed action.
-- It never changes actions.policy_decision. When JEV is confident its
-- suggestion is stricter than the policy's, hold = 1: the manager must
-- acknowledge the suggestion before the action can be approved. That adds a
-- review step; it removes none.
CREATE TABLE action_classifications (
    action_id        TEXT PRIMARY KEY REFERENCES actions(id),
    workspace_id     TEXT NOT NULL REFERENCES workspaces(id),
    request_id       TEXT NOT NULL UNIQUE REFERENCES classifier_requests(id),
    model            TEXT NOT NULL,
    suggestion       TEXT NOT NULL CHECK (suggestion IN ('allow', 'require_human', 'deny')),
    probabilities    TEXT NOT NULL,
    confidence       REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    core_decision    TEXT NOT NULL CHECK (core_decision IN ('allow', 'require_human', 'deny')),
    hold             INTEGER NOT NULL CHECK (hold IN (0, 1)),
    acknowledged_by  TEXT,
    acknowledged_at  TEXT,
    created_at       TEXT NOT NULL,
    CHECK (hold = 1 OR acknowledged_at IS NULL),
    CHECK ((acknowledged_by IS NULL) = (acknowledged_at IS NULL))
);
