---
title: "ADR 0005: Manager Edition scope against the v2.0 concept notes"
status: Proposed
date: 2026-10-04
decided_by: pending (project steward, GOVERNANCE.md §1)
decided_on: pending
authorship: Substantially AI-generated (Claude Code) with human review pending
---

# ADR 0005: Manager Edition scope against the v2.0 concept notes

## Context

Five research notes bear on the Manager Edition. They describe:

- a supervisor with six specialist agents;
- a "Hermes Control Plane" dashboard, built in React/Next.js;
- MCP connectors;
- a JARVIS-style mission control, with a coordinator persona and
  agent-written shared state.

`06-architecture-direction.md` checks each of their 70 concepts against
this repository. It finds that most of them fit only once they are
reshaped. Some conflict with ADRs 0001–0004, `SAFETY.md`, or the step 0.8
review.

That review found three places that each need a recorded decision:
orchestration, the console stack and naming, and deployment with
connectors. Without one recorded decision, later work could quietly bring
back the notes' vocabulary and architecture. That would be a substantial
change made without the decision `GOVERNANCE.md` §3 requires. This ADR
records the scope in one place.

The notes are unverified research inputs. Their footnotes were not read,
and this ADR cites none of them.

## Decision

### 1. Orchestration

1. The Manager Edition core is a single-assistant, human-orchestrated
   system. It hosts none of these:
   - a supervisor agent;
   - a router agent;
   - specialist agents;
   - a coordinator persona;
   - memory written by agents.
2. Routing is the manager's explicit choice of workflow on screen, plus a
   deterministic refusal set that runs before any AI preview. No model
   assigns risk, picks a workflow, or releases text, and no model can open
   a gate. Under ADR 0006, the JEV classifier may suggest a workflow (the
   manager still picks), and may add a hold or a refusal. It never removes
   one.
3. "Specialist" capability arrives only as an entry in one reviewed
   assistant task manifest.
   - Each entry declares a version, a prompt hash, a data scope, and an
     output contract.
   - Code caps the data scope, and the manifest can only narrow it. This is
     the same discipline ADR 0002 applies to effects.
   - The Personal profile admits no Staffing or Quality & Safety task.
4. Any multi-step orchestration belongs at the Florence-X integration point
   (ADR 0001). It needs all three of these:
   - Florence-X orchestration, evidenced;
   - a lane's evidence that one bounded assistant call is not enough;
   - a steward decision.

   Until then it sits on no gate.

### 2. Console stack and naming

1. The screens stay plain ES modules, with no framework and no build step,
   behind the `Source` seam. They are served by the stdlib loopback host
   under the current Content Security Policy. React and Next.js are not
   adopted.
2. The product and edition name stays "Nurse AI OS Manager".
   - "Hermes Control Plane" and "Ask Hermes" put Hermes inside a product or
     control name. `05-hermes-review.md` §2.3 lists that as not
     acceptable.
   - This ADR also excludes two more names from any Manager Edition
     product, screen, button, download, or persona:
     - "Jarvis" (there is no coordinator persona, §1.1);
     - "control plane" (kept as the term for Florence-X and EDENA).
3. The design rule taken from the notes is: the dashboard makes work
   visible and governable; it does not think.

### 3. Deployment

1. The Personal Manager profile runs only on the manager's own computer.
   - Today that is the local loopback app with a per-launch token
     (ADR 0003).
   - The Hermes Desktop host that ADR 0003 defers (step 1.11) may later
     replace that HTTP transport behind the `Source` seam. It stays on the
     manager's own computer, and it must meet the conditions in §6.
2. Hosted and hybrid modes are not offered for manager records.
   - A hybrid channel is a G7 data-boundary decision.
   - The hash-only Florence-X projection is the only candidate payload.
   - An institution-approved environment is the only destination.

### 4. Connectors

1. The Personal profile has no connectors, MCP or otherwise.
   - The on-screen promise "does not connect to your employer's systems"
     is shown at every first run. `test_app_browser.mjs` checks that it is
     shown.
   - Proposed step P1.2 will hold the promise mechanically. An import
     allowlist alone cannot: an allowed module could add a new destination
     without a new import. So P1.2 also pins every outbound destination to
     one allowlist where the connection is made, and adds a runtime egress
     test that fails on any other destination.
