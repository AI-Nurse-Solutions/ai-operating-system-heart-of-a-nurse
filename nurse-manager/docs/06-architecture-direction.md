---
title: Architecture direction and build plan improvements, after the v2.0 concept notes
date: 2026-10-04
authorship: Substantially AI-generated (Claude Code) with human review pending
status: Draft for steward review. Nothing here changes an accepted ADR or the status of any step in 01-build-steps.md.
sources: Five research notes supplied by the steward on 2026-10-04 (listed in §1). They are unverified research inputs. None of their footnotes is cited here, because none was read.
---

# Architecture direction and build plan improvements

Five research notes bear on the Manager Edition:

- one proposes a "Nurse AI OS Architecture v2.0";
- two specify a "Hermes Control Plane" dashboard;
- one explains open-source JARVIS Mission Control setups;
- one reviews a paid community's system.

This document checks each concept they contain against this repository and
its binding rules. It then states which concepts change the Manager
Edition's direction, and how the build plan should absorb them.

**Verdict.** The notes describe a web-based control plane with many
agents. It runs on a server that a vendor or the customer operates. The
v2.0 note asks that it can run in the customer's governed environment when
required. The Mission Control note weighs local, hosted, and hybrid setups.

The Manager Edition is different: a local, single-assistant app with no
model by default. About a fifth of what the notes ask for already exists
here, under other names. Most of the rest fits once it is reshaped to the
accepted ADRs. That covers governed approvals, evidence, a home screen that
shows what needs attention, and stop controls. A small set conflicts with
binding rules and is not adopted.

The most valuable result of the review is not a new layer. It is five
gaps in what already ships (§2). The most serious: a manager who starts
their own workspace cannot add projects, tasks, decisions, or priorities to
it, so the board, Mission Control, and the brief stay empty.

Of the 70 concepts in the notes:

| Verdict | Count | Meaning |
|---|---|---|
| Already have | 14 | The repository does this today, often under another name or in another form |
| Adapt | 42 | Keep the intent, change the shape to fit the ADRs and `SAFETY.md` |
| Defer | 8 | Valid, but behind G7 or a steward decision that has not been made |
| Reject | 6 | Conflicts with a binding rule, or is unsound here |
| Adopt as written | 0 | None survives unchanged |

## 1. Sources and method

The five notes, as supplied:

| Note | Concept ids | What it proposes |
|---|---|---|
| "A formal Nurse AI OS Architecture v2.0 document…" | ARCH-01 to ARCH-21 | Supervisor plus six specialist agents, critic, escalation manager, knowledge and memory layers, MCP connectors, a governance plane, and six phases from 0 to 12+ months |
| "Draft the UI component tree for the dashboard" | UI-01 to UI-13 | A React/Next.js component tree for a "Hermes Control Plane" |
| "What are best in class hermes dashboard setups…" | PRD-NAME, PRD-01 to PRD-18, PRD-SCREENS, PRD-IA, PRD-DESIGN, PRD-BOUNDARY, PRD-METRICS, PRD-MVP | Product requirements for the same dashboard |
| "How do open-source JARVIS Mission Control setups work" | MC-01 to MC-07 | How file-backed shared state, a lead-coordinator persona, and a real-time dashboard work in those setups |
| "Research … their Agentic OS system, Jarvis, and mission control" | SK-01 to SK-04 | A review of a paid community's system. Its public material is gated and unverifiable |

**Method.** Every pass below was an AI pass run in Claude Code. No person
has reviewed this document yet (see the frontmatter).

The first passes mapped these subsystems:

- the Manager Edition core
- its renderer and IPC contract
- `naio-integrations`
- `naio-harness-v2`
- the Mission Control lineage in `naio-os/`
- the binding policy files and prior architecture documents

Later passes gave each concept a verdict and proposed one-PR build steps.
Two checking passes followed. One checked every repository claim against
the code. The other checked every proposal against `SAFETY.md`,
`GOVERNANCE.md`, `TRADEMARKS.md`, ADRs 0001–0004, the validation report's
corrections, and the step 0.8 review. Their corrections were applied, and
a final pass checked coverage, duplicate steps, and sequencing. A further
five-way review checked this draft itself, covering facts, policy, plan
coherence, completeness, and style.

The findings in §2 were checked again in the same session, by reading the
code at each cited line.

**Names used below.** Proposed steps are named P + gate + number; for
example, P2.3 is the third proposed G2 step. All are listed in §5.4, and
their numbers are provisional. Steward decision issues are I-1 to I-7
(§6). N-1 and N-2 are steps outside the Manager Edition.

## 2. What the review found in today's code

These are facts about the repository at the commit this document lands on.
Each one is a gap in shipped work, not a new feature.

1. **An own workspace cannot gain projects, tasks, decisions, or
   priorities.**
   - The writers exist (`ManagerWorkspace.add_project`, `add_task`,
     `move_task`, `set_blocked`, `set_paused`, `complete_task`,
     `record_decision`, `set_priorities`; `src/nurse_manager/services.py:147-340`).
   - No CLI command, IPC command, or app write calls them
     (`contracts/ipc/commands.json`; `WRITE_COMMANDS` at
     `src/nurse_manager/app.py:65-72`).
   - Only `sample.py` calls some of them. `move_task` and `set_paused`
     have no caller outside tests.
   - Sources, learning items, contributions, memories, pack documents, and
     briefs can already be added from the app. Without projects and tasks,
     though, the board, Mission Control, and the brief stay empty.
2. **The audit stream is not tamper-evident.**
   - `event_log` has no hash chain and no append-only enforcement
     (`migrations/0001_initial.sql:157`; `Store.log` at `store.py:296-301`).
   - Where a writer logs, the row is written in the same transaction as
     the change, so it fails closed. AI ledger updates are not logged yet
     (P4.5).
   - `SAFETY.md:36` requires tamper-evident audit for official
     deployments. Shipping the signed release candidate (step 6.1) without
     a chain would knowingly miss that clause.
3. **Approvals exist only on the command line.**
   - Mission Control lists "Approval needed" items
     (`src/nurse_manager/views.py:230-232`).
   - `approve`, `run`, and `export` are not app writes. The support guide
     says the screens never write export files (`docs/04-support-guide.md:155`).
   - ADR 0003 promises no terminal. Before any second path is added, the
     action status checks must move inside the write.
     - Today `ActionBoundary.approve` reads the status (`actions.py:250`)
       before opening the write transaction (`:265`).
     - `ActionBoundary.execute`, which the `run` command calls, does the
       same (`:281`, then `:295`).
     - `_set_status` updates by id alone (`:381-386`).
4. **What the assistant was told is not versioned.**
   - The two system prompts are unversioned constants (`assistant.py:95`,
     `:104`). The preview hash covers them per request, but nothing names a
     version.
   - The Florence-X `EvidenceBundle` leaves `model_used`, `model_version`,
     and `prompt_template_version` empty by design, because the action
     boundary calls no model (`02-contract-map.md` §4;
     `florence_adapter.py:273-276`). So a bundle for exporting an AI-drafted
     revision cannot say which model and prompt produced it, even though
     the ledger records the model for each request.
5. **Safety state depends on which screen loaded.**
   - The sample banner is set only from envelopes that carry a `sample`
     field (`renderer/app.mjs:263`). `WeeklyBrief` and `AssistantStatus`
     have none, so a direct load of the brief or AI pages cannot show it.
   - One badge kind, `blocked`, is used for five different things: a
     blocked task, the manager's own "Stopped", "Waiting", "Will not be
     sent", and "Delete for good?" (`renderer/views.mjs:145`, `:310`,
     `:964`, `:1252`, `:1368`).

Smaller verified defects, each taken into a step in §5:

- `move_task` changes the status of a completed task without clearing its
  completion evidence (`services.py:199-237`). Fixed by P2.1.
- The per-item **Stop assistants** button calls the same global stop as
  **Stop all assistants** (`renderer/app.mjs:498`). The support guide calls
  it "Stop one piece of work" (`04-support-guide.md:181`). Fixed by P6.8.
- The record-writer register (`02-contract-map.md` §5) omits three
  tables: `action_policy_versions`, `pilot_feedback`, and
  `pilot_feedback_exports`. Fixed by P1.1.
- `02-contract-map.md:15` still says "this PR". `:134` says mission
  lifecycle moves to Florence-X "once G2 step 2.11 lands", but 2.11
  shipped as a one-way adapter only. Fixed by P1.1.

One finding sits outside the Manager Edition. The shared EDENA engine
allows a zone migration when `zone_migration_approval` holds any non-empty
value (`naio-integrations/src/naio_integrations/policy.py:92`). Its own test
asserts that an invented id is allowed
(`naio-integrations/tests/test_data_zones.py:96-106`). The `approval_id`
path, by contrast, checks the actor's held approvals (`policy.py:278`).
This changes Integration Contract behavior, so it needs a GOVERNANCE §3
proposal (step N-1 in §5.4).

