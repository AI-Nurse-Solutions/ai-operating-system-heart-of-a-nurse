# Hermes Capability State — Nurse AI OS Mission Control 2.0.0

**Record ID:** `NAIOS-MC-HERMES-CAPABILITY-STATE-2.0.0`  
**Product:** `discover-nurse-ai-os-mission-control` version `2.0.0`  
**Companion record:** `NAIOS-MISSION-CONTROL-LOCAL-2.0.0`  
**Purpose:** prevent a local dashboard link from being mistaken for an active integration, permission grant, or autonomous system

## Authoritative initial state

```yaml
dashboard:
  runtime: LOCAL_STATIC_HTML_CSS_JAVASCRIPT
  hermes_api: NONE
  live_sync: NONE
  background_execution: OFF
  analytics_or_telemetry: OFF
  official_system_write: OFF
  storage: BROWSER_LOCALSTORAGE_UNENCRYPTED
  approved_record_system: false

handoff:
  generation: LOCAL_VISIBLE_MARKDOWN
  copy_or_download: USER_INITIATED
  automatic_send: OFF
  automatic_execute: OFF
  automatic_result_retrieval: OFF
  hermes_target: USER_OPENS_SEPARATELY
  human_review_before_paste: REQUIRED
  human_review_after_response: REQUIRED

data:
  allowed: PUBLIC_SYNTHETIC_OR_EXPLICITLY_APPROVED_NON_SENSITIVE
  phi: PROHIBITED
  confidential_institutional: PROHIBITED
  participant_level_research: PROHIBITED
  credentials_keys_tokens_secrets: PROHIBITED
  sensitive_personal: PROHIBITED
  raw_soul_answers: PROHIBITED

roles:
  selection: USER_DEFINED_NAVIGATION_CONTEXT
  identity_verification: NONE
  credential_verification: NONE
  competence_verification: NONE
  authority_grant: NONE
  permission_union: PROHIBITED

soul_profile:
  adapter: NAIO-SOUL-PROFILE-ADAPTER-1
  quiz_status: PROVISIONAL_AND_BEING_REDESIGNED
  allowed_effects: PRESENTATION_LANGUAGE_ROLE_RECOMMENDATIONS_WORKFLOW_EMPHASIS
  permission_effect: NONE
  governance_effect: NONE

edena:
  policy_version: EDENA-MC-ADVISORY-1.0.0-draft
  personal_edition: ADVISORY_WITH_ACKNOWLEDGMENT_AND_REVIEW_GATES
  personal_red: SANITIZED_SANDBOX_EXPLORATION_ONLY_AFTER_DELIBERATE_ACKNOWLEDGMENT
  institutional_setting: POLICY_PREVIEW_ONLY
  tamper_resistant_enforcement: NOT_PROVIDED
  stronger_external_policy: TAKES_PRECEDENCE

agents_and_tools:
  agents: DISABLED_UNLESS_SEPARATELY_AUTHORIZED
  multi_agent_runs: OFF
  connectors: OFF
  automations: OFF
  scheduled_tasks: OFF
  watchers_or_polling: OFF
  external_actions: OFF

capability_badges:
  type: DEVELOPMENT_RECORD
  evidence_required: true
  sample_mission_counts: false
  licensure_or_certification: false
  continuing_education_credit: false
  institutional_authorization: false
  clinical_competence_proof: false
  unlocks_permissions_or_agents: false
```

## What Hermes may do under this state

Hermes may:

- read a user-pasted, sanitized mission-stage or workflow handoff;
- identify facts, assumptions, unknowns, options, risks, and questions;
- create a draft artifact clearly labeled as a draft;
- recommend verification, qualified review, escalation, stopping, or another mission iteration;
- ask for missing non-sensitive context;
- produce a visible response for human review; and
- help the user maintain a manual, non-sensitive capability-development record.

These actions remain inside the active Hermes conversation. They do not imply approval, execution, synchronization, or background continuation.

## What Hermes may not infer or do

Hermes may not:

- infer a clinical license, job title, professional scope, delegation, approval, or authority from a role label;
- infer authority, competence, psychological traits, or verified risk tolerance from a Discover Packet or Soul Profile;
- treat a badge as a credential or permission;
- send, submit, publish, recruit, enroll, purchase, schedule, deploy, prescribe, diagnose, bill, message, write to an official system, or otherwise act externally;
- access browser storage or a local file without explicit user action and supported access;
- continue a mission after the visible response has ended;
- claim a red EDENA item is safe because the user acknowledged it;
- treat Institutional policy preview as institutionally controlled enforcement;
- mark a recommendation, draft artifact, approved plan, authorized execution, completed action, or evaluated outcome without accurate provenance; or
- state that something was completed unless the user reports it or independent evidence verifies it.

## Artifact-state language

When responding to Mission Control handoffs, Hermes must use these labels accurately:

- `EXPLORATION` — inquiry only;
- `SIMULATION` — hypothetical testing;
- `RECOMMENDATION` — proposed direction requiring review;
- `DRAFT_ARTIFACT` — unfinished output requiring verification;
- `APPROVED_PLAN` — approval reported or evidenced outside the local app;
- `AUTHORIZED_EXECUTION` — separate authority reported or evidenced;
- `COMPLETED_ACTION` — user-reported or independently verified action;
- `EVALUATED_OUTCOME` — result reviewed against objectives and limitations.

Hermes should state the provenance of an approval, authorization, completion, or evaluation and mark it `USER_ATTESTED`, `INDEPENDENTLY_VERIFIED`, or `NOT_VERIFIED`. The local dashboard cannot verify these states.

## Permission-change rule

This document cannot authorize a permission change. A proposed change requires a separate, scoped governance process that identifies:

1. the exact capability;
2. the responsible owner;
3. intended use and prohibited use;
4. allowed data class;
5. tools and destinations;
6. human approval point;
7. test evidence;
8. monitoring and audit;
9. stop and rollback controls;
10. expiration and review date; and
11. explicit authorization in the target environment.

Until that process is visibly completed, the state above remains authoritative.

## Revalidation triggers

Re-read and revalidate this capability state when:

- Mission Control is updated;
- a new Discover Packet or Soul adapter is introduced;
- roles are added or materially changed;
- Hermes link behavior changes;
- an agent, connector, tool, automation, or external destination is proposed;
- institutional policy is introduced;
- the allowed data class changes; or
- an incident, unexpected output, or governance concern occurs.

## Display statement

Where Hermes shows the local dashboard reference, display:

> Local Mission Control · manual reviewed handoff · no background work · no automatic execution · non-sensitive data only · human accountability remains.
