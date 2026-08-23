---
title: "Three-Lane Implementation Plan"
status: "Proposed staged plan"
version: "0.1"
date: "2026-08-23"
applicability: "Planning record. Each cycle is conditional on the prior gate. It creates no product, cohort, pricing, partnership, institutional relationship, clinical validation, or authority to process PHI, and it schedules no work that any person is committed to perform."
---

# Three-Lane Implementation Plan

Three 90-day cycles, run in order, each with one lane, one artifact, one gate. Discovery for all three archetypes runs continuously underneath ([PLAYBOOK §1](PLAYBOOK.md#1-discovery-runs-in-every-cycle)). Nothing in a later cycle begins because its cycle number arrived; it begins because the prior gate passed.

The plan is written for a founder-constrained team. Where a task cannot be delegated, it says so, because the binding resource here is not engineering hours.

---

## Cycle 0 — Two weeks before Cycle 1

Short, unglamorous, and the difference between a build and a guess.

| # | Deliverable | Done means |
|---|---|---|
| 0.1 | **Five roles named for the Manager lane** | A real person or a specific title in each of User, Buyer, Beneficiary, Approver, Steward ([SEGMENTS §4](SEGMENTS.md#4-role-separation)) |
| 0.2 | **Six to ten design partners recruited** | Nurse managers, QI, informatics, and educators-with-program-responsibility who have agreed to two sessions each, not to a demo |
| 0.3 | **Five real artifacts collected** | Actual packets, proposals, or committee submissions these people have had to produce, with identifiers removed by them before sharing |
| 0.4 | **Two approvers interviewed** | People who *receive* those artifacts, asked what makes them send one back |
| 0.5 | **Refusal set v0.1 drafted** | Written, testable, and reviewed against the governance kit ceiling |
| 0.6 | **Rights position stated** | Which sources may be ingested, which may be cited, which may never enter a distributable artifact |

**Non-goal for Cycle 0:** building anything. A prototype at this stage answers a question nobody has asked yet.

---

## Cycle 1 — The Manager (days 1–90)

### 1.1 The bounded outcome

> **Turn one no-PHI unit, workforce, education, quality, or AI-adoption problem into a review-ready Governed Project Packet.**

One user segment. One problem shape. One input contract. One finished output. One safety boundary. One measurable success criterion. Anything that does not serve that sentence is Cycle 2 or later.

### 1.2 The input contract

The intake collects exactly this, refuses everything else at the door, and records each refusal visibly:

**Accepted:** the problem in the user's words; the groups of people affected, described by role and setting; the stated goal; the authority context — who decides, who must be consulted, what the user may not decide; time and resource constraints; user-supplied sources with a rights attestation; local policy references *by citation*, not by paste, unless the user attests they may share them.

**Refused, with a named reason shown to the user:** PHI or any reconstructable patient narrative; identifiable staff performance, discipline, or attendance data; employer-confidential or vendor-confidential material the user cannot attest to; rights-encumbered content (test banks, licensed terminology, textbook text); requests for clinical decision support; requests to determine, score, or rank a named person.

A refusal is not a dead end. Each one offers the nearest permitted alternative — a synthetic equivalent, a de-identified restatement, or a citation-only path.

### 1.3 The artifact: Governed Project Packet v0.1

Fifteen sections, fixed for the whole cycle. The schema does not grow mid-cycle; a section that partners keep asking for is logged for v0.2 and left out.

| # | Section | The discipline it enforces |
|---|---|---|
| 1 | Problem definition | Stated as a condition, not as a solution in disguise |
| 2 | Affected people | Staff, patients, families, and community named by group |
| 3 | Goals and success measures | Measurable, with the measure chosen before the intervention |
| 4 | Baseline and missing information | **What is unknown is listed, not filled in** |
| 5 | Workflow map | Current state before proposed state |
| 6 | Evidence and policy sources | Cited with provenance and rights basis |
| 7 | Stakeholder and authority map | Who decides, consults, informs, approves |
| 8 | Data boundary | Data classes touched; the EDENA disposition of the work itself |
| 9 | Staff-burden assessment | Whose work increases, in whose minutes |
| 10 | Risks and alternatives | Including the alternative of doing nothing |
| 11 | Decision owner and action owner | Two named humans; never the system |
| 12 | Monitoring and reassessment | What is watched, by whom, how often |
| 13 | Stop and escalation conditions | What would end this, and who may end it |
| 14 | Communication and implementation plan | Who hears what, when |
| 15 | Unresolved concerns | **Dissent survives to the reviewer intact** |

Sections 4 and 15 are the ones a general-purpose assistant will not produce unprompted and the ones a reviewer notices first. They are the product.

**Export:** a review-ready document the user can hand to a committee, plus the session record behind it. Both are the user's; neither is retained as training material without separate, revocable, specific consent.

### 1.4 Build increments

| Weeks | Increment | Exit condition |
|---|---|---|
| 1–2 | **Intake contract and refusal set**, running end to end with no drafting at all | Every refusal in §1.2 fires on a crafted input and states its reason |
| 3–4 | **Section engine and packet schema**, browser-first, no installation | A packet renders with every section either answered or explicitly marked missing |
| 5–6 | **Source and rights ledger; provenance and uncertainty display** | No claim renders without a source, an inference marker, or an unknown marker |
| 7–8 | **Guided workflow and correction capture**; ten supervised sessions with design partners | Ten packets exist, each from a real problem the partner brought |
| 9–10 | **Reviewer acceptance round** — partners submit packets to their actual approvers | Written reviewer feedback on at least six packets |
| 11 | **Evaluation harness seeded** from the cycle's own failures | Twenty stored cases run against the current model on demand |
| 12 | **Price test** — the Nurse-Led AI Governance Readiness Sprint offered to partners | A yes, a no, or a counter-offer from every partner asked |

Two things deliberately absent from this list: authentication beyond what a browser session needs, and any institutional deployment surface. Both are Cycle 4 questions and both would eat this cycle.

### 1.5 Governance disposition

**Yellow risk · D1 data · Recommend ceiling.** Institution-specific work is Yellow even without PHI. Every packet carries a named human reviewer, approval of the exact artifact rather than of the workflow, an audit trail, and no execution of any external action by the system. The system drafts and recommends; the user submits, sends, schedules, and decides.

### 1.6 Founder-only versus delegable

| Only the founder can do | Must be delegated or the cycle fails |
|---|---|
| Design-partner recruitment through nursing credibility | Front-end build of the section engine |
| Reading a packet and knowing what a committee will reject | Evaluation harness plumbing |
| The Sprint delivery and the pricing conversation | Session scheduling and note transcription |
| Judgment calls on refusals and scope | Accessibility and human-factors review |

The recurring failure mode is the founder doing column two at the expense of column one.

### 1.7 Cycle 1 stop conditions

Stop and re-plan if any of these holds at day 90: no approver accepted a packet with less rework than their status quo; no partner brought a second problem unprompted; the packet's value came from the drafting rather than from sections 4, 8, 9, 13, and 15; or any partner asked to put PHI in and the honest answer was that the workflow needed it.

---

## Cycle 2 — The Certification Learner (days 91–180)

**Begins only if the Cycle 1 gate passes.**

### 2.1 The bounded outcome

> **Convert a nurse's certification goal, baseline, available time, and own source materials into a governed learning plan with weekly actions, progress evidence, reflection, and scheduled reassessment.**

Not "pass the exam." No pass-rate claim, no competence claim, no score prediction — in the product, in the marketing, and in the measures.

### 2.2 The dominant constraint is rights, not engineering

This lane's failure mode is legal, not technical. Certification content, test banks, licensed terminology, and textbook material carry restrictive rights, and a learning product is exactly the shape that ingests them by accident.

The rule for the cycle: **the system reasons over the learner's own attested materials and openly licensed sources, and generates original practice content. It does not reproduce, reconstruct, or approximate proprietary test items.** The source and rights ledger built in Cycle 1 becomes a gate rather than a record: a source without a permission basis cannot enter a plan, and cannot appear in anything exported.

Before the cycle: source and rights registers maintained, production language original, research evidence separated from distributable artifacts, licenses obtained before any terminology mapping, clean-room drafting procedure written, removal and rollback paths defined, and IP counsel engaged before any commercial corpus or ontology release.

### 2.3 What is new on the spine

Only four things, which is the point of the spine:

1. **Plan schema** — goal, baseline, time budget, weekly actions, evidence, reflection prompts, reassessment date.
2. **Longitudinal memory** — the first real test of whether persistent personal context creates value, and the first place where forgetting must be as easy as remembering.
3. **Reliance instrumentation** — measuring whether the learner is thinking with the system or outsourcing to it ([EVIDENCE §4](EVIDENCE.md#4-appropriate-reliance-and-the-deskilling-check)).
4. **Sponsorship boundary** — when an employer pays, the learner's reflections and self-identified weaknesses are not visible to the sponsor. Enforced in the data model, defaulted closed, and stated to both parties at intake.

### 2.4 Build increments

| Weeks | Increment | Exit condition |
|---|---|---|
| 1–2 | Rights gate on the ledger; learner intake with attestation | An unattested source cannot enter a plan |
| 3–4 | Plan schema and first-plan workflow | A nurse produces a plan they say they will actually follow |
| 5–8 | Weekly cycle: act, record evidence, reflect, adjust; memory across sessions | Ten learners complete four weeks each |
| 9–10 | Reassessment and plan revision; the commit-then-compare pattern in practice | Plans change for stated reasons, recorded |
| 11 | Reliance and unassisted checks | Baseline reliance measures exist for every active learner |
| 12 | Direct price test to individuals | Individual nurses asked to pay their own money |

### 2.5 Cycle 2 stop conditions

Stop if: fewer than half of active learners return in week four without a prompt; reliance measures move toward dependence; the plan's value is indistinguishable from a generic study schedule; or any part of the workflow requires proprietary material to be useful.

---

## Cycle 3 — The Builder–Organizer (days 181–270)

**Begins only if the Cycle 2 gate passes and the contribution preconditions hold.**

### 3.1 The bounded outcome

> **Turn one nurse-led initiative into a governed action system: defined audience, value proposition, stakeholder map, work plan, evidence ledger, communication assets, decision log, measures, and review cadence.**

### 3.2 Preconditions, not features

Cycle 3 does not begin until contribution can be made **consented, rights-aware, attributed, versioned, evaluated, revocable, and separated from PHI and employer-confidential material.** These are entry conditions. A pack that cannot be withdrawn by its author is not shippable, and a marketplace assembled without them is a liability.

Research first splits the three subgroups — entrepreneur, community developer, organizer — and the cycle builds for whichever one showed a repeated artifact in discovery. It does not build for all three.

### 3.3 The real deliverable

The initiative artifact is the visible output. The actual test is the **capability pack**: can a user turn their own validated workflow into something another nurse can run, with attribution, a version, an evaluation bundle, a rights statement, and a revocation path? That is the platform question, and it is answered by two or three packs that a second user successfully runs — not by a catalog.

### 3.4 Build increments

| Weeks | Increment | Exit condition |
|---|---|---|
| 1–2 | Subgroup selection from discovery; initiative schema | One subgroup named, with the artifact they repeatedly produce |
| 3–5 | Initiative workflow on the spine; evidence ledger and decision log | Five initiatives documented end to end |
| 6–8 | Pack format: manifest, version, attribution, rights statement, evaluation bundle, revocation | A pack round-trips: authored, versioned, withdrawn |
| 9–10 | Second-user run: a pack authored by one nurse, run by another | Two packs run successfully by someone other than the author |
| 11 | Community review path — consent, dissent recorded, changes versioned | One pack passes review with a documented disagreement |
| 12 | Distribution and sponsorship test | Someone pays, sponsors, or adopts — or does not |

### 3.5 Cycle 3 stop conditions

Stop if: no pack survives a second user; contribution requires appropriating community or employer knowledge; attribution or revocation cannot be honored; or the packs that get built are the founder's rather than users'.

---

## What runs across all three cycles

**Discovery** — interviews and observation across all three archetypes, every cycle ([PLAYBOOK §1](PLAYBOOK.md#1-discovery-runs-in-every-cycle)).

**The evaluation corpus** — every failure, correction, override, refusal, and reviewer rejection becomes a stored case. This is the asset that compounds, and it only compounds if it is captured while it happens rather than reconstructed later.

**External nurse and community review** — the Stage 5 panel is convened during Cycle 1, not after all three: three direct-care nurses, one educator or informaticist, one ethics or quality reviewer, one patient/family/community representative, one disability, language-access, or cultural-safety representative, with targeted privacy, legal, security, human-factors, and ontology consultation. Independent review, exact rule references, documented dissent, adjudication, versioned changes, and no "ratified" designation until the governance conditions are met. Reviewers are compensated.

**Executable governance** — after nurse review, approved rules are normalized into typed predicates, compiled to an executable form, given input and output schemas, made fail-closed, and covered by mutation tests that prove unsafe changes fail. Enforcement is verified at every intake, memory, delegation, tool, connector, and output boundary. The human-readable Constitution remains the governing source; generated code never becomes the authority.

**One canonical EDENA policy source** — Green, Yellow, Orange, Red-P, Red-E. Any simplified user-facing scheme is a deterministic projection of the canon, never a second tier system maintained in parallel:

```text
Canonical EDENA policy
        ↓
Audience-specific display
```

**The delivery circle** — recruited around the current cycle rather than the ten-year vision: nurse product/research partner, product engineer, UX and human-factors collaborator, privacy and security adviser, nursing informatics or ontology adviser, enterprise clinical sponsor, patient and community advisers.

---

## The one-page version

| | **Cycle 1 — Manager** | **Cycle 2 — Certification Learner** | **Cycle 3 — Builder–Organizer** |
|---|---|---|---|
| **Artifact** | Governed Project Packet | Governed learning plan | Governed action system + capability pack |
| **Proves** | Institutional value and payment | Retention and individual payment | Extensibility and network value |
| **Buyer** | Department or institution | The nurse | Self, sponsor, or organization |
| **Approver** | Authorized leader or local governance | The nurse | Community or organizational authority |
| **Governance** | Yellow · D1 · Recommend | Green–Yellow · D0–D1 · Recommend | Yellow · D0–D1 · Recommend |
| **Dominant constraint** | Reviewer acceptance | Rights clearance | Contribution and revocation |
| **New on the spine** | The spine itself | Plan schema, memory, reliance, sponsorship boundary | Pack format, review path, distribution |
| **Fails if** | No approver accepts; no second problem | No return in week four; reliance worsens | No pack survives a second user |