## 3. The architecture as it stands, and where the notes land

```mermaid
flowchart TD
    M["Nurse manager (the only human; the accountable owner)"]

    subgraph UI["Screens: plain ES modules, no framework, strict CSP"]
        MC["Mission Control: needs my judgment, assistants at work, stop"]
        WK["Board, Tasks, Project dashboard"]
        BR["Weekly brief, Packs, Library, Memory"]
        AP["Approvals page (proposed, P5.1 to P5.3b)"]
        AR["Activity record and 'How this was made' (proposed, P3.12 to P3.13)"]
    end

    subgraph HOST["Loopback host: per-launch token, write allowlist, owner injected"]
        SV["Single writers per record (02-contract-map §5)"]
    end

    subgraph GATES["Gates every capability passes"]
        G1["Capture rules: refuse identifiers and D2 or above"]
        G2["Profile table, plus EDENA at recommend for assistants (ADR 0002)"]
        G3["Budget, preview bound by hash, deterministic output check"]
        G4["Acceptance bound to text hash"]
        G5["Action boundary: propose, approve, recheck, execute, receipt"]
    end

    subgraph DATA["One SQLite workspace on this computer"]
        R["Records, revisions, actions, receipts"]
        L["AI request ledger: hashes and outcomes, never text"]
        E["event_log: metadata only (hash chain proposed, P2.3)"]
    end

    LM["Optional model on this computer (ADR 0004)"]
    FX["Florence-X projection: one-way, hashes not content"]
    PARK["Parked at G7 or on no gate: supervisor and specialist agents, connectors, org identity, hosted or hybrid, staffing operations"]

    M --> MC
    UI --> SV
    SV --> GATES
    GATES --> DATA
    G3 <--> LM
    DATA --> FX
    PARK -.->|only after institutional authorization and a steward decision| GATES
```

How the v2.0 components land, in one line each:

| v2.0 component | In the Manager Edition |
|---|---|
| Nurse Manager Workspace | Mission Control and the existing screens. Huddles, coaching, and communications are packs. Staffing and quality operations are G7 |
| Request Router | The manager picks the workflow on screen. A deterministic refusal set runs before any AI preview (P4.3). When the manager turns it on, JEV suggests a place to start and checks a question before the AI model; it never picks (ADR 0006) |
| Session and Task State | Per-mechanism state machines that already exist. Resume means re-verify, never re-run |
| Supervisor Agent | Not in the Manager core, on any gate. Florence-X, after evidence and a steward decision |
| Specialist Agents | One reviewed assistant task manifest with versioned prompts (P4.1). No Staffing or Quality & Safety tasks in the Personal profile |
| Critic / Verifier | Already built as a deterministic output check. It gains a pinned regression and red-team set (P4.2). A model critic may only add warnings |
| Escalation Manager | "Needs my judgment" with a reason, or an honest hand-off out of the app. A second reviewer is G7 |
| Approved Knowledge Base | Sources stay references with review dates the manager maintains (P3.11). Employer policy libraries are G7 |
| Organization / Session Memory | Organization memory is G7. There is no hidden session memory; continuity comes only from what the manager accepted |
| Audit and Evidence Ledger | `event_log` plus receipts and Florence-X bundles. It becomes tamper-evident (P2.3), never called "immutable" |
| Tools and Connectors (MCP) | None in the Personal profile. An admission contract is a G7 design item |
| Identity, RBAC/ABAC | One owner plus a distinct assistant identity until G7 |
| Data classification, minimum-necessary retrieval | Already built as refusal at capture and "only this project, exactly as previewed" |
| Human approval gates | Already built and hash-bound. They gain an in-app path (P5.1 to P5.3b) |
| Observability | Local facts the manager pulls. Nothing leaves the computer |
| Nurse Ethics Control Plane | A rules and operating-boundary register held to the code by a test (P5.4). "Control plane" stays the term for Florence-X and EDENA |

## 4. Direction: ten decisions

These are the direction statements this document asks the steward to adopt.

- The proposed ADR 0005 (`adr/0005-scope-against-v2-concept-notes.md`)
  records:
  - decision 1;
  - the parked scope in decision 6;
  - the deployment and connector scope;
  - the naming and console-stack parts of decision 9.
- The rest is adopted through the proposal issues in §6:
  - Decision 5 is not in the ADR. Steps P3.6b and P5.4 carry it, and it
    is decided under I-3.
  - The status semantics in decision 9 go to I-6.
  - Decisions 2 and 7 go to I-5, decision 4 to I-2, and decision 8 to
    I-7.
  - Decisions 3 and 10 need nothing beyond I-4 (in-app approval) and P0.3
    (opening the issues).

1. **One human-orchestrated, single-assistant system.**
   - The notes' supervisor, router agent, six specialists, coordinator
     persona, agent-written shared memory, and agent registry are not built
     into the Manager core.
   - They become three things: the manager's explicit choice of workflow,
     reviewed task entries in one assistant manifest, and reviewed packs.
   - Any multi-step orchestration is Florence-X work, after it is evidenced
     and the steward decides (ADR 0001; `three-lanes/STRATEGY.md:151`
     defers "more generalized agents, agent swarms").
2. **Every new capability passes the gates the code already enforces:**
   - capture-time refusal, not redaction
   - a byte-exact preview bound by hash
   - EDENA at `recommend`
   - budgets
   - a deterministic line-by-line citation check
   - owner acceptance bound to the text hash
   - for effects: propose → approve bound to hash and destination →
     recheck → receipt

   No model ever assigns risk, picks a workflow, or releases text, and no
   model can open a gate. Under ADR 0006, the JEV classifier may suggest a
   workflow (the manager still picks), and may add a hold or a refusal. It
   never removes one.
3. **Close the real-manager gaps first, in the order of §5.2:**
   - decide every task status transition inside its write (P2.1)
   - wire the existing writers to commands and screens (P2.2, P3.1, P3.2)
   - make action status transitions conditional (P2.4), and add reject and
     revoke in the backend (P5.3a)
   - give governed actions an in-app path (approve, run, reject, revoke)
     if the steward agrees (I-4)
   - after the pilot subset: let the weekly brief be edited as a
     stale-checked new draft that keeps its AI label (P3.3)
4. **Audit becomes tamper-evident, never "immutable".**
   - One SHA-256 chain on `event_log`, written in the writer's transaction.
     It reuses the canonical-hash discipline of the gateway tracer and the
     harness provenance ledger.
   - A chain inside the file detects edits, deletions, and reordering of
     interior rows. It cannot detect a cut-off tail, or the whole file
     swapped for an older valid copy: what remains still verifies. So the
     latest head and row count are also kept outside the workspace file,
     and checked against it.
   - The chain is proposed as a named prerequisite of step 6.1.
   - Until it lands, every view and document says the local log is not
     tamper-evident.
5. **The boundary is D0/D1. It is stated, held by tests, and never
   certified.**
   - One register maps each rule to its enforcing code and test, and lists
     what is admitted, refused, and G7-only.
   - A header strip on every screen states the data rule as an
     instruction, plus "names are not detected".
   - No surface says "No PHI", "Production", "certified", "immutable", or
     "compliant", and the overclaim test is extended to all five (P3.6a).
6. **Organizational scope is parked, and named so.**
   - G7 becomes a parked-scope register (§5.5) with a header that says
     `SAFETY.md` §2–3 apply unchanged. This covers anything that needs:
     - D2 or higher data
     - a second person or an organization identity
     - connectors
     - a hosted or hybrid surface
     - customer-cloud deployment or a BAA
     - role-based views, a risk register, or incidents
   - Rejected for the Personal profile, not deferred:
     - staffing and coverage operations
     - quality and safety event review
     - coaching notes about named individuals
     - measuring people by unit, shift, or role
7. **Anything that governs runtime behavior carries a version, and records
   name it.**
   - This covers system prompts, the profile table, the EDENA policy,
     privacy recognizers, and packs.
   - CI forces a version bump when content changes. A widening change links
     a steward decision.
8. **Measurement follows `three-lanes/EVIDENCE.md`, not the notes' KPI
   table.**
   - Facts are counted locally and shown only to the manager, as counts or
     "N of M". They are never scores and never segmented by person. No
     measure is shared with an employer at individual grain
     (`EVIDENCE.md:103`).
   - Anything that leaves the computer goes through an opt-in, previewed
     pilot export after a steward decision.
