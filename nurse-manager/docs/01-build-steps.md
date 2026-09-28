---
title: Manager Edition build steps
date: 2026-09-28
authorship: Substantially AI-generated (Claude Code) with human review pending
---

# Manager Edition build steps

The Unified Build Path's gates (G0–G7) are split below into steps small
enough for one PR each. **Status** reflects this repository at the
commit that adds this file. "Done" means the step's exit check exists
and passes; it does not mean the gate is passed. Gates are passed by
the human go/no-go the plan requires.

Legend: ✅ done in this PR · 🟡 started · ⬜ not started · ⛔ blocked on a person, an account, or hardware

## G0 — Baseline (NM-001)

| # | Step | Status | Exit check |
|---|---|---|---|
| 0.1 | Reinspect this repo and `florence-x`; run their tests | ✅ | `00-validation-report.md` §1 |
| 0.2 | Verify Hermes Desktop and JEV claims against primary sources | ✅ | Report §2 |
| 0.3 | Record corrections to the plan | ✅ | Report §3 |
| 0.4 | Decide where the manager core lives | 🟡 proposed | ADR 0001, needs steward decision |
| 0.5 | Decide the rule for human-initiated local effects | 🟡 proposed | ADR 0002, needs steward decision |
| 0.6 | Confirm the pilot cohort's OS inventory, **especially Windows 10 vs 11** | ⛔ | Needs managers' machine list |
| 0.7 | Pin the upstream Hermes commit for the spike | ⬜ | Candidate: tag `v2026.9.24` |
| 0.8 | Branding and redistribution review of Hermes (MIT) and notices | ⬜ | `THIRD_PARTY_NOTICES.md` entry |
| 0.9 | Request code-signing identities (Windows, Apple) | ⛔ | Needs the steward's accounts |
| 0.10 | Establish the disposition of the "PR #25 / issue #16" the plan names | ⛔ | Needs `florence-x` API access |

## G1 — Installer and contracts (NM-003, NM-004)

| # | Step | Status | Exit check |
|---|---|---|---|
| 1.1 | Contract map and record-writer register | ✅ | `02-contract-map.md` |
| 1.2 | Initial migration and isolated workspace directory | ✅ | `migrations/0001_initial.sql`; `test_records_and_views.StoreTests` |
| 1.3 | Headless JSON command surface the desktop host will call, with one versioned envelope per command (`nurse-manager-ipc@1`) | ✅ | `nurse_manager.cli`; `CliJourneyTests` |
| 1.4 | Generate TypeScript types from the contract for the renderer | ✅ | `contracts/ipc/`; `test_ipc_contract.py` (stdlib schema check, generated types current) and `test_ipc_contract.mjs` (ajv strict plus `tsc --strict` over every real envelope) |
| 1.5 | Spike: bundle Hermes Desktop with `HERMES_HOME` pointed at a Nurse AI OS data home; confirm no collision with an existing Hermes install | ⬜ | Clean-VM install log |
| 1.6 | Spike: can a desktop plugin add Mission Control as a route? If not, a documented minimal patch set | ⬜ | Spike note plus upstream delta |
| 1.7 | Disable terminal, home-directory discovery, auto-skills, messaging, and background capture in the backend (not just hidden in the UI) | ⬜ | Tests that call the backend directly |
| 1.8 | Clean-machine install; offline first launch; no developer tools needed | ⛔ | Windows 11 and macOS VMs plus signing (0.9) |

## G2 — Durable manager mission (NM-005, NM-006)

