-- Nurse AI OS Manager Edition — the policy version behind each decision (step 2.12).
--
-- An action's decision is recorded with the version of the policy that made
-- it, so its evidence names that policy even after the profile or the EDENA
-- engine is upgraded. It is written in the same transaction as the action.
-- Actions recorded before this migration have no row: their evidence says the
-- version is not known rather than guessing the current one.
CREATE TABLE action_policy_versions (
    action_id      TEXT PRIMARY KEY REFERENCES actions(id),
    policy_version TEXT NOT NULL
)
