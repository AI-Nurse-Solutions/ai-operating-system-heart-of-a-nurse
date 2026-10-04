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
| 0.4 | Decide where the manager core lives | ✅ | ADR 0001, accepted by the steward 2026-09-28 |
| 0.5 | Decide the rule for human-initiated local effects | ✅ | ADR 0002, accepted by the steward 2026-09-28 |
| 0.6 | Confirm the pilot cohort's OS inventory, **especially Windows 10 vs 11** | ✅ superseded | ADR 0003 (local app in the browser) runs on Windows 10 and 11, macOS, and Linux; laptop checks remain part of 1.10 |
| 0.7 | Pin the upstream Hermes commit for the spike | ⏸ deferred | ADR 0003; candidate when resumed: tag `v2026.9.24` |
| 0.8 | Branding and redistribution review of Hermes (MIT) and notices | ✅ | `THIRD_PARTY_NOTICES.md` Hermes Desktop row and §2.1 (referenced, not bundled; step 1.11 obligations); `05-hermes-review.md` (sources read 2026-09-29 at `v2026.9.24`/`f97608f` and main `ee5f49b`); `test_notices.py` |
| 0.9 | Request code-signing identities (Windows, Apple) | ⛔ | Needs the steward's accounts |
| 0.10 | Establish the disposition of the "PR #25 / issue #16" the plan names | ⛔ | Needs `florence-x` API access |

## G1 — Installer and contracts (NM-003, NM-004)

| # | Step | Status | Exit check |
|---|---|---|---|
| 1.1 | Contract map and record-writer register | ✅ | `02-contract-map.md` |
| 1.2 | Initial migration and isolated workspace directory | ✅ | `migrations/0001_initial.sql`; `test_records_and_views.StoreTests` |
| 1.3 | Headless JSON command surface the desktop host will call, with one versioned envelope per command (`nurse-manager-ipc@1`) | ✅ | `nurse_manager.cli`; `CliJourneyTests` |
| 1.4 | Generate TypeScript types from the contract for the renderer | ✅ | `contracts/ipc/`; `test_ipc_contract.py` (stdlib schema check, generated types current) and `test_ipc_contract.mjs` (ajv strict plus `tsc --strict` over every real envelope) |
| 1.5 | Local app (ADR 0003): loopback-only host with a per-launch token, single instance, user-data folder outside the bundle | ✅ | `test_app.py` (token, Host and Origin checks, write allowlist, owner-only lock, quit, idle stop) |
| 1.6 | First-run onboarding: explore the sample or start your own workspace, with the data rules stated first | ✅ | `test_app_browser.mjs` |
| 1.7 | Honest lifetime: "running on this computer", Quit, heartbeat, stop after idle | ✅ | `test_app.py`, `test_app_browser.mjs` |
| 1.8 | Packaged builds for Windows, macOS, and Linux with the Python runtime bundled (unsigned test builds) | ✅ | `nurse-manager-app.yml`: built-in self-test on all three; full browser journey against the packaged Linux build |
| 1.9 | Code signing: Apple Developer ID plus notarization; a Windows signing route | ⛔ | Needs the steward's signing identities (0.9) |
| 1.10 | Clean-machine install on real manager laptops; offline first launch | ⛔ | Needs signed builds (1.9) and a pilot laptop inventory |
| 1.11 | Hermes Desktop host (upstream shell, plugins, `HERMES_HOME`) | ⏸ deferred | ADR 0003: after the pilot. The renderer's `Source` is the seam. |

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
| 2.10 | Concern, containment, and preservation-hold records carried over from the prior plan | ⛔ | Needs the prior plan's definitions (S1 is not in this repository; searched 2026-09-29). A hold can stop deletion, so it is not built on guessed definitions |
| 2.11 | Align action records to Florence-X `CandidateAction`/`EDENADecision` via an adapter | ✅ | `test_florence_adapter.py`: pinned JSON Schemas always, Florence-X Pydantic models in the `florence-x-contract` CI job |
| 2.12 | Map receipts and the event log to Florence-X `EvidenceBundle` | ✅ | `florence_adapter.to_evidence_bundle` / `evidence_bundles`, following Florence-X's runtime conventions (contract map §4). Florence-X publishes no JSON Schema for it, so `test_florence_adapter.py` checks every action state (awaiting, approved, succeeded, failed, denied, stale, effect unknown) against field tables offline, and the `florence-x-contract` job validates the same bundles with Florence-X's own `EvidenceBundle` model at the pinned commit and holds the tables equal to its fields. No names, paths, or content cross; the same records always give the same bundle |

