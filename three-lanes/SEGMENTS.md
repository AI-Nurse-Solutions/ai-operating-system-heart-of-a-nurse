---
title: "The Three Lanes: segment definitions and role separation"
status: "Proposed segmentation"
version: "0.1"
date: "2026-08-23"
applicability: "Definitional record. It fixes who each lane serves and who decides for them. It creates no product, program, cohort, partnership, pricing, institutional relationship, or authority to process PHI."
---

# The Three Lanes: segment definitions and role separation

Three archetypes carry the long-term product map: the Learner, the Manager, and the Nurse Builder–Organizer. This document does the unglamorous work of saying exactly who they are, who pays for them, who is allowed to approve their work, and which apparent segments are not lanes at all.

The reason to be this pedantic is a specific failure mode:

> **The person who loves the product is frequently not the person who pays for it, and almost never the person who may authorize it.**

A segment definition that collapses those roles produces a product that delights a user who cannot buy it, or an artifact that a reviewer refuses because nobody asked what the reviewer needed.

---

## 1. The Learner is two markets, not one

The single most consequential correction to the three-group model: a prelicensure student and a licensed nurse pursuing certification share a verb and nothing else that matters commercially or ethically.

| | **Certification / upskilling nurse** | **Prelicensure student** |
|---|---|---|
| Primary job | Sustain a personal professional-learning plan against a dated goal | Learn clinical judgment, organize study, prepare for and reflect on simulation |
| Agency over the decision | Own it entirely | Constrained by faculty, program, and accreditation |
| Buyer | The nurse; sometimes an employer or association | Student, school, or program — rarely the user alone |
| Approver | The nurse | Faculty and program |
| Dominant risk | Copyrighted test-prep material; unsupported competence claims | Academic integrity, novice overreliance, protected educational content, clinical-rotation data |
| Cycle | Recurring, self-paced, months long | Term-bound, externally scheduled |
| Can be served without an institutional partner | Yes | **No** |