| # | Step | Status | Exit check |
|---|---|---|---|
| 2.1 | Project, task, decision, source, and priority records with capture-time data rules | ✅ | `CaptureRuleTests` |
| 2.2 | Board moves cannot complete a task; completion needs evidence (enforced in SQL too) | ✅ | `test_dragging_a_card_cannot_complete_it`, `test_the_database_itself_refuses_completion_without_evidence` |
| 2.3 | Deterministic no-model weekly brief with record citations | ✅ | `BriefTests` |
| 2.4 | Draft → accept bound to the reviewed text hash → new draft on edit | ✅ | `test_acceptance_is_bound_to_the_text_that_was_reviewed`, `test_editing_after_acceptance_starts_a_new_draft` |
| 2.5 | Action boundary: propose → evaluate → approve (bound) → recheck → execute → receipt | ✅ | `ActionBoundaryTests` |
| 2.6 | Denied, blocked, and unknown actions have no effects | ✅ | `test_denied_actions_have_no_effects` |
| 2.7 | Retry never duplicates; interrupted execution is verified, never re-run | ✅ | `test_retry_never_duplicates_the_effect`, reconcile tests |
| 2.8 | Backup and restore never silently discard newer records | ✅ | `test_restore_refuses_to_discard_newer_work` |
| 2.9 | Create → review → save → close → reopen → export | ✅ | `test_create_review_save_close_reopen`, `CliJourneyTests` |
| 2.10 | Concern, containment, and preservation-hold records carried over from the prior plan | ⬜ | Needs the prior plan's definitions (S1 was not available here) |
| 2.11 | Align action records to Florence-X `CandidateAction`/`EDENADecision` via an adapter | ✅ | `test_florence_adapter.py`: pinned JSON Schemas always, Florence-X Pydantic models in the `florence-x-contract` CI job |
| 2.12 | Map receipts and the event log to Florence-X `EvidenceBundle` | ⬜ | Florence-X publishes no JSON Schema for it yet; needs its model or a published schema |

## G3 — Unified manager views (NM-002, NM-007)

| # | Step | Status | Exit check |
|---|---|---|---|
| 3.1 | Read models for Mission Control, board, and table over the same ids | ✅ | `test_same_ids_and_counts_across_views` |
| 3.2 | Honest empty, sample, and unavailable states | ✅ | `test_empty_workspace_states_are_honest` |
| 3.3 | Design tokens with enforced contrast; text-safe orange | ✅ | `test_design_tokens.py` |
| 3.4 | Weekly brief journey spec and synthetic sample week | ✅ | `03-weekly-brief-journey.md`, `samples/synthetic-week.json` |
| 3.5 | Renderer: Mission Control, board, and table pages over the IPC contract | ✅ | `renderer/`; `test_renderer_browser.mjs` (keyboard journey, accessible names, same ids across views, empty and error states, injected markup stays text, 320px reflow, Night Studio, reduced motion, no console or CSP errors); renderer typechecks against the contract |
| 3.5b | Project dashboard page (purpose, owner, milestone, readiness, tasks, resources, decisions, evidence) | ⬜ | Needs a `project` IPC command; next renderer step |
| 3.6 | Library, Learning and Growth, and Contribution views | ⬜ | |
| 3.7 | "Think with this project" composer that shows the context it will send | ⬜ | Depends on G4 |

## G4 — Bounded assistance (NM-009, NM-010)

| # | Step | Status | Exit check |
|---|---|---|---|
| 4.1 | Assistant proposals evaluated by the authoritative EDENA engine at `recommend` | ✅ | `AssistantProposalTests` |
| 4.2 | Hermes adapter behind a replaceable interface; session ↔ mission id map | ⬜ | Adapter contract tests |
| 4.3 | Budgets and cost limit enforced before any provider call | ⬜ | Budget-exhaustion test |
| 4.4 | Provider failure degrades to the no-model path | ⬜ | Timeout and offline tests |
| 4.5 | DecisionAdapter (JEV-shaped), shadow mode on synthetic data only | ⬜ | Labeled set plus shadow report; needs JEV early access |

## G5 — Controlled follow-through (NM-011)

| # | Step | Status | Exit check |
|---|---|---|---|
| 5.1 | Recurring local brief ("runs when this device is awake") | ⬜ | Restart, retry, and dedup tests |
| 5.2 | Scoped memory: inspect, correct, exclude, delete | ⬜ | Reuse `GovernedMemory` |
| 5.3 | "Assistants at work" with stop control | ⬜ | Stop-control test |
| 5.4 | Education, committee, and communication packs | ⬜ | Pack manifests with maintainer and review date |

## G6 — Packaged manager pilot (NM-012)

| # | Step | Status | Exit check |
|---|---|---|---|
| 6.1 | Signed release candidate; manifest pins upstream, policy, schema, and packs | ⛔ | Signing (0.9) |
| 6.2 | Update feed with signature check, pre-migration backup, and forward repair | ⬜ | Uses `Store.backup` and the newer-schema refusal |
| 6.3 | Onboarding, support guide, and pilot feedback | ⬜ | |

## G7 — Managed organization extension

Requires institutional authorization. Out of scope until then.