## G3 — Unified manager views (NM-002, NM-007)

| # | Step | Status | Exit check |
|---|---|---|---|
| 3.1 | Read models for Mission Control, board, and table over the same ids | ✅ | `test_same_ids_and_counts_across_views` |
| 3.2 | Honest empty, sample, and unavailable states | ✅ | `test_empty_workspace_states_are_honest` |
| 3.3 | Design tokens with enforced contrast; text-safe orange | ✅ | `test_design_tokens.py` |
| 3.4 | Weekly brief journey spec and synthetic sample week | ✅ | `03-weekly-brief-journey.md`, `samples/synthetic-week.json` |
| 3.5 | Renderer: Mission Control, board, and table pages over the IPC contract | ✅ | `renderer/`; `test_renderer_browser.mjs` (keyboard journey, accessible names, same ids across views, empty and error states, injected markup stays text, 320px reflow, Night Studio, reduced motion, no console or CSP errors); renderer typechecks against the contract |
| 3.5b | Project dashboard page (purpose, owner, milestone, readiness, tasks, resources, decisions, evidence) | ✅ | `project` IPC command and `ProjectDashboard` contract type; `ProjectDashboardTests`; browser journey from Mission Control, by keyboard and back. Readiness is stated facts, never a score or percentage |
| 3.5c | Project feedback on the dashboard: about the work, from a group or role, closed only with a written response | ✅ | Migration `0005` (`project_feedback`, with a database check that "addressed" has a response); `FeedbackTests` (capture rules, dates, kinds, lengths, audit); `feedback-add` / `feedback-address` IPC commands; open feedback in readiness facts and in the "Think with this project" context; browser journeys (add by keyboard, mark addressed, dev host read-only, markup stays text) |
| 3.6a | Library: every source in the workspace, overdue reviews first; add a source through the capture rules | ✅ | `library` and `source-add` IPC commands; `LibraryTests` (same source ids as the dashboards, overdue first, capture rules, review date checked); browser journeys (read-only on the dev host, references stay text, 320px reflow, add by form with an identifier refused first) |
| 3.6b | Learning and Growth: the manager's own learning, planned → in progress → completed with a written takeaway; facts, never a score | ✅ | Migration `0006` (`learning_items`, with a database check that "completed" has a takeaway and a date); `LearningTests` (order, facts, takeaway required, no future completion, decided inside the write, capture rules, audit); `learning*` IPC commands; browser journeys (plan, start, complete by form; read-only on the dev host; no percentages) |
| 3.6c | Contributions: what the manager did, who shares the credit (teams, groups or roles), and the evidence; a draft counts only once verified; facts, never a score or ranking | ✅ | Migration `0007` (`contributions`, with database checks that "my part" and "shared credit" are written and that "verified" has evidence and a date); `ContributionTests` (order, facts, evidence required, no future dates, decided inside the write, capture rules, audit); `contribution*` IPC commands; browser journeys (draft by form with an identifier refused first and the typed text kept, verify with evidence; read-only on the dev host; no percentages) |
| 3.7 | Weekly brief and AI assistance screens: draft from records or with AI, a preview of exactly what will be sent before anything is, review, and accept | ✅ | `assistant-preview` and `weekly` IPC commands; the request is bound to the reviewed preview (`PreviewTests`, `WorkspaceWriteTests`); `test_app_browser.mjs` (no model by default, connect a model on this computer, preview equals what the stand-in model received, AI draft waits for acceptance, 320px reflow); `test_renderer_browser.mjs` (read-only on the dev host, brief text never becomes markup) |
| 3.7b | "Think with this project" on the project dashboard: ask a question, see exactly what would be sent, get an answer that is a suggestion and is never saved | ✅ | `ProjectQuestionTests` (no model, preview equals what is sent, only this project's records, a changed question needs a new preview, identifiers never sent, invented citations not shown, shared daily limit); migration `0003` keeps every ledger row (`test_upgrading_keeps_every_ai_request_already_recorded`); `test_app_browser.mjs` (preview, send, "Not saved" answer); dev host read-only |
| 3.7c | Keep an AI answer as a project note; keeping it is the manager's acceptance | ✅ | Migration `0004` (`project_notes`; the ledger gains an answer hash, never the text); `ProjectNoteTests` (nothing saved until kept; only the exact answer to that question about that project; once, by the owner; unanswered requests refused); `note-keep` IPC command; browser journey keeps an answer and finds it under Notes |

## G4 — Bounded assistance (NM-009, NM-010)

| # | Step | Status | Exit check |
|---|---|---|---|
| 4.1 | Assistant proposals evaluated by the authoritative EDENA engine at `recommend` | ✅ | `AssistantProposalTests` |
| 4.2 | Provider adapter behind a replaceable interface (ADR 0004): no model by default; a model on this computer (Ollama-compatible, loopback only, proxies bypassed, redirects refused) | ✅ | `test_assistant.py` (`DefaultPostureTests`, `SettingsTests`, `LocalDraftTests`) against a stand-in model server over real HTTP; `assistant*` IPC commands in the contract |
| 4.2b | The one cloud AI service | ⛔ | Needs the steward's choice of provider, plus review of its data-use, retention, and pricing terms. The key goes in the OS credential store (ADR 0004) |
| 4.2c | Hermes session ↔ mission id map | ⏸ deferred | With the Hermes host (1.11) |
| 4.3 | Budgets checked before any provider call: a daily request limit and a monthly cost budget; each request recorded before the call | ✅ | `BudgetTests` (limit reached, zero limit, failures count, a paid provider stopped before it is called, an interrupted request still counts) |
| 4.4 | Any gate or provider failure returns the records-only draft and the reason; never another service | ✅ | `FallbackTests` (server down, server error, timeout, adapter bug, output with identifiers, invented citations, empty output, data rules, EDENA) |
| 4.5 | DecisionAdapter (JEV-shaped), shadow mode on synthetic data only | ✅ | `decision_adapter.py`: a JEV "Choice"-shaped interface shadowed against EDENA action decisions. Labeled set `samples/shadow-edena-decisions.json` (24 synthetic proposals, every profile reason, both origins; labels held equal to the policy) and shadow report `samples/shadow-edena-decisions.report.md` (review-always baseline: the floor). `test_decision_adapter.py`: no adapter changes a decision; less-strict suggestions are named case by case; failing or out-of-contract adapters are recorded, not trusted; only the reviewed set, pinned by its sha256, ever reaches an adapter |
| 4.5b | A live JEV adapter in the shadow harness | ✅ | ADR 0006 admits JEV. `JevDecisionAdapter` asks JEV the harness's three options and decides nothing; `tools/shadow_report.py --adapter jev` reads the key on standard input. Only the pinned synthetic set reaches it. `ShadowAdapterTests` runs it against a stand-in JEV over real HTTP |
| 4.5c | Run the shadow harness against the live JEV and review its report | ⛔ | Needs the steward's JEV key (early access). The report's less-strict cases are read before any pilot turns the action review on |
| 4.6 | JEV as an opt-in classifier (ADR 0006): off by default; the manager's own key in the operating system's credential store; data rules, EDENA at `recommend`, a daily request limit, and the stop control before every request; a byte-exact preview bound by hash; a ledger without text; a pinned model | ✅ | Migration `0014` (`classifier_settings`, `classifier_requests`, `action_classifications`); `credentials.py`; `classifier.py`. `test_classifier.py`: `DefaultPostureTests`, `KeyTests` (the key never in the file, an argument, an envelope, or an error), `GateTests` (the body is the previewed bytes), `ContractTests` and `FailureTests` (every answer outside the contract, and every failure, changes nothing and says why), `StopTests`, `CredentialStoreTests` (macOS and Linux, with the system calls mocked), `MigrationTests`. `classifier*` IPC commands; the dev host stays read-only |
| 4.7 | JEV's four jobs, each switched on separately, each only ever stricter: action review (a confident stricter suggestion holds approval until acknowledged), refusal pre-check before the AI model, workflow routing (a suggestion; nothing starts), attention order (every item kept; no number shown) | ✅ | `ActionReviewTests`, `RefusalCheckTests`, `RoutingTests`, `AttentionTests`; `ActionBoundary.approve` refuses an unacknowledged hold. Browser journey against a stand-in JEV: connect with a key that is never shown back; every job starts off; routing, ordering, and the refusal check each send exactly the previewed bytes; a refused question never reaches the AI model; disconnect removes the key. Action review is on the command surface only, like approval |
| 4.8 | JEV on real machines | ⛔ | Before a pilot uses JEV: check each credential store on a real Windows, macOS, and Linux machine (the Windows store has no automated test), and re-read TypeSafe's terms (ADR 0006) |

## G5 — Controlled follow-through (NM-011)

| # | Step | Status | Exit check |
|---|---|---|---|
| 5.1 | Recurring local brief ("runs when this device is awake"): off by default; a records-only draft at the manager's local weekday and hour while the app runs, caught up at the next launch that week; never a model, never accepted for the manager | ✅ | Migration `0008` (`brief_schedule`; `brief_runs` keyed by week, a drafted run needs its revision); `test_schedule.py`: restart (settings and runs survive; a crash mid-run leaves nothing half done), retry (after 5 then 30 minutes, gives up after 3 attempts and says so), dedup (asking again, two processes, the manager's own brief wins); `RecurringBriefAppTests` (the app's own thread drafts once); browser journeys (off by default, choices kept through a refused save, read-only on the dev host) |
| 5.2 | Scoped memory: what the manager asks the assistant to remember, for all work or one project, in their own words (the assistant never adds to it); inspect, correct, exclude (kept, never sent), delete (gone, text zeroed); used only by "Think with this project", where the preview shows it | ✅ | `WorkspaceMemory` implements the Integration Contract's `MemoryInterface` (the contract `GovernedMemory` implements), persisted by migration `0009` (`memories`); identifiers are refused, not stored redacted; `test_memory.py` (contract and consent verbs, order and facts, capture rules, correct with provenance, exclude/include decided inside the write, delete leaves no text in any table or the file); `test_assistant.py` (in-use memory reaches the model and can be cited, excluded never, a change invalidates the preview); `memory*` IPC commands; browser journeys (add with an identifier refused first and the text kept, correct, exclude, use again, delete with confirmation; the preview shows memory; read-only on the dev host) |
| 5.3 | "Assistants at work" with stop control: Mission Control lists every request waiting for a model and the recurring brief; one switch (the manager only) stops them all, and a Stop button sits wherever a model is working | ✅ | `AssistantControl` and migration `0010` (`assistant_control`; the request ledger gains `finished_at`, `stopped`, and `refused_stopped`, rebuilt with every row and note kept); `test_control.py`, the stop-control tests (a brief and a project question abandoned mid-request return within a second, and the late reply is never saved or shown; a stop landing after the reply is checked, or a stop-and-restart during the request, still discards it; nothing is sent while stopped, even when the stop comes after the preview; the recurring brief waits and runs after; owner-only, repeatable stop, explicit restart; a crash-left request is not shown for ever; the migration keeps every row and note); `test_app.py` (the app's scheduler prepares nothing while stopped); browser journeys (stop the model mid-brief and mid-question, the Every week and Mission Control states, restart by keyboard; read-only on the dev host) |
| 5.4 | Education, committee, and communication packs: each a reviewed set of templates reused from the shared deliverable catalog, with a manifest naming its maintainer and review dates and pinning each template by hash; a draft started from one is written and accepted by the manager like the weekly brief | ✅ | `nurse-manager/packs/*.json` and `PackService`; migration `0011` (`artifacts` gains `pack_document`, rebuilt with every row kept; `pack_documents` records the pack version and template pin); `test_packs.py` (every shipped manifest names its maintainer and review dates and pins its templates; a missing maintainer or date, a review date before the last review, a changed or missing template, or a wrong schema or catalog is refused; a broken pack is listed as unavailable, never used; a pack past its review date starts nothing and names who to ask; drafts carry the template, rules and origin; edits are new drafts, stale, unchanged or identifying edits refused; acceptance bound to the reviewed text; the migration keeps every brief and revision); `test_app.py` (lifecycle and malformed bodies); browser journeys (start, an identifier refused with the text kept, save, accept by keyboard; read-only on the dev host) |

## G6 — Packaged manager pilot (NM-012)

| # | Step | Status | Exit check |
|---|---|---|---|
| 6.1 | Signed release candidate; manifest pins upstream, policy, schema, and packs | ⛔ | Signing (0.9) |
| 6.2 | Update feed with signature check, pre-migration backup, and forward repair | ✅ | `update.py`: a signed feed (RSA-SHA256 over its exact bytes, verified with the standard library alone; agrees with OpenSSL) from a pinned key only; never backwards (replayed, contradicted, and expired feeds refused; no older release offered); advisory and manual (never downloads, installs, or runs by itself); `update-check` command; `tools/sign_update_feed.py` for the steward. `Store`: an existing workspace is backed up before any upgrade, and none happens without one; a failed step leaves the workspace at the last step that finished, names the backup, and is repaired forward by a corrected release. `test_update.py` |
| 6.2b | Turn the update feed on | ⛔ | Needs the steward: an update signing key kept off this repository (its public half and id pinned in `config/update-feed.json`), a feed address, and hosting. The Help page (step 6.3) then gains a "Check for updates" button |
| 6.3 | Onboarding, support guide, and pilot feedback | ✅ | **Onboarding:** before anything is created, the first-run screen says what the app does and does not do, that records stay on this computer, that no AI model runs by default, what the sample is, how to create your own workspace, and that the privacy screen does not detect names (correction 9). **Help and feedback** repeats it after the first run. **Support guide:** `04-support-guide.md`, held to the code by `test_support_guide.py`: every command, option, label, folder, and link it names exists, and nothing calls content free of patient information. `reconcile` is now a command, so the crash advice can be followed. **Pilot feedback:** migration `0013` and `PilotFeedback`. `test_pilot.py` checks capture rules and refusals, delete leaving no text in the file, and the exact export text with no workspace name, owner, or ids. It checks that the export is screened again, bound to the previewed hash, owner-only, and never lost when a file is not saved, and that the migration keeps every record. It also checks `reconcile` (nothing interrupted, unknown and never re-run, confirmed by hash). `pilot-feedback*` and `reconcile` are in the IPC contract. `test_app.py` checks that writes are POST-only, bodies are checked, and a name sent by the page is ignored. The dev host stays read-only. Browser journeys: onboarding facts. In the app, an identifier is refused with the text kept, save works by keyboard, the saved file is byte for byte the preview, a blocked export shows why without the identifier, delete asks first, nothing leaves 127.0.0.1, and the page reflows at 320px. On the dev host, the page is read-only and feedback text stays text. Where the export goes is the steward's decision; nothing is sent anywhere |

## G7 — Managed organization extension

Requires institutional authorization. Out of scope until then.
