---
title: Contract map and record-writer register (NM-003)
date: 2026-09-28
authorship: Substantially AI-generated (Claude Code) with human review pending
---

# Contract map and record-writer register

## 1. The three contract sources

| Source | Language | Where | Status |
|---|---|---|---|
| Florence-X core | Pydantic v2, Python ≥ 3.12 | `florence-x/packages/florence-core/florence_core/schemas/` | Clinical orchestration substrate; Postgres/LangGraph targets |
| Integration Contract v1.0 | stdlib dataclasses, Python 3.11 | `naio-integrations/src/naio_integrations/contract.py` | Working EDENA gateway, Directive v1.1 semantics |
| Manager core (this PR) | SQLite schema + stdlib, Python 3.11 | `nurse-manager/` | Manager records; reuses the Integration Contract |

## 2. Overlapping types

| Concept | Florence-X | Integration Contract | Manager core | Resolution |
|---|---|---|---|---|
| Proposed action | `CandidateAction` (payload **hash**, target, reversible, external_boundary_crossed, evidence_refs) | `GatewayRequest` (carries **content**) | `actions` row (payload hash, destination, purpose, cost limit, expected effect) | Manager rows carry a hash like `CandidateAction`, never content. Adapter maps `effect` → `ActionType`, `destination` → `intended_target`, and `export_markdown` → `external_boundary_crossed=false`. The plan's `ActionIntent` was not found in either repo. |
| Policy decision | `EDENADecision` (allow, allow_with_constraints, require_human, escalate, deny, throttle, contain, stop; `expires_at`) | `PolicyDecision` (allow, deny, require_approval; obligations) | `actions.policy_decision` + `policy_reasons` | Manager uses the Integration Contract's three outcomes. Mapping: `require_approval` ↔ `require_human`. The manager core never produces the other Florence-X outcomes; contain/stop belong to G2 step 2.10. |
| Evidence | `EvidenceBundle` (per workflow run: context hash, model, tool calls, decisions, reviews, citations) | `evidence.py` (claim-to-source traceability, PICO) | `artifact_revisions.source_refs` + `receipts` + `event_log` | These are **two meanings** of "evidence", as the plan warns. Manager uses Florence-X's meaning (run record) for receipts and the event log. `source_refs` is citation traceability. Do not name a manager table `evidence_bundle`. |
| Human review | `HumanReview` | `ReviewRecord` (deliverables) | `approvals` (actions), `accepted_by`/`accepted_at` (revisions) | All bind to a named human. Manager binds approvals to the payload hash, destination, workspace, and revision. |

## 3. Vocabulary mappings

**Data class.** The Personal Manager profile admits D0–D1 only.

| Directive v1.1 | Florence-X | Personal Manager profile |
|---|---|---|
| D0 public/synthetic/de-identified | `public` | admitted |
| D1 personal professional | `internal` (closest) | admitted |
| D2 confidential organizational | `internal` | **refused** |
| D3 regulated (incl. PHI) | `phi_local` / `phi_redacted` | **refused** |
| D4 restricted critical | `restricted` | **refused** |

**Risk tier and presentation label.**

| Directive v1.1 | Florence-X | Presentation (plan) | In the Personal Manager profile |
|---|---|---|---|
| green | green | Green | admitted low-risk local operation |
| yellow | yellow | Yellow | needs specified review |
| orange | orange | **Yellow + "organization approval" badge**, never Green | unreachable: needs an authenticated org |
| red-e | red | Red | unreachable |
| red-p | red_blocked | Red | blocked |

## 4. Florence-X adapter (build steps 2.11 and 2.12)

`src/nurse_manager/florence_adapter.py` turns a manager action into
Florence-X `CandidateAction` and `EDENADecision` dicts. It is a one-way
projection; Florence-X types are never written back into manager tables.

| Manager field | Florence-X field | Rule |
|---|---|---|
| `actions.id` | `action_id` | unchanged |
| workspace + artifact | `workflow_run_id` | `nurse-manager:<workspace>:<artifact>` |
| `origin`/`proposed_by` | `agent_id` | human → `human:workspace-owner:<workspace>`; assistant → `assistant:<role>`. **Names never cross.** |
| — | `requester_role` | `nurse_manager` |
| `effect` | `action_type`, `reversible`, `external_boundary_crossed` | `export_markdown` → `write_record`, reversible, internal; send/post → `send_message`, irreversible, external; publish/upload/delete → `call_api`. Unknown effects raise. |
| `destination` | `intended_target` | `workspace-exports:<file>` |
| workspace profile | `data_classification` | `internal` (D0/D1 mix; the conservative choice) |
| `payload_sha256` | `proposed_payload_hash` | `sha256:<full hex>`; content never crosses |
| revision + `source_refs` | `evidence_refs` | revision id first, then cited record ids |
| `tier` | `risk_hint` / `risk_tier` | green→green, yellow→yellow, red→**red_blocked** |
| `policy_decision` | `decision` | allow→allow, require_approval→require_human, deny→deny |
| `policy_reasons` | `rationale` | reason codes, verbatim |
| `action_policy_versions` (recorded when the action was decided) | `policy_pack_version` | `nurse-manager-personal-profile@v`, plus `+edena-gateway-policy@v` for assistants; the policy in force at the decision, never today's (so an upgrade does not rewrite history). `null` for actions recorded before migration 0012, which did not keep it |

The contract is enforced two ways:

- `contracts/florence-x/` holds unmodified copies of Florence-X's JSON Schemas, pinned by commit and hash. Every test run validates against them.
- The CI job `florence-x-contract` installs Florence-X at the same commit, validates against its Pydantic models (`extra="forbid"`), and checks the pinned copies byte-for-byte.

### Evidence (build step 2.12)