9. **Naming and design stay calm and plain.**
   - The product is "Nurse AI OS Manager".
   - "Hermes Control Plane" and "Ask Hermes" put Hermes inside a product or
     control name. `05-hermes-review.md` §2.3 lists that as not
     acceptable.
   - This document adds the same rule for "Jarvis" (no coordinator
     persona) and "control plane" (kept as the term for Florence-X and
     EDENA). A guard test enforces all four (P0.5).
   - The renderer stays framework-free ES modules. The notes'
     React/Next.js tree is not adopted.
   - Status meaning becomes declared data. A critical color is reserved for
     "denied" and "failed", and only after the overloaded `blocked` kind is
     split.
10. **Gates pass by go/no-go, never by month.**
    - The notes' six phases are mapped onto gates or marked "deferred: on no
      gate" (§5.6).
    - The pilot is gated by signing and clean-machine install, not by
      feature count.
    - Steward decisions are batched into a few proposal issues (§6), so the
      blocked critical path is not buried under new work.

## 5. Build plan improvements

### 5.1 The critical path does not change

The pilot is still gated by code signing:

- 0.9: signing identities
- 1.9: signing
- 1.10: clean-machine install on real manager laptops
- 6.1: signed release candidate

0.9 and 1.9 are blocked on the steward's accounts. 1.10 and 6.1 follow
from them, and 1.10 also needs a pilot laptop inventory. Nothing below
unblocks them, so they should be requested now if they have not been.

This document proposes adding named prerequisites to 6.1's row in
`01-build-steps.md`. None is added until the steward accepts it:

- the audit chain (P2.3), after I-2
- capture from the screens (P3.1, P3.2), after I-3
- the status strip, with its unsigned-build label and data rule (P3.6a,
  P3.6b)
- the security facts sheet (P6.1)
- the support-guide additions and correction (P6.8)

The rows in §5.4 carry the same marker.

### 5.2 Minimal pilot-ready subset, in order

The full list in §5.4 has about 60 steps. Most are post-pilot. These are
the steps a real manager's pilot needs, in build order:

1. P1.1: complete and test the record-writer register. It lands before any
   new migration.
2. P1.3: one shared test over every `WRITE_COMMANDS` entry. It lands
   before the capture screens add new write commands.
3. P2.1: task transitions decided inside the write.
4. P2.2: capture commands.
5. P3.1, P3.2: capture screens.
6. P2.3: tamper-evident `event_log`.
7. P2.4: conditional action transitions.
8. P3.6a, P3.6b: header status strip, with the global stop and the data
   rule.
9. P3.7: actionable "Needs my judgment".
10. P5.1: the Approvals page (read), and P5.3a: reject and revoke in the
    backend. P5.2 and P5.3b follow if the steward decides the app may act
    on approvals (I-4).
11. P6.1: security and data-handling facts.
12. P6.8: support-guide additions and the Stop wording correction.

### 5.3 How the new steps enter 01-build-steps.md

- Ids here are provisional. Final step and migration numbers are assigned
  once, when the steward accepts a step into `01-build-steps.md`.
- G3 and G5 have every existing step done. The other gates still have
  blocked or deferred steps:
  - G0: 0.9 and 0.10 blocked; 0.7 deferred
  - G1: 1.9 and 1.10 blocked; 1.11 deferred
  - G2: 2.10 blocked
  - G4: 4.2b and 4.5b blocked; 4.2c deferred
  - G6: 6.1 and 6.2b blocked

  Proposed steps are marked **additions** in their gate. So a go/no-go the
  steward gives later covers them explicitly, and one already given is not
  quietly reopened.
- Column additions to `assistant_requests` come in two migrations, so the
  buildable step does not wait on a steward decision.
  - P4.1 adds the nullable `prompt_version` column on its own, in place,
    with `ALTER TABLE … ADD COLUMN` (the 0004 pattern).
  - P4.3's refusal category and `refused_intake` outcome come in a later
    migration, after I-5. The new outcome changes the outcome CHECK, so
    that migration follows the 0010/0011 pattern: rebuild, keep every row,
    and back up first.
- Every new write command gets the same protections: POST only, body
  checked, owner injected, read-only on the dev host, named in the support
  guide, and present in the generated types. P1.3 enforces this for every
  entry in `WRITE_COMMANDS`.

### 5.4 Proposed steps by gate

**Steward column.**

- **D**: needs a steward decision first. The issue it belongs to is in §6.
- **—**: buildable now.
- **⛔**: also blocked on an existing blocked step, which is named.

Test files and test classes named in an exit check are new, unless they
already exist in `nurse-manager/tests/` or the named package.

#### G0 — Baseline (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P0.1 | ADR 0005: Manager Edition scope against the v2.0 concept notes (proposed in this PR) | ADR status Accepted, with a decision record | D (I-1) |
| P0.2a | Fix stale status lines in `01-build-steps.md` and the README | `test_support_guide.py` still passes; no line calls a done step pending | — |
| P0.2b | Record the mapping of the notes' six phases (§5.6) in `01-build-steps.md` | Every phase has a gate or "deferred: on no gate" | D (I-1) |
| P0.3 | Open the steward decision issues in §6 and link them from `01-build-steps.md` | Issues exist; each blocked step names its issue | — (opened by or for the steward) |
| P0.4 | Obtain or re-author the 2.10 definitions (concern, containment, preservation hold) | A definitions document the steward accepts; 2.10 becomes buildable | D (I-3) |
| P0.5 | Guard the Manager Edition against Hermes or persona names in product positions | `ManagerEditionNamingTests` in `test_notices.py`: passes now; fails on a seeded "Ask Hermes", "Hermes Control Plane", "Jarvis", or "control plane" string in a product position; passes on "runs on Hermes Desktop" | — (Hermes names); D (I-1: the "Jarvis" and "control plane" cases rest on ADR 0005) |

#### G1 — Installer and contracts (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P1.1 | Complete the record-writer register (`action_policy_versions`, `pilot_feedback`, `pilot_feedback_exports`); correct `02-contract-map.md:15` and `:134` | A test fails when a migration adds a table missing from §5, or §5 names a table the migrated schema lacks; a text assertion that the map no longer says "this PR" or "once G2 step 2.11 lands" | — |
| P1.2 | Pin the network surface, not only the imports: only named modules may import network listeners, network clients, or process spawning, each with a stated reason; and every outbound destination is on one allowlist (loopback, the configured update feed, and JEV's address under ADR 0006), checked where the connection is made. An allowed module could otherwise add a new destination without a new import | `test_network_surface.py` passes now and fails on seeded fixtures: a forbidden import, and a new destination added inside an allowed module. A runtime egress test drives every command with connections intercepted and fails on any destination off the allowlist | — |
| P1.3 | One shared test over every `WRITE_COMMANDS` entry: malformed body refused, page-supplied identity ignored, dev host read-only | The test iterates the tuple, so a new command without coverage fails | — |

#### G2 — Durable manager mission (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P2.1 | Decide every task transition inside the write (`WHERE id = ? AND workspace_id = ? AND status IN (…)`, rowcount 1). A completed task moves only by explicit reopen with a reason; reopen keeps the earlier evidence in an append-only record. Add "withdrawn", with a reason | `TaskTransitionTests`: two racing moves cannot both succeed; reopen keeps prior evidence; the migration keeps every task and event | — |
| P2.2 | Capture commands for projects, tasks, decisions, and priorities, over the existing writers. Owner, reviewer, and decided-by are free text, as the writers accept them today. If I-3 chooses to enforce role words, that lands in the writers in a follow-up step, so the CLI and the screens get it together | `CliJourneyTests`: an empty own workspace gains a project and task, moves it, completes it with evidence, and shows the same ids on Mission Control, board, and table; ajv and `tsc --strict` pass | — |
| P2.3 | Tamper-evident `event_log`: SHA-256 chain written in `Store.log`'s transaction; triggers that refuse UPDATE and DELETE; `verify_events`; the chain head named at backup; restore refuses a broken chain. The latest head and row count are anchored outside the workspace file, where a copy of the file does not carry them (for example the operating system's credential store, or a head the manager keeps), and `verify_events` checks the file against that anchor. Rows from before the migration are reported as unchained, never hashed after the fact. The docs say what it does not cover: anyone who can change both the file and the anchor as the manager's own account. **Prerequisite of 6.1** | `EventChainTests`: edits, deletions, and reordering mid-chain are detected; a cut-off tail and a whole-file rollback to an older valid copy are detected against the outside anchor; a missing anchor is reported, never treated as valid; a failed log insert rolls back the write; restore of a broken chain is refused | D (I-2) |
| P2.4 | Conditional action status transitions (`WHERE status = expected`, rowcount checked); `approve` refuses a revision that is no longer accepted | Two-process `ActionBoundaryTests`: approve vs approve gives one approval; run vs reconcile gives one receipt; run vs run gives one effect | — |
| P2.5 | A human-proposed effect whose rule needs independent review is denied at proposal time, with a hand-off reason, instead of waiting for an approval that can never be granted | `ActionBoundaryTests`; the shadow set gains a labeled case and is re-pinned in this PR. If N-1 later changes a label, N-1 re-pins it | — (assistant-origin case: D, I-5) |
| P2.6 | Capture known-limit probes: a pinned synthetic fixture of what the privacy screen does not catch (names, roster-style lines), recorded as stated limits, not passes | `CaptureRuleTests` known-limit test; each limit is named in plain words in the support guide | — |

