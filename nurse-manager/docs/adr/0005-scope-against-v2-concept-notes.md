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

Five research notes propose a "Nurse AI OS Architecture v2.0". They
describe a supervisor with six specialist agents, a "Hermes Control Plane"
dashboard built in React/Next.js, MCP connectors, and a JARVIS-style mission
control with a coordinator persona and agent-written shared state.
`06-architecture-direction.md` checks each of their 70 concepts against
this repository. It finds that most of them fit only once they are
reshaped. Some conflict with ADRs 0001–0004, `SAFETY.md`, or the step 0.8
review.

Three areas of that analysis each proposed an ADR of their own. Without one
recorded decision, later work could quietly bring back the notes'
vocabulary and architecture. That would be a substantial change made
without the decision `GOVERNANCE.md` §3 requires. This ADR records the
scope in one place.

The notes are unverified research inputs. Their footnotes were not read,
and this ADR cites none of them.

## Decision

### 1. Orchestration

1. The Manager Edition core is a single-assistant, human-orchestrated
   system. It hosts no supervisor agent, no router agent, no specialist
   agents, no coordinator persona, and no memory written by agents.
2. Routing is the manager's explicit choice of workflow on screen, plus a
   deterministic refusal set that runs before any AI preview. No model
   assigns risk, picks a workflow, releases text, or holds a gate.
3. "Specialist" capability arrives only as an entry in one reviewed
   assistant task manifest. Each entry declares a version, a prompt hash, a
   data scope, and an output contract. Code caps the data scope and the
   manifest can only narrow it, the same discipline ADR 0002 applies to
   effects. The Personal profile admits no Staffing or Quality & Safety
   task.
4. Any multi-step orchestration belongs at the Florence-X integration point
   (ADR 0001). It needs three things: Florence-X orchestration evidenced; a
   lane's evidence showing that one bounded assistant call is not enough;
   and a steward decision. Until then it sits on no gate.

### 2. Console stack and naming

1. The screens stay plain ES modules behind the `Source` seam. They are
   served by the stdlib loopback host under the current Content Security
   Policy. React, Next.js, and any build step are not adopted.
2. The product and edition name stays "Nurse AI OS Manager". "Hermes
   Control Plane", "Ask Hermes", "Jarvis", and "control plane" never name a
   Manager Edition product, screen, button, download, or persona
   (`05-hermes-review.md` §2.3, `TRADEMARKS.md` §3). "Control plane" stays
   the term for Florence-X and EDENA.
3. The design rule taken from the notes is: the dashboard makes work
   visible and governable; it does not think.

### 3. Deployment

1. The Personal Manager profile has one deployment mode: local loopback
   with a per-launch token (ADR 0003).
2. Hosted and hybrid modes are not offered for manager records. A hybrid
   channel is a G7 data-boundary decision. The hash-only Florence-X
   projection is the only candidate payload. An institution-approved
   environment is the only destination.

### 4. Connectors

1. The Personal profile has no connectors, MCP or otherwise. The on-screen
   promise "does not connect to your employer's systems" is a contract held
   by tests.
2. A connector admission contract is a G7 design item.
   - A read-only connector is a data source gated by EDENA. It is evaluated
     at yellow/`recommend`, at most D2, institution-hosted, HTTPS only, with
     no redirects and no token passthrough.
   - A connector that writes or sends is an effect and goes through the
     action boundary. Send and post stay blocked.
   - Incident/EHR (D3) and messaging-send connectors are rejected.

### 5. Parked scope

1. These wait for institutional authorization (G7):
   - organization identity and RBAC
   - reviewer roles and escalation to a second reviewer
   - organization memory and knowledge
   - risk register, incidents, and change-control workflows
   - Governance, Analytics, and Administration routes
   - customer-cloud deployment and BAA work
   - staffing operations and quality-event review
2. `SAFETY.md` §2–3 apply unchanged to every parked item. No precondition
   authorizes raw PHI in agent memory, telemetry, logs, or model context.
   None admits PHI to the hosted service or pools data across
   organizations.
3. In the Personal profile, the PRD's appeal, override, and feedback loop
   is the manager's power to reject or supersede, plus pilot feedback. It
   is not rebuilt as a separate feature.

### 6. Conditions on resuming deferred Hermes work

Resuming step 1.11 (Hermes Desktop host) or 4.2c (Hermes session map)
requires that:

1. no Hermes-named surface appears in the Manager Edition;
2. no Hermes session holds conversation state outside the hash-bound
   preview and the text-free request ledger;
3. the import allowlist (proposed step P1.2) is extended only in the same
   PR as a decision that admits the new runtime;
4. plugins are treated as unsandboxed, and every effect is still decided
   in the Python backend (validation report, correction 6).

## Alternatives considered

- **Adopt the v2.0 architecture as written.** Rejected for three reasons.
  It moves mission lifecycle into the manager core, against ADR 0001. It
  needs connectors and D2+ data the Personal profile refuses (`SAFETY.md`
  §3; `02-contract-map.md` §3). And it adds autonomy above the EDENA
  `recommend` ceiling (ADR 0002).
- **Specialist agents inside the Personal profile, each at `recommend`.**
  Rejected. Each agent would widen what a model sees without a reviewed
  manifest entry. Staffing and quality work needs data above D1, or
  determinations about named people. Agents add nothing a reviewed task
  entry does not.
- **A React/Next.js console.** Rejected. ADR 0003 and the offline,
  no-build, system-font rules already cover the need. A framework adds
  dependencies to inventory and a build step to trust.
- **A hosted dashboard with local execution (hybrid).** Deferred to G7.
  Titles, purposes, and file names carry meaning that a "metadata only"
  channel would leak.

## Consequences

- The notes' useful intent is kept as steps in
  `06-architecture-direction.md` §5. That intent covers in-app approvals, a
  tamper-evident audit stream, a status strip, an actionable home, versioned
  prompts, evidence views, and a rules register.
- Proposals that bring back a router, supervisor, specialist agent,
  persona, connector, or hosted surface need a new ADR that supersedes
  this one.
- The naming guard (proposed step P0.5) and the import allowlist
  (proposed step P1.2) hold sections 2 and 4 mechanically, not only by
  review.

## Decision record

Not yet decided. This is a substantial change under `GOVERNANCE.md` §3.
It needs a proposal issue, an open comment period, and the steward's
decision recorded in the issue. Alternatively, the steward may record an
explicit written decision here, following the pattern of ADRs 0001–0004.
Until then the status stays "Proposed", and no step that depends on this
ADR is treated as unblocked.