2. A connector admission contract is a G7 design item.
   - A read-only connector is a data source gated by EDENA. It is
     institution-hosted and evaluated at yellow/`recommend`, at most D2. It
     uses HTTPS only, with no redirects and no token passthrough.
   - A connector that writes or sends is an effect and goes through the
     action boundary. Send and post stay blocked.
   - Incident/EHR (D3) and messaging-send connectors are rejected.

### 5. Parked scope

1. These wait for institutional authorization (G7):
   - organization identity and RBAC;
   - reviewer roles, and escalation to a second reviewer;
   - organization memory and knowledge;
   - risk register, incidents, and change-control workflows;
   - Governance, Analytics, and Administration routes;
   - customer-cloud deployment and BAA work;
   - staffing operations and quality-event review. These are for the
     organization profile only, and rejected for the Personal profile.
2. `SAFETY.md` §2–3 apply unchanged to every parked item. No precondition
   authorizes raw PHI in agent memory, telemetry, logs, or model context.
   None admits PHI to the hosted service or pools data across
   organizations.
3. In the Personal profile, the dashboard requirements note's appeal,
   override, and feedback loop already exists. It is the manager's power to
   reject or supersede, plus pilot feedback. It is not rebuilt as a
   separate feature.

### 6. Conditions on resuming deferred Hermes work

Resuming step 1.11 (Hermes Desktop host) or step 4.2c (Hermes session map)
requires:

1. No Hermes-named surface appears in the Manager Edition.
2. No Hermes session holds conversation state outside the hash-bound
   preview and the text-free request ledger.
3. The import and destination allowlists (proposed step P1.2) are extended
   only in the same PR as a decision that admits the new runtime.
4. Plugins are treated as unsandboxed, and every effect is still decided in
   the Python backend (validation report, correction 6).

## Alternatives considered

- **Adopt the v2.0 architecture as written.** Rejected, for three reasons:
  - It moves mission lifecycle into the manager core, against ADR 0001.
  - It needs connectors and D2+ data that the Personal profile refuses
    (`SAFETY.md` §3; `02-contract-map.md` §3).
  - It adds autonomy above the EDENA `recommend` ceiling (ADR 0002).
- **Specialist agents inside the Personal profile, each at `recommend`.**
  Rejected.
  - Each agent would widen what a model sees, without a reviewed manifest
    entry.
  - Staffing and quality work needs data above D1, or determinations about
    named people.
  - Agents add nothing that a reviewed task entry does not.
- **A React/Next.js console.** Rejected.
  - The shipped renderer is framework-free ES modules
    (`nurse-manager/README.md`). It is served under a strict CSP by the
    ADR 0003 loopback host, with system fonts only, so it works offline.
  - §2.1 makes this binding.
  - A framework adds dependencies to inventory and a build step to trust.
- **A hosted dashboard with local execution (hybrid).** Deferred to G7.
  Titles, purposes, and file names carry meaning that a "metadata only"
  channel would leak.

## Consequences

- The notes' useful intent is kept as steps in
  `06-architecture-direction.md` §5. That intent covers:
  - in-app approvals;
  - a tamper-evident audit stream;
  - a status strip and an actionable home;
  - versioned prompts;
  - evidence views;
  - a rules register.
- A proposal that brings back a router, supervisor, specialist agent,
  persona, connector, or hosted surface needs a new ADR that supersedes
  this one.
- The naming guard (proposed step P0.5) and the import and destination
  allowlists with their egress test (proposed step P1.2) will hold sections
  2 and 4 mechanically, not only by review.

## Decision record

Not yet decided.

- This is a substantial change under `GOVERNANCE.md` §3. It needs a
  proposal issue, an open comment period, and the steward's decision
  recorded in the issue.
- When the steward decides, the decision is copied here with who decided,
  when, and how the decision was given. These are the same fields the
  decision records of ADRs 0001–0004 carry.
- Until then the status stays "Proposed".
- The steps that depend on this ADR are listed under I-1 in
  `06-architecture-direction.md` §6. None of them is treated as unblocked.
- P1.2, and the Hermes cases of P0.5, rest on `05-hermes-review.md` §2.3
  and the existing action boundary, not on this ADR. They may be built
  first. P0.5's "Jarvis" and "control plane" cases take effect when this
  ADR is accepted.