The certification learner is the buildable learner. The prelicensure student is a research subject and a partnership question, and is treated in [STRATEGY §5](STRATEGY.md#5-the-prelicensure-lane-is-research-only) as a separately governed subgroup rather than a lane.

**Bounded outcome for the certification learner**

> Convert a nurse's certification goal, baseline, available time, and **own** source materials into a governed learning plan with weekly actions, progress evidence, reflection, and scheduled reassessment.

The outcome is explicitly *not* "pass the exam." No system in this repository may claim, imply, or be measured against exam performance. What is claimed is a usable plan, study continuity, source-aware explanation, visible uncertainty, and a record of what the learner changed and why.

---

## 2. The Manager

The Manager is a nurse manager, nurse leader, educator with program responsibility, quality-improvement nurse, or clinical informatics nurse who is accountable for work that other people will review.

What makes this segment the strongest first wedge is not enthusiasm. It is that the Manager's daily work already has the shape the system is good at: a problem affecting identified groups of people, evidence and policy that must be cited, an authority boundary that must be respected, a named human who owns the decision, and a reviewer waiting downstream.

Generic AI drafts the memo. It does not natively preserve authority, unresolved risk, staff burden, monitoring, stop conditions, escalation, and handoff — and it does not know that dropping any of them is the failure.

**Bounded outcome**

> Turn one no-PHI unit, workforce, education, quality, or AI-adoption problem into a review-ready governed project packet.

**Governing constraint.** Institution-specific work is Yellow even without PHI, because it names real units, real staffing conditions, and real local policy. It requires authenticated local sources, a named human reviewer, approval of the exact artifact rather than the workflow in general, no silent execution, an audit trail, and an explicit employer boundary. The Manager lane never runs at Green just because no patient is named.

---

## 3. The Nurse Builder–Organizer

Renamed from "entrepreneur–community developer–organizer," which bundled at least three jobs that share agency and share almost no payment behavior.

| Subgroup | What they are building | Who might pay |
|---|---|---|
| **Nurse entrepreneur** | A business, product, or professional service | Self, then customers |
| **Community developer** | A professional or geographic community | Sponsor, association, employer, grant |
| **Organizer** | Coordinated action around advocacy, education, or policy | Organization, membership, grant, nobody |

Research separates these three before any build begins. They are one lane only in the sense that they all test the same platform question.

**Bounded outcome**

> Turn one nurse-led initiative into a governed action system: defined audience, value proposition, stakeholder map, work plan, evidence ledger, communication assets, decision log, measures, and review cadence.

**The real test.** This lane is not primarily a revenue bet. It is the test of whether a user can *produce* a reusable capability rather than only consume one — and whether that capability can be reviewed, versioned, attributed, licensed, and revoked without appropriating community knowledge. If contribution cannot be made consented, rights-aware, attributed, versioned, evaluated, revocable, and separated from PHI and employer-confidential material, there is no platform here and the lane should not ship.

---

## 4. Role separation

Every lane documents five roles. A lane whose five roles are not all named is not ready to build.

| Role | Question it answers |
|---|---|
| **User** | Who repeatedly performs the workflow? |
| **Buyer** | Who pays? |
| **Beneficiary** | Whose outcome should improve? |
| **Approver** | Who must permit consequential use? |
| **Steward** | Who reviews safety, rights, quality, and change? |

| Segment | User | Buyer | Beneficiary | Approver | Steward |
|---|---|---|---|---|---|
| **Manager** | Nurse manager, QI, informatics, educator-with-program | Department or institution | Staff and the people they care for | Authorized leader or local governance | QI, staff nurses, policy and safety reviewers |
| **Certification learner** | Nurse | Nurse, or employer if sponsored | The nurse | The nurse; employer if work-sponsored | Educator or content steward |
| **Builder–Organizer** | Nurse builder | Self, sponsor, or organization | The community or customers served | Community or organizational authority | Affected community, rights and governance reviewers |
| **Prelicensure learner** | Student | Student or school | The student | Faculty and program | Faculty, student, accessibility and integrity reviewers |

Two consequences follow immediately and both are build decisions, not marketing decisions:

1. **The Manager lane must produce an artifact the Approver accepts**, which means an approver is interviewed in discovery and reads real output before the workflow is considered done. Reviewer acceptance is the gate, not user satisfaction.
2. **The employer-sponsored learner has two masters.** When an employer pays, the learner's reflection and self-assessed weaknesses are not the employer's to read. That boundary is designed in at the data model, not added later as a setting.

---

## 5. Cross-cutting roles that are not lanes

Three groups matter enormously and would each be a mistake to build as a fourth equal product.

**Educator or program leader — user *and* channel.** Governs prelicensure use, brings cohorts, defines academic-integrity boundaries, reviews learning output, and can become an institutional buyer. Bounded outcome when engaged: convert one learning objective into a governed teaching and evaluation package with synthetic exercises, Socratic prompts, reflection, accessibility controls, and faculty review. The educator is how the Learner lane reaches institutions; treat them as the bridge, not as a separate roadmap.

**QI, safety, or clinical informatics nurse — advanced design partner.** The most strategically important bridge group. They already speak workflow analysis, implementation, evidence, data limitation, quality measurement, human factors, vendor evaluation, and governance committees, and they are the users most likely to engage the Nursing Intelligence Kernel, EDENA, and evaluation contracts on their merits. They belong **inside the Manager cohort as an advanced subtype**, not in a separate lane.

**Direct-care and charge nurses — workflow truth and governance participants.** They are the only people who can say what creates burden, where policy diverges from practice, what a tired nurse at 03:00 will misread, whether an escalation path is usable, and what disappears at handoff. They must be present in the design of anything institutional. They are also frequently the least able to pay and the least available for abstract governance tooling, so they are not the first payer segment and should never be recruited as though they were. Their participation is compensated.

Two further groups are **channels and institutional partners**, not end-user lanes: nursing associations, schools, and certification programs; and community organizations. They may become distribution partners, buyers, content licensors, review bodies, cohort sponsors, or hosts. None of that is a product lane.

**Executive buyers — CNO, CNIO, quality executive, AI-governance sponsor — are approvers and buyers, not daily users.** Their questions are different in kind: does this reduce implementation risk, what evidence does it produce, what is the data boundary, who remains accountable, how does it fit existing governance, what does it cost, what is required of IT, legal, education, and operations. Building the Manager's daily tool and expecting it to answer the executive's questions is a category error; the packet is what crosses that gap.

---

## 6. What this document does not do

It does not establish that any of these people want the product. It defines who would be asked and who would decide. [EVIDENCE.md](EVIDENCE.md) states what would count as an answer, and what would count as being wrong.