#### G3 — Unified manager views (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P3.1 | Capture and move tasks from the screens: capture, move, block, mark paused or active, complete with evidence. Owner and reviewer default to "me" or a role. **Prerequisite of 6.1** | `test_app.py` write tests; a `test_app_browser.mjs` journey from an empty own workspace, by keyboard; an identifier refused with the typed text kept; 320px reflow | D (I-3: are owner and reviewer limited to role words, or only hinted?) |
| P3.2 | Capture projects, decisions, and this week's priorities from the screens. **Prerequisite of 6.1** | Browser journey; a fourth priority refused with the typed text kept; a decision captured in the app is cited in the next brief | D (I-3) |
| P3.3 | Edit the weekly brief as a new draft bound to the text you opened. An edited AI draft keeps an "Edited by you from an AI draft" label | `BriefTests`: stale base and unchanged text refused; the AI label survives edits; pack documents delegate to the same writer | — |
| P3.4 | Revision history and text compare for briefs and pack documents | `RevisionCompareTests` and a `test_renderer_browser.mjs` journey: the diff renders as text, injected markup stays literal, keyboard reachable, read-only on the dev host | — |
| P3.5 | "Records this draft cites": a resolved, text-only list built from the citations actually in the text. No confidence score | `ViewTests`: every cited id resolves; removing a cited line removes it from the list; overdue sources flagged | — |
| P3.6a | Header status strip on every route: workspace kind; "Test build (unsigned)" from a build marker that fails closed; assistants working or stopped, with the global stop; judgment count. Fixes the sample banner on the brief and AI pages. **Prerequisite of 6.1** | Present on every route in `ROUTES`, with no fixed count; the build label cannot read anything but "Test build (unsigned)" without a signature record; the overclaim pattern is extended to "No PHI", "Production", "certified", "immutable", and "compliant" | — |
| P3.6b | The data rule in the strip, worded as an instruction, plus "names are not detected". **Prerequisite of 6.1** | The line is identical on every route; `test_support_guide.py` holds the same wording | D (I-3: the wording) |
| P3.7 | Actionable "Needs my judgment" (detail below the table). Quick actions on Mission Control | `ViewTests`: target route and phrase on every item; deterministic order; no numeric score field; the group follows from the record kind through a fixed mapping. A unit test of the tier function over the full Directive vocabulary plus an unknown value | — |
| P3.8 | Grouped navigation (Today, Work, Knowledge, My growth, Assistance, Help) and plain labels: "Table" becomes "Tasks"; the AI gate "EDENA policy" becomes "Policy check", with EDENA named in Help; "Idea" and "Ideas" made consistent | Keyboard journey through the grouped nav; `test_support_guide.py` finds every label the guide names | — (grouping, "Tasks", "Idea"); D (I-6: the name "Today", and EDENA leaving the gate label) |
| P3.9a | Declare status semantics in `tokens.json`: each badge kind has a family, an icon, and a default label | `test_design_tokens.py`: every badge kind the renderer uses is declared, including kinds chosen at runtime | — |
| P3.9b | Split `blocked` into blocked, denied, and failed. Add a reserved critical family, used only by denied and failed, and a neutral family for paused, unavailable, Stopped, and Waiting | `test_design_tokens.py`: the critical family is used only by denied and failed; contrast pairs pass in both themes | D (I-6) |
| P3.10 | Voice and naming guide held to the code (detail below the table) | `test_voice_guide.py`: every glossary label appears in the renderer; no banned term appears in visible text | D (I-6) |
| P3.11 | "I checked this source": the app records today's date (never a typed one) and the next review date; the review state travels with the source | `LibraryTests`: the date cannot be supplied; another workspace's source refused; an audit row written | — |
| P3.12 | Activity record: a metadata-only, filterable view of `event_log` (record type, record id, actor kind, dates). Labeled "local log, not tamper-evident" until P2.3, then shows the chain status | `ActivityRecordTests`: rows equal `Store.events()`; no content fields; the contract refuses an event with `before` or `after` | — (chain status after P2.3) |
| P3.13 | "How this was made" per revision, plus a per-artifact evidence packet **preview** (detail below the table) | `TraceTests`; the same records always give the same packet; no body text, names, paths, or workspace id appear | — |
| P3.14 | A given-up weekly brief appears under "Needs my judgment" and links to the brief; it clears when a revision exists for that week or the week ends | `ViewTests` for appear, clear on revision, clear at week end | — |
| P3.15 | Help states where to report a concern (detail below the table), until 2.10 provides a Report concern record | `test_support_guide.py` and the Help screen hold the same text; no Report concern control yet | — |
| P3.16 | A label and status comprehension check with testers on the synthetic sample, recorded with the evidence fields `directive.html` requires | `docs/07-design-check.md`; `tokens.json` "status" may drop "not yet user-tested" only by citing it | — |
| P3.17 | Optional: local Library search over titles, references, and shipped pack templates; sends nothing to a model | `LibraryTests`: no ledger row and no provider call | — |
| P3.18 | Optional: a screened note kept with an acceptance | `BriefTests`: an identifier in the note refuses the acceptance and leaves a draft | — |

P3.7 in detail:

- Every judgment item links to where it is decided, and carries an action
  phrase: Decide; Review and accept; Approve or leave.
- Action items show their stored tier through one pure tier function. It
  shows orange as Yellow plus "organization approval", never Green. An
  unknown or missing tier never shows Green.
- Overdue items come first. There is no severity score.
- Mission Control has two groups, with no third urgency level:
  - "Act on these": a decision, review, or approval is waiting.
  - "For information": nothing needs deciding, such as a source due for
    review or assistants stopped.
- Until approval is in the app, action items say: "Approval is not
  available in the app yet. Nothing happens until it is approved." They
  never point to a terminal.

P3.10 in detail. The guide holds:

- the glossary;
- banned wording, in one fenced block;
- the persona rule: the dashboard makes work visible and governable; it
  does not think;
- "packs", never "blueprints".

P3.13 in detail. Each revision states its origin:

- records only;
- AI, with the model and prompt version;
- or a pack pin.

It also lists the cited records, the acceptance, the action, the policy
version, and the receipt. Ids are replaced by ordinals.

P3.15 in detail. Help states the two places to report a concern: the
organization's incident process, and privately to the project. It says to
leave patient information out of the report.

#### G4 — Bounded assistance (additions; 4.2b, 4.2c, and 4.5b remain open)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P4.1 | Assistant task manifest with versioned prompts, recorded on every request (detail below the table) | `AssistantTaskManifestTests`: the task ids match the CHECK; a prompt edit without a version bump fails; a missing or mismatched entry refuses before preview and falls back to the records-only draft. `test_florence_adapter.py`: the bundle for an AI-drafted revision carries its model and prompt version; a human-origin revision's bundle leaves them empty; Florence-X validates both | — |
| P4.2 | A pinned regression set for the output check, with red-team cases: invented citation, uncited line, citation spoofing, and instruction-bearing text inside a cited record | `test_output_check_set.py`: every case matches its label; the set's sha256 is pinned; any loosening fails CI | — |
| P4.3 | A named refusal set before any AI preview (detail below the table) | `RefusalSetTests` over a pinned synthetic case file: each category refused before preview; nothing reaches the stand-in model; permitted management questions pass | D (I-5; I-1, because it rests on `three-lanes/IMPLEMENTATION.md`, still "Proposed") |
| P4.4 | AI assistance profile and facts (detail below the table) | `StatusFactsTests`: counts equal ledger rows; spend equals the sum the budget gate uses; no "%" rendered | — |
| P4.5 | Every AI ledger insert and update writes a matching `event_log` row | `LedgerAuditTests` across fallback, stop, provider failure, and refused output | — |
| P4.6 | The project-question context carries each source's kind, data class, and review state | `ProjectQuestionTests`: a changed review date invalidates the preview; preview equals what the stand-in model received | — |
| P4.7 | The manager can leave sections out of a project question; a left-out section is stated as left out, so the model cannot read absence as "none" | `ProjectQuestionTests`: left-out sections are never sent; a changed selection needs a new preview | — |
| P4.8 | Kept project notes in "Think with this project", only when every record a note cites is still in use, cited by note id, with no exemption from the citation check | `ProjectQuestionTests` for kept, unkept, excluded-memory, and deleted-memory cases | D (I-5) |

