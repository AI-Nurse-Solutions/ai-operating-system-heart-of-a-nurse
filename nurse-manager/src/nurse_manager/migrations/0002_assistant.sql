-- Nurse AI OS Manager Edition — bounded assistance (G4, ADR 0004).
--
-- A workspace has no AI provider until its manager connects one. Every
-- provider passes the same gates: the data rules, EDENA at recommend, a
-- budget checked before the request, and output saved only as a draft.

-- One row per workspace, written only when the manager changes a setting.
-- No row means the default: no model. There is no cloud provider value
-- yet, because no cloud service has been chosen (ADR 0004).
CREATE TABLE assistant_settings (
    workspace_id       TEXT PRIMARY KEY REFERENCES workspaces(id),
    provider           TEXT NOT NULL DEFAULT 'none' CHECK (provider IN ('none', 'local')),
    model              TEXT NOT NULL DEFAULT '',
    endpoint           TEXT NOT NULL DEFAULT '',
    monthly_budget_cents INTEGER NOT NULL DEFAULT 0 CHECK (monthly_budget_cents >= 0),
    daily_request_limit  INTEGER NOT NULL DEFAULT 20 CHECK (daily_request_limit BETWEEN 0 AND 500),
    updated_by         TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);

-- Every attempt to use a provider, including the ones the gates stopped.
-- Metadata only: hashes and counts, never the text sent or received.
-- cost_cents stays NULL until the provider replies, so an interrupted
-- request counts at its estimate.
CREATE TABLE assistant_requests (
    id               TEXT PRIMARY KEY,
    workspace_id     TEXT NOT NULL REFERENCES workspaces(id),
    task             TEXT NOT NULL CHECK (task IN ('weekly_brief')),
    provider         TEXT NOT NULL,
    model            TEXT NOT NULL DEFAULT '',
    prompt_sha256    TEXT NOT NULL DEFAULT '',
    outcome          TEXT NOT NULL CHECK (outcome IN (
                         'drafted', 'no_model', 'refused_data_rules', 'refused_policy',
                         'refused_budget', 'provider_failed', 'output_refused')),
    reason           TEXT NOT NULL DEFAULT '',
    estimated_cents  INTEGER NOT NULL DEFAULT 0,
    cost_cents       INTEGER CHECK (cost_cents IS NULL OR cost_cents >= 0),
    revision_id      TEXT REFERENCES artifact_revisions(id),
    requested_by     TEXT NOT NULL,
    created_at       TEXT NOT NULL
);

CREATE INDEX idx_assistant_requests_workspace ON assistant_requests(workspace_id, created_at)