`to_evidence_bundle` turns one action's approval, receipt, and event-log
entries into a Florence-X `EvidenceBundle`; `evidence_bundles` does it for
every action whose effect Florence-X can name. It follows the conventions
Florence-X's own runtime uses when it fills a bundle.

| Manager record | `EvidenceBundle` field | Rule |
|---|---|---|
| action | `bundle_id`, `signal_id`, `workflow_run_id` | `<action>:evidence`, `<action>:proposal`, and the same run id as the `CandidateAction` |
| `payload_sha256` | `context_hash` | `sha256:<hex>`: the content the action acted on, never the content itself |
| the action's `EDENADecision` | `edena_decisions` | exactly one, the same dict `to_edena_decision` returns |
| `approvals` row | `human_reviews` | one `approve` review by `nurse_manager`, reviewer `human:workspace-owner:<workspace>`; the approver must be the owner |
| latest `receipts` row | `tool_calls` | one `ToolCallRecord` once an effect was attempted: `tool_id` is the effect; `executed` only when it succeeded; `output_hash` is the exported file's sha256, also when an interrupted export is confirmed after a restart (for a confirmation recorded by an earlier release without the digest, the digest of the approved content it was confirmed against); `error` is the exception type or `effect_unknown`, never the message (it can hold a path, and so a user name) |
| `actions.status` | `final_action` | denied → `blocked:deny`; awaiting approval → `awaiting_human_review`; approved → `awaiting_execution`; succeeded → the action type (`write_record`); failed → `failed:<type>`; effect unknown → `effect_unknown:<type>`; stale → `blocked:stale_approval` |
| `actions.status` | `incident_flags` | `edena_deny:<action>`, `stale_approval:<action>`, or `effect_unknown:<action>` |
| policy vs. what ran | `deviations_from_edena` | an effect after a denial, or without a required approval; never expected, reported if it happens |
| revision + `source_refs` | `source_citations` | as `evidence_refs` |
| `created_at`, approval, `event_log` `execute`, receipt | `signal_received_at`, `reviewed_at`, `executed_at`, `completed_at` | a denial completes when it is made; a stale approval when it is found stale; pending actions have no `completed_at` |
| last `event_log` entry for the action | `created_at` | so the same records always give the same bundle |
| — | `model_*`, `prompt_template_version`, `agent_versions`, `overrides`, `outcome_feedback` | empty: the action boundary calls no model, and nothing overrides a decision |

Florence-X publishes no JSON Schema for `EvidenceBundle`. Offline, the
tests check the shape against field tables; the `florence-x-contract` job
validates every bundle with Florence-X's own `EvidenceBundle` model and
holds those tables equal to its fields, so they cannot drift.

## 5. Record-writer register

One logical writer per record type. Views never write.

| Record | Table(s) | Sole writer | Readers |
|---|---|---|---|
| Workspace | `workspaces` | `ManagerWorkspace.create` | all |
| Project | `projects` | `ManagerWorkspace.add_project` | views, brief |
| Task | `tasks` | `ManagerWorkspace.add_task/move_task/set_blocked/set_paused/complete_task` | views, brief |
| Source | `sources` | `ManagerWorkspace.add_source` | brief |
| Decision | `decisions` | `ManagerWorkspace.record_decision` | brief |
| Priorities | `priorities` | `ManagerWorkspace.set_priorities` | views, brief |
| Artifact + revisions (weekly briefs and pack documents) | `artifacts`, `artifact_revisions` | `BriefService` (pack documents through `PackService`) | views, actions, Packs |
| Action, approval, receipt | `actions`, `approvals`, `receipts` | `ActionBoundary` | views |
| AI settings | `assistant_settings` | `AssistantService.connect_local/disconnect` (the workspace owner only) | views, assistant |
| AI request ledger (hashes and outcomes, never text; weekly briefs and project questions; unfinished while waiting for a model) | `assistant_requests` | `AssistantService` | assistant (budget, note binding), Mission Control (assistants at work) |
| Project feedback (about the work, from a group or role) | `project_feedback` | `ManagerWorkspace.add_feedback/address_feedback` | project dashboard, assistant (project context) |
| Learning item (the manager's own professional learning) | `learning_items` | `ManagerWorkspace.add_learning/start_learning/complete_learning` | Learning and Growth |
| Contribution (the manager's own, with shared credit and evidence) | `contributions` | `ManagerWorkspace.add_contribution/verify_contribution` | Contributions |
| Recurring brief settings (the owner's choice of weekday and hour; off by default) | `brief_schedule` | `BriefSchedule.configure` (the workspace owner only) | Weekly brief |
| Recurring brief runs (one per week: drafted, skipped, or failed with retries) | `brief_runs` | `BriefSchedule.run_due`, called by the running app | Weekly brief |
| Memory (what the manager asks the assistant to remember; for all work or one project) | `memories` | `WorkspaceMemory` (the Integration Contract's `MemoryInterface`; the workspace owner only) | Memory, assistant (project context) |
| Assistants stopped or working (one switch per workspace; a generation that rises with every stop) | `assistant_control` | `AssistantControl.stop/resume` (the workspace owner only) | Mission Control, assistant, recurring brief |
| Pack document origin (pack, version, and template pin a document started from) | `pack_documents` | `PackService.start` (the workspace owner only) | Packs, document |
| Project note (an AI answer the manager kept, exactly as given) | `project_notes` | `AssistantService.keep_project_note` (the workspace owner only) | project dashboard |
| Audit stream | `event_log` | every writer, via `Store.log`, inside the same transaction | backup/restore |
| Schema | `schema_migrations` | `Store._migrate` | restore |

Not owned here, and to be preserved:

- Mission lifecycle and workflow state are owned by Florence-X once G2 step 2.11 lands.
- Hermes session history is context only, mapped to mission ids.