P4.1 in detail:

- Prompts stay in code.
- One manifest lists, for each task:
  - its id (the set of ids equals the `0010` task CHECK);
  - its version and prompt sha256;
  - its data scope (code caps it; the manifest can only narrow it);
  - its output contract;
  - its review dates.
- One nullable `prompt_version` ledger column records the version on every
  request.
- For an action on an AI-drafted revision, the `EvidenceBundle` model and
  prompt fields come from that revision's ledger row and manifest entry.
  For anything else they stay empty. The `02-contract-map.md` §4 row is
  updated to match.

P4.3 in detail. The refusal categories:

- patient narratives
- identifiable staff performance or discipline
- employer-confidential material
- clinical decision support
- determining, scoring, or ranking a named person

Each refusal names the nearest permitted path. The ledger keeps only the
outcome and category.

P4.4 in detail. The profile states:

- what the assistant may do, and what it never does;
- the gates, in plain words;
- prompt versions;
- requests by task and outcome;
- spend against budget (the fields are already in the contract).

It also says that the monthly cost budget does not apply to a model on
this computer, which is estimated at zero cost (`assistant.py:203`). The
daily request limit governs it (`:387-390`). A budget setter arrives with
the cloud provider (4.2b).

#### G5 — Controlled follow-through (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P5.1 | Approvals page (read) (detail below the table) | `ApprovalsViewTests`: same action ids as Mission Control; stale, effect unknown, executing, and superseded shown honestly; the page renders tiers only through P3.7's tier function | — |
| P5.2 | Propose, approve, and run an export from the screens. Approval needs a single-use read token issued with the page that showed the action, so an approval cannot be replayed or made for an action the page did not show. The token proves the page was fetched, not that a person read it: a program running as the manager on this computer can fetch the page too. Human review rests on the manager using the app, as it does for every write today (ADR 0003); the docs must not claim more | `test_app.py`: owner injected; wrong sha or destination refused with no approval row; a reused or missing read token refused; a browser journey by keyboard | D (I-4: ADR 0002 addendum making the app an approval surface; it supersedes `naio-os/mission-control/ARCHITECTURE.md:150` for this edition); after P2.4 and P5.1 |
| P5.3a | Reject a proposal, or revoke an approval that has not run, with an optional screened rationale (backend and CLI) | Rejected and revoked actions have no effect and cannot be approved or run; racing reject and approve, or revoke and run, gives one winner; the migration keeps every action; `to_evidence_bundle` maps each new status to a `final_action` and `incident_flags` value, and `02-contract-map.md` gains the rows | — |
| P5.3b | Reject and revoke from the Approvals page | `test_app.py` allowlist and body checks; a keyboard journey; read-only on the dev host | D (I-4); after P5.1 and P5.3a |
| P5.4 | Manager rules and operating-boundary register (detail below the table) | `test_operating_boundary.py`: every effect in the profile table, every pack, and every assistant task appears with the right status; every named function and test exists | D (I-3) |
| P5.5 | Governed Project Packet pack (MVP outcome 1), reusing the pack engine and acceptance binding | `test_packs.py` passes for the manifest; required sections are present in every started document | D (I-1: three-lanes status) |
| P5.6 | Improvement pack at planning level only: no rosters, census, named staff, or event detail | `test_packs.py`; the pack's rules narrow the template guidance that asks for baselines and named people | D (I-3: the D1/D2 line) |
| P5.7 | First pack-linked assistant task: draft one pack section from project records | `PackSectionTests`: preview equals what is sent; only this project's records and the chosen section; written through the existing writer | D (I-5); after P4.1 to P4.3; ⛔ evidence from real managers waits on 6.1 |

P5.1 in detail. The page shows:

- every proposed action, what it would do, and why it is waiting;
- the exact rendered text with its sha256;
- separately labeled, the payload fingerprint that approval binds;
- "Proposed by" and "Approved by";
- policy reasons in plain words, and the policy version;
- tier labels, through P3.7's tier function.

P5.4 in detail. The register:

- lists rules under the notes' six control classes (access, data,
  decision, evidence, runtime, retention), each with its enforcing function
  and test;
- states the scope as admitted, refused, and G7-only;
- lists named-person determinations as "prohibited by rule, not
  detected".

#### G6 — Packaged manager pilot (additions)

| Id | Step | Exit check | Steward |
|---|---|---|---|
| P6.1 | Security and data-handling facts for hospital IT, held to the code (detail below the table). **Prerequisite of 6.1** | `test_security_facts.py`: every named header, folder, command, and setting exists; the overclaim pattern finds nothing | — (distribution: D, I-7) |
| P6.2 | Pilot evidence plan (detail below the table). Gate 1 is a post-pilot outcome review, not G6's go/no-go | `test_pilot_evidence_plan.py`: every locally counted item names a table and column, or an IPC field, that exists | D (I-1, I-7) |
| P6.3 | Local usage and draft-outcome facts, shown only to the manager (detail below the table). Counts and "N of M" only | `test_usage_facts.py`: counts equal direct SQL counts; no percentages; the sample is flagged; a static check that only `BriefService.accept` sets "accepted" | — |
| P6.4 | Opt-in usage facts in the pilot feedback export: absent by default, previewed, no record ids, refusal counts never included | `test_pilot.py` cases; export equals preview byte for byte | D (I-7) |
| P6.5 | Evidence packet export | Export equals the P3.13 preview; owner-only; a hash mismatch refuses | D (I-4: pilot-export pattern or an ADR 0002 effect; I-2: chain and retention) |
| P6.6 | Governed-artifact manifest (detail below the table) | `test_governed_artifacts.py` | D (I-5: routine vs substantial changes) |
| P6.7 | Consented evaluation-case path (design proposal) for the real-failure cases that Gate 1 condition 7 needs | A GOVERNANCE §3 issue with a recorded decision; until then P6.2 marks condition 7 "not collectable" | D (I-7) |
| P6.8 | Support guide additions and one correction (detail below the table). **Prerequisite of 6.1** | `test_support_guide.py` holds each statement, and asserts that the guide no longer claims a per-item stop | — |

P6.1 in detail. The facts sheet states:

- the bind address, the CSP, and the data folder;
- what is and is not sent;
- the audit gap, until P2.3;
- "updates: not configured", until 6.2b;
- "builds are unsigned until 6.1".

P6.2 in detail. The plan maps each `EVIDENCE.md` Gate 1 condition and
measure to one source: counted locally, consented self-report, recorded by
the steward, or not collectable.

P6.3 in detail. The facts are:

- AI drafts accepted, superseded before acceptance, or still open;
- answers kept;
- exports;
- stops.

P6.6 in detail.

- Every file or constant that governs runtime behavior has a sha256 and a
  declared version.
- CI fails on a change without a version bump. It also fails on a widening
  change without a linked steward decision.
- It reuses P4.1's prompt pins.
- 6.1's release manifest pins this manifest's sha256 rather than repeating
  its entries, so P6.6 does not wait on 6.1.

P6.8 in detail. Additions:

- Extend the existing screenshot rule (`04-support-guide.md:16-18`) to any
  screenshot of real work.
- Backups sit on the same disk, so copy them elsewhere.
- `update-state.sqlite` is not in a backup.
- "Stays on this computer" is not "private from your employer" on a
  hospital-managed laptop.

Correction: the guide calls the per-item button "Stop one piece of work"
(`04-support-guide.md:181`). It should say what the in-app help already
says (`renderer/views.mjs:942`): every **Stop assistants** button stops all
assistants.

#### Outside the Manager Edition

| Id | Step | Exit check | Steward |
|---|---|---|---|
| N-1 | EDENA: a zone-migration approval must be a named approval the actor holds; an Orange request needs the named, held approval id, not any held approval | `test_data_zones.py`: an invented zone-migration approval is denied (today it is allowed, `:96-106`); policy-engine and multi-role tests updated | D (GOVERNANCE §3: Integration Contract behavior change) |
| N-2 | Align the root README with the Directive's Final Command (detail below the table); list the other copies for their owners | `website-alignment.yml` passes; a README assertion in `tests/test_public_governance_artifacts.py` | D (I-6) |

N-2 in detail. Replace "Hermes supports" (`README.md:5`) with the
Directive's Final Command, "Agents propose. Humans judge. Nurses steward."
(`directive.html:57`). Stop presenting Hermes as the chief of staff
(`README.md:3`).

### 5.5 G7 becomes a parked-scope register

G7 today reads "Requires institutional authorization. Out of scope until
then." The proposal keeps that and adds a register, so a parked concept
cannot quietly return as a G3 feature. The register's header says:

> `SAFETY.md` §2–3 apply unchanged to every row. No precondition below
> authorizes raw PHI in agent memory, telemetry, logs, or model context,
> PHI in the hosted service, or pooling data across organizations. Any such
> change needs the steward's explicit written decision (GOVERNANCE.md §3),
> and the default answer is no.

| Parked item (concept ids) | Preconditions |
|---|---|
| Organization identity, RBAC/ABAC, reviewer roles, SLAs, escalation to a second reviewer, service accounts (ARCH-13, PRD-02, UI-03 switchers) | Institutional authorization; EDENA `authenticated_org` plus an approver-authority check, not just a login |
| Organization workspace profile admitting D2 (ARCH-14 at org level) | An ADR with a recorded steward decision; D3 and D4 stay refused |
| Organization memory and an employer policy library (ARCH-08, ARCH-09) | The org profile ADR; a separate store implementing the same `MemoryInterface`; manager-only writes and refuse-not-quarantine kept unless the steward decides otherwise |
| Connector admission contract (ARCH-12) | See below the table |
| Hosted or hybrid mode (MC-05) | A data-boundary decision; the hash-only Florence-X projection is the only candidate payload; an institution-approved environment is the only destination |
| Customer-cloud deployment packet and BAA (ARCH-21) | The institution's own approved environment (`SAFETY.md:30`), never the hosted service (`SAFETY.md:29`); counsel review |
| Risk register, incidents, evaluations with thresholds, change-control workflow (UI-09, PRD-14) | Institutional authorization; the 2.10 definitions (P0.4) |
| Organization retention schedule, connector certification, organization-wide model governance (ARCH-19, ARCH-20 phase 6) | Institutional authorization |
| Staffing and coverage operations; quality and safety event review (ARCH-01, ARCH-05) | A named design partner (`three-lanes/STRATEGY.md:151`); the org profile. Never in the Personal profile |
| Governance, Analytics, and Administration routes (PRD-IA, UI-03) | The rows above |
| **On no gate:** a supervisor agent, multi-agent specialists or swarms, an agent roster (ARCH-04, PRD-04; ARCH-05 beyond the P4.1 manifest) | Florence-X orchestration evidenced, and a lane's evidence showing one bounded assistant call is not enough, and a steward decision (ADR 0005) |

Connector admission contract, in detail:

- A read-only connector:
  - is institution-hosted;
  - is evaluated at yellow/`recommend`, at most D2;
  - uses HTTPS only, with no redirects and no token passthrough;
  - has its manifest pinned by hash.
- A connector that writes or sends is an effect and goes through the
  action boundary. Send and post stay blocked.
- Incident/EHR (D3) and messaging-send connectors are rejected.

Concepts rejected in §7 are not parked and have no preconditions here:
UI-13, PRD-NAME, MC-01, MC-03, MC-06, and SK-03. Bringing any of them back
needs a new ADR that supersedes ADR 0005.

### 5.6 The notes' six phases, mapped

| Note phase | Where it lands |
|---|---|
| 1. Core platform: identity, tenanting, RBAC, connector and workflow registry, audit (0–3 months) | Workspace, audit, and packs exist (G1–G2). The audit chain is P2.3. Identity, tenanting, RBAC, and connectors are G7 |
| 2. Knowledge and retrieval (2–5 months) | Library and packs now (P3.11, P4.6); organization knowledge is G7 |
| 3. Supervisor plus three specialists (4–7 months) | On no gate (§5.5). The assistant task manifest (P4.1) is the bounded replacement |
| 4. Critic, safety harness, red team, scorecards, nurse-led review cadence (6–9 months) | See below the table |
| 5. Three more specialists, connectors, operating console (8–12 months) | Specialists and connectors: on no gate and G7. Console: P3.x and P5.1 to P5.3b |
| 6. Enterprise readiness (12+ months) | P6.1 now. Local continuity already exists as backup and restore (2.8), and P6.8 adds off-disk copies. The rest is G7 (§5.5) |

Phase 4 in detail:

- P4.2, P4.3, and P6.2 cover it; `naio-harness-v2` evaluations stay the
  harness.
- The scheduled nurse-led review maps to the `three-lanes/PLAYBOOK.md`
  §10 cadence, once I-1 accepts the three-lanes documents:
  - weekly review of corrections and refusals;
  - a monthly evaluation run;
  - a per-cycle gate review;
  - an evaluation run before any model change ships.
- Trace analytics stay local facts the manager pulls (P4.4, P6.3).
- The pinned output-check set (P4.2) catches drift in the check itself.
- Organization-level drift and escalation analytics are G7 (PRD-14).

No gate passes on a date. Time envelopes may be stated, and the validation
report already calls the source plan's envelope optimistic
(`00-validation-report.md` §4).

### 5.7 MVP, restated

The notes' three MVP outcomes become:

1. **A governed leadership artifact from structured input.** This is the
   Governed Project Packet pack (P5.5), built on capture (P2.2, P3.1,
   P3.2).
2. **A bounded single-assistant workflow through preview, review,
   acceptance, and the governed export**, in place of "a bounded
   multi-agent workflow". It uses P4.1 and P5.1 to P5.3b.
3. **A per-artifact evidence packet** (P3.13, P6.5). It crosses only as
   hashes, ordinals, and role-form identities. It states that the local
   log is not tamper-evident until P2.3 lands.

The notes' six MVP screens map to existing or proposed screens:

| Note's MVP screen | Here |
|---|---|
| Home | Mission Control (P3.6a, P3.7) |
| Work Board | Board and Tasks (P3.1) |
| Approval Inbox | Approvals (P5.1 to P5.3b) |
| Artifact Review | Brief and pack review (P3.3, P3.4) |
| Agent Registry | The AI assistance profile (P4.4), not a registry |
| Audit Explorer | The Activity record (P3.12, P3.13) |

The notes' deferral list stands, and voice control is also out of scope.

The MVP is not met on the synthetic sample. Until a real manager can
capture their own records, any measure measures only the sample.

## 6. Steward decisions, batched

The review raised about fifty questions only the steward can answer. They
group into seven proposal issues, plus N-1.

**Most of the pilot subset (§5.2) needs no decision** and can start now:
P1.1, P1.3, P2.1, P2.2, P2.4, P3.6a, P3.7, P5.1, P5.3a, P6.1, and P6.8.

Four of its steps wait on a decision:

- P2.3 waits on I-2.
- P3.1, P3.2, and P3.6b wait on I-3.

I-4 decides whether P5.2 and P5.3b join the pilot. So decide I-2, I-3, and
I-4 first.

No pilot step waits on I-1. Accepting ADR 0005 can follow. It unblocks
P0.2b, P0.5's persona and "control plane" cases, P4.3, P5.5, and P6.2.

| Issue | Decides | Unblocks |
|---|---|---|
| **I-1 Scope** | Accept ADR 0005. Accept or not the `three-lanes/` documents (all "Proposed"), on which the refusal set, the packet pack, and Gate 1 rest; if accepted, whether `PLAYBOOK.md` §10 is the Manager Edition's scheduled governance review. Conditions for resuming 1.11 and 4.2c (ADR 0005 §6) | P0.1, P0.2b, P0.5 ("Jarvis" and "control plane" cases), P4.3, P5.5, P6.2 |
| **I-2 Audit** | Chain on `event_log` (recommended), or route manager decisions through the gateway tracer. Whether `SAFETY.md` §4 binds the Personal pilot (recommended: yes, as a 6.1 prerequisite). Where the chain head is kept. Whether audit rows and the AI ledger are kept for the life of the workspace | P2.3 (and through it P3.12's chain status), P6.5 |
| **I-3 Data and people** | The D1/D2 line. Whether owner, reviewer, and decided-by fields are limited to "me" or a role. The header data-rule wording. Whether the named-person rule binds. The 2.10 definitions | P0.4, P3.1, P3.2, P3.6b, P5.4, P5.6 |
| **I-4 Approvals** | An ADR 0002 addendum making the app an approval surface, superseding the older rule that a dashboard does not approve gates. Whether saving an evidence packet is an effect under ADR 0002 or follows the pilot-export pattern | P5.2, P5.3b, P6.5 |
| **I-5 AI scope** | Five questions; see below the table. The cloud provider (4.2b) stays its own decision | P2.5 (assistant-origin case), P4.3, P4.8, P5.7, P6.6 |
| **I-6 Naming and design** | Confirm "Nurse AI OS Manager" and the naming rules (decision 9). The home's name, and four more design questions; see below the table | P3.8 (the name "Today", the EDENA label), P3.9b, P3.10, N-2 |
| **I-7 Measurement and distribution** | Gate 1 as a post-pilot review. Whether any usage counts may enter the pilot export (default: no). Whether the project will ever claim time saved or cost per deliverable, and under what evidence standard. Who receives the security facts sheet. The consented evaluation-case path | P6.1 distribution, P6.2, P6.4, P6.7 |
| **N-1 EDENA approvals** | The Integration Contract change in §5.4 | N-1, and any G7 Orange or zone-migration path |

I-3, the D1/D2 line. The two documents disagree:

- `three-lanes/STRATEGY.md:99` treats manager content that names "real
  units, staffing conditions, and local policy" as D1.
- `02-contract-map.md:34` refuses D2 "confidential organizational"
  material.

I-3, the owner and reviewer fields. Names are not detected, so the
question is whether "me" or a role is enforced or only hinted. If
enforced, the limit is added in the writers behind P2.2's commands, not
only on the screens.

I-5 decides:

- whether to accept the refusal categories, including whether staffing or
  scheduling determinations about named staff are refused;
- whether kept notes may return to a model;
- whether to admit the pack-section task;
- whether prompt-wording changes and narrowing changes are routine (a CI
  version bump plus a change-log line), while widening changes stay
  substantial;
- whether an assistant proposal approved by the owner counts as
  independent review.

I-6 decides:

- whether the home keeps the name "Mission Control" or becomes "Today".
  The name already covers several things here: the Manager home, the
  `naio-os/` dashboard, and the `mission-control/` packets;
- that the Manager assistant gets no persona name, including "Florence";
- whether to split `blocked` and add critical and neutral families;
- whether "EDENA" appears on manager screens;
- whether red-p shows as "Blocked";
- the README tagline, and the other copies of it.

## 7. Concept-by-concept reconciliation

"Today" names the existing mechanism. "Change" names the step or rule that
carries the concept.

### Architecture v2.0 (ARCH)

| Id | Concept | Verdict | Today → change |
|---|---|---|---|
| ARCH-01 | Workspace with five surfaces | Adapt | Mission Control, brief, packs → see the list below the table |
| ARCH-02 | Request router | Adapt | Fixed workflow per command → no router that picks; manager chooses; refusal set before preview (P4.3); JEV may suggest a place to start, after a preview (ADR 0006) |
| ARCH-03 | Session and task state | Adapt | Per-mechanism state machines → kept; resume re-verifies, never re-runs; any multi-step checkpoint lives at Florence-X and stores hashes and stage names only |
| ARCH-04 | Supervisor agent | Defer | Absent → on no gate (§5.5) |
| ARCH-05 | Six specialist agents | Adapt | Two fixed prompts → one assistant task manifest (P4.1); no Staffing or Quality & Safety tasks in the Personal profile |
| ARCH-06 | Critic / verifier | Already have | The checking function exists as a deterministic `_check_output` (`assistant.py:749`), not a second model → pinned regression and red-team set (P4.2); a model critic may only warn |
| ARCH-07 | Escalation manager | Adapt | "Needs my judgment" for the owner → deny-at-proposal with hand-off (P2.5), refusal hand-offs (P4.3); second reviewer at G7 |
| ARCH-08 | Approved knowledge base | Adapt | Reference-only sources → "I checked this source" (P3.11), review state in context (P4.6); employer library at G7 |
| ARCH-09 | Organization memory | Defer | Personal, manager-written memory → G7 store on the same interface |
| ARCH-10 | Session memory | Adapt | Stateless requests by design → no hidden session memory; kept notes in context only by decision (P4.8) |
| ARCH-11 | Audit and evidence ledger | Adapt | Metadata-only `event_log`, receipts, Florence-X bundles → hash chain (P2.3) |
| ARCH-12 | MCP tool and connector layer | Defer | None; send, post, publish, and upload blocked → import and destination allowlists with an egress test now (P1.2); admission contract at G7 |
| ARCH-13 | Identity, RBAC/ABAC | Defer | Owner plus assistant identity → "Proposed by" and "Approved by" on P5.1; RBAC at G7 |
| ARCH-14 | Data classification | Already have | Refusal at capture, D0/D1 only → rule stated on every screen (P3.6b); the notes' four-class vocabulary not adopted |
| ARCH-15 | Minimum-necessary retrieval | Already have | Only this project, exactly as previewed → manager can leave sections out (P4.7) |
| ARCH-16 | Human approval gates | Already have | Hash-bound gates on acceptance, sends, notes, exports, actions → conditional transitions (P2.4), in-app path (P5.1 to P5.3b) |
| ARCH-17 | Observability | Adapt | No telemetry by design → local facts the manager pulls (P4.4, P6.3) |
| ARCH-18 | Nurse ethics control plane | Adapt | Rules scattered across code → one register held to code (P5.4) |
| ARCH-19 | Six control classes | Adapt | Five of six have mechanisms → register headings (P5.4); retention decided in I-2; preservation holds wait for 2.10 (P0.4); no effect is ever re-executed automatically |
| ARCH-20 | Month-based roadmap | Adapt | Gates by go/no-go → phases mapped (§5.6, P0.2b); no gate passes on a date |
| ARCH-21 | Customer cloud, BAA, security artifacts | Adapt | None → security facts sheet now (P6.1); deployment packet and BAA at G7 |

ARCH-01, the five surfaces:

- Huddles: the brief, plus the communication pack's huddle script.
- Coaching: the education and communication packs, addressed to groups or
  roles.
- Planning-level improvement work: a pack (P5.6).
- Staffing and quality operations: G7.
- Approvals: P3.7 and P5.1.

### UI component tree (UI)

| Id | Concept | Verdict | Today → change |
|---|---|---|---|
| UI-01 | AppShell and providers | Adapt | `start(doc, source)` with the Source seam → one shell read model for the status strip; no realtime, permission, or workspace providers; no command palette, notification center, or global search beyond P3.17 |
| UI-02 | Global safety layer | Adapt | Scattered banners → status strip (P3.6a, P3.6b); never "Production" or "No PHI" |
| UI-03 | Navigation | Adapt | 11 flat links → grouped nav (P3.8); no switchers or G7 routes |
| UI-04 | Action dock and overlays | Adapt | Inline notices → quick actions on Mission Control (P3.7); Report concern waits for 2.10 (Help text: P3.15) |
| UI-05 | Home with attention queue | Adapt | Mission Control → actionable judgment queue in two groups (P3.7) |
| UI-06 | Work board and drawer | Adapt | Read-only board → writable (P3.1). See below the table |
| UI-07 | Approvals route | Adapt | None → P5.1 to P5.3b. See below the table |
| UI-08 | Agent registry | Adapt | One provider slot → one assistant profile (P4.4), not a registry |
| UI-09 | Governance route (NIST AI RMF) | Adapt | None → Activity record and "How this was made" (P3.12, P3.13); risk register, incidents, evaluations, and change control at G7 |
| UI-10 | Reusable primitives | Adapt | `badge()` → declared status semantics (P3.9a, P3.9b); tier function with P3.7 |
| UI-11 | Shared data contracts | Adapt | `nurse-manager-ipc@1` stays the only contract. See below the table |
| UI-12 | First-build order | Adapt | Different order already built → §5.2 |
| UI-13 | React/Next.js | Reject | Plain ES modules with no framework (`nurse-manager/README.md`), under the loopback host's strict CSP (`devhost.py` `SECURITY_HEADERS`); ADR 0005 §2.1 makes this binding, with no build step |

UI-06, the work board and drawer:

- The project dashboard stays the detail view.
- There are no task dependencies or comments; they are a post-pilot
  candidate that needs a decision.
- Board and Tasks are the list views. There is no timeline.
- There are no SLA clocks and no "next best action".

UI-07, the approvals route:

- Approval is once per action only.
- "Edit then approve" means edit, new draft, accept, new proposal.
- An approval has no expiry. It already goes stale at the recheck when
  anything it was bound to changes.
- Escalation and SLA are G7.

UI-11, the shared data contracts:

- ApprovalRequest is the existing `Action`.
- AuditEvent becomes a metadata-only `ActivityEvent`.
- The notes' types and vocabularies are not ported.

### Dashboard requirements (PRD)

| Id | Concept | Verdict | Today → change |
|---|---|---|---|
| PRD-NAME | Product name and promise | Reject (the name) | The name conflicts with `05-hermes-review.md` §2.3 → "Nurse AI OS Manager"; guard test (P0.5). The promise is kept, adapted (see below the table) |
| PRD-01 | Unified operational home | Already have | Mission Control → P3.6a, P3.6b, P3.7 |
| PRD-02 | Role-based experience | Defer | One person by design → G7 |
| PRD-03 | Outcome-based intake | Adapt | No intake → capture forms (P3.1, P3.2); no sensitivity selector; refusal with the typed text kept |
| PRD-04 | Agent roster | Defer | One assistant → the P4.4 profile can become a roster's first entry if the steward admits a second assistant |
| PRD-05 | Work orchestration | Adapt | Writers unexposed → P2.1, P2.2, P3.1 |
| PRD-06 | Structured review states | Adapt | Draft, accepted, superseded → edit as new draft (P3.3), history and compare (P3.4); "published" means exported; "sent" stays impossible |
| PRD-07 | Approval gates | Adapt | Approve once, fail-closed recheck → in-app path, reject and revoke; no approve-for-session |
| PRD-08 | Safe intervention | Adapt | Stop, resume, disconnect → task pause from screens (P3.1), revoke (P5.3a); support-guide Stop wording corrected (P6.8) |
| PRD-09 | Evidence-first outputs | Already have | Citation on every line, draft banners → cited-records list (P3.5); no confidence score |
| PRD-10 | End-to-end traceability | Adapt | Ids exist, unjoined → prompt versions (P4.1), "How this was made" (P3.13) |
| PRD-11 | Searchable audit trail | Adapt | Unsearchable `event_log` → chain (P2.3), Activity record (P3.12); arguments only as hashes |
| PRD-12 | Policy-aware action control | Already have | Profile table re-read, EDENA, policy version stored → plain-word reasons on P5.1 |
| PRD-13 | Quality measurement | Adapt | None → draft-outcome facts as counts (P6.3); no percentages or time saved |
| PRD-14 | Risk monitoring | Defer | None → G7 and 2.10; measuring people by segment is rejected for the Personal profile |
| PRD-15 | Data-boundary controls | Already have | Onboarding, capture refusals, blocked effects → rule on every screen (P3.6b) |
| PRD-16 | Model and cost governance | Adapt | Daily limit and pre-send budget check exist, spend hidden → spend and the local-model budget rule shown (P4.4); budget setter with 4.2b |
| PRD-17 | Workflow library | Already have | Reviewed, hash-pinned packs → no in-app authoring |
| PRD-18 | Change control | Adapt | Repository governance → governed-artifact manifest (P6.6) |
| PRD-SCREENS | Command center in 30 seconds | Adapt | Mission Control → "30 seconds" is a pilot test question (P3.16, P6.2), not a claim; "Act on these" and "For information" groups (P3.7) |
| PRD-IA | Information architecture | Adapt | Flat → P3.8; G7 branches recorded in §5.5, not stubbed |
| PRD-DESIGN | Calm clinical operations | Adapt | Already the shipped direction → status semantics as data, split `blocked`, plain labels (P3.8, P3.9a, P3.9b) |
| PRD-BOUNDARY | Clinical operating boundary | Already have | Stricter than the note → operating-boundary register (P5.4). The notes' first workflows are mapped below the table |
| PRD-METRICS | Success measures | Adapt | None → see below the table |
| PRD-MVP | Three MVP outcomes | Adapt | → §5.7 |

PRD-NAME, the promise, adapted: "When I need to produce, review, or follow
up on leadership work, I want one place that shows what needs my judgment
and what is done, so I can move faster and stay accountable."

PRD-BOUNDARY, the notes' first workflows:

| Workflow | Here |
|---|---|
| Leadership communications | Communication pack |
| Staff education plans; educational content | Education pack |
| QI charter | Improvement pack, at planning level (P5.6) |
| Project coordination | Capture (P2.2, P3.1) |
| Policy-change summaries | The committee pack's policy or procedure draft, plus a communication-pack message. Employer policy text is held back by the D1/D2 line (I-3); employer policy libraries are G7 |
| Literature synthesis from outside sources | Not admitted. Sources stay references (P3.11), and no outside text reaches a model; changing that needs I-5 |
| Policy monitoring | Not admitted. The Personal profile has no connectors (G7) |

PRD-METRICS, the measures:

- `EVIDENCE.md` measures (P6.2, P6.3).
- Safety and governance are held as tested properties and counts, never
  rates:
  - stops are counted (P6.3), and stop latency is already tested (5.3,
    `test_control.py`);
  - trace completeness is "How this was made" on every revision (P3.13);
  - the named owner and approval records are "Proposed by" and "Approved
    by" (P5.1);
  - prompt and policy versions are pinned (P4.1, P6.6).
- Output quality is draft outcomes (P6.3), plus reviewer acceptance and
  rework from `EVIDENCE.md` §6 (P6.2). Edit distance is not computed.
- No weekly-active targets, no ROI from time saved, no equity segmentation
  of people.
- Cost per deliverable waits on I-7. Incident counts are G7 (2.10).

### JARVIS Mission Control (MC) and the community research (SK)

| Id | Concept | Verdict | Today → change |
|---|---|---|---|
| MC-01 | Five-layer OpenClaw stack | Reject | SQLite behind `Store`, stdlib loopback host → ADR 0005 records the existing layer mapping; no git-as-truth, Node, or WebSocket backend |
| MC-02 | Goal → tasks → review → human lifecycle | Already have | The human task lifecycle exists, with evidence-gated completion → the lead-agent delegation part is not adopted |
| MC-03 | Shared operational memory | Reject | Agent-written memory is refused by design; persistence and recovery already exist → given-up brief pointer (P3.14) |
| MC-04 | Dashboard surfaces | Adapt | Board, schedule, assistants at work → writable board; messaging and integrations rejected; activity feed is P3.12 |
| MC-05 | Local, hosted, hybrid | Defer | Local loopback only → hosted and hybrid at G7 |
| MC-06 | Named coordinator persona | Reject | No persona → kept principle: the dashboard makes work visible and governable, it does not think (P3.10, ADR 0005) |
| MC-07 | Healthcare safety for mission control | Adapt | Mostly present → tamper-evident log (P2.3); screenshot rule extended (P6.8) |
| SK-01 | OS, chief-of-staff, command-center story | Already have | Present in the README and the Directive → the README aligned to the Final Command (N-2) |
| SK-02 | Plug-and-play blueprints | Already have | Packs and the sample → called "packs", never "blueprints" (P3.10) |
| SK-03 | Cinematic dark command-center look | Reject | Calm Day and Night Studio tokens stay |
| SK-04 | Gated, unverifiable material | Already have | Repository rules treat it as non-evidence → this document cites none of the notes' footnotes |

## 8. Risks

- **Scope inflation against a blocked critical path.** About 60 new steps
  arrive while the pilot waits on signing. §5.2 is the answer: build the
  pilot-ready subset and treat the rest as post-pilot.
- **The steward is a bottleneck.** About fifty questions, and many steps
  blocked on one person. §6 batches them into seven issues, and says which
  three to decide first.
- **"Stays on this computer" is not "private from the employer".** Pilot
  laptops may be hospital-managed. IT, e-discovery, or a device audit can
  read the workspace file: kept notes, memory, usage facts, refusal counts,
  and the typed actor names. Weigh this before computing any fact (P6.3),
  and say it at onboarding and in P6.1.
- **Instructions hidden in records.** The output check stops invented
  citations, but not a model following an instruction typed inside a cited
  record. P4.2's red-team cases matter more once a cloud provider (4.2b)
  is chosen.
- **Clinical-sounding names invite clinical data.** A screen named
  "Staffing" or "Quality & Safety" invites workforce and incident detail
  that the privacy screen cannot catch (names are not detected). No route
  carries those names.
- **Packs and tasks become agents by another name.** Each new pack or
  assistant task widens what a model sees. The manifest (P4.1) and the
  register (P5.4) must be the only way in.
- **Over-blocking pushes managers elsewhere.** A manager may copy unit data
  into another AI service. `three-lanes/STRATEGY.md` treats routine bypass
  as a stop condition. The register cannot detect it, so the pilot should
  ask.
- **Evidence read as audit-grade.** The packet (P3.13, P6.5) must say it is
  not tamper-evident until P2.3 lands, and must carry no workspace or
  revision ids.
- **Usage facts read as a performance record.** Facts stay with the
  manager. No measure is attributable to a named person for any employment
  purpose, and none is shared with an employer at individual grain
  (`EVIDENCE.md:103`). This proposal also keeps refusal counts out of the
  pilot feedback export (P6.4).
- **Unverified citations leak into repository documents.** The notes'
  footnotes were not read. Neither this document nor ADR 0005 cites them,
  and the voice guide (P3.10) should say so for future work
  (`CONTRIBUTING.md` §4).

## 9. What this document does not do

- It does not change an accepted ADR. ADR 0005 is proposed alongside it
  with status "Proposed".
- It does not change the status of any step in `01-build-steps.md`, or add
  steps there. That happens per step, as the steward accepts them.
- It does not change code. The defects in §2 are recorded as steps.
- It does not claim the Manager Edition meets `SAFETY.md` §4 today. It
  states that it does not, and how that is closed.
