---
title: "Evidence Gates and Metric Definitions"
status: "Proposed measurement plan"
version: "0.1"
date: "2026-08-23"
applicability: "Measurement record. It defines what would count as evidence and what would count as being wrong. It reports no results, establishes no baseline, and creates no product, program, pilot, institutional relationship, clinical validation, or authority to process PHI."
---

# Evidence Gates and Metric Definitions

Nurse AI OS has structural verification and almost no outcome evidence. This document states, before any cycle runs, what would count as a lane working — so that the answer cannot be assembled afterward from whatever happened to be encouraging.

## 1. The one signal that matters most

> **They bring a second real problem without being asked.**

Everything else on this page is instrumentation around that sentence. A person who returns with a second genuine task has made a judgment about value that no satisfaction score reaches. A person who praises a demonstration has made no judgment at all.

## 2. Signals that are not evidence

Named explicitly, because each is easy to collect and each has ended a startup that mistook it for demand.

| Not evidence | What it actually indicates |
|---|---|
| Sign-ups | Curiosity, or a good headline |
| Positive reactions after a demonstration | Politeness, and the founder's credibility |
| Time on task | Possibly confusion |
| "I would definitely use this" | A prediction people are reliably bad at making |
| A pilot discussed but unscheduled | A polite decline with a longer timeline |
| Founder-run sessions producing good artifacts | The founder's expertise, not the system's |
| Reviewer approval of an authoritative-looking packet | The most dangerous signal in the plan — see §5 |

## 3. The cycle gates

A gate passes only if **every** condition holds. Partial passage is failure with a re-plan, not a reason to proceed carefully.

### Gate 1 — Manager, at day 90

1. At least **six** packets produced from real problems that partners brought.
2. At least **four** packets submitted to an actual approver, and at least **three** accepted with **less rework than that approver's status quo**, stated by the approver.
3. At least **three** partners returned with a second real problem, unprompted.
4. At least **one** paid engagement or a signed pilot commitment with a date.
5. Partners **preserved** the governance steps — sections 4, 8, 9, 13, 15 survive to the reviewer rather than being stripped before submission.
6. At least **one** partner states, unprompted, a specific thing the packet contains that they would not have produced with a general-purpose assistant.
7. At least **fifteen** stored evaluation cases derived from real failures, not authored as examples.

### Gate 2 — Certification learner, at day 180

1. At least **ten** learners produced a plan and completed **four weeks** against it.
2. At least **half** returned in week four without a prompt.
3. Plans **changed** at reassessment, for reasons the learner stated.
4. Reliance measures do not move toward dependence (§4).
5. At least **three** learners paid their own money.
6. No plan depended on rights-encumbered material; the rights gate refused at least one real source without the learner abandoning the plan.

### Gate 3 — Builder–Organizer, at day 270

1. At least **five** initiatives documented end to end.
2. At least **two** capability packs run successfully by a user other than the author.
3. At least **one** pack passed community review **with a documented disagreement** and a versioned change.
4. Revocation was exercised at least once and honored completely.
5. At least **one** builder recruited another relevant user.
6. Someone paid, sponsored, or formally adopted.

## 4. Appropriate reliance and the deskilling check

Learning products that make people feel capable while making them less capable are a known failure, and the feeling arrives before the deficit shows. Both are measured, and they are never assumed to agree.

**The unassisted check.** Monthly, a short task the learner completes with no assistance. It is compared with their own prior unassisted work — never with other learners, never as a score, never visible to a sponsor or employer, and never used in any determination about a person.

**Reliance indicators tracked over time:** proportion of sessions in which the learner commits to an answer before asking; frequency of the learner correcting or rejecting a draft; whether questions get more specific or more open-ended over weeks; whether the learner can restate the reasoning without the system present.

**The confidence trap.** Confidence before and after is recorded and is never reported as an outcome on its own. Confidence rising while unassisted performance flattens is a harm signal, not a success metric.

## 5. Testing for authority-shaped acceptance

A reviewer may accept a packet because it is complete, or because it reads like something that has already been approved. The second is a failure the plan actively hunts for rather than waits to discover.

Method: at least twice per cycle, a packet is submitted with a **known material omission in section 4 or 15** — a genuinely missing piece of information, or a genuinely unresolved concern that would ordinarily be reported. If reviewers accept it without noticing, the artifact is producing false confidence and the format is wrong regardless of every other number on this page.

This test is disclosed to design partners in advance as part of the study design. It is never run on an artifact that will drive a real institutional decision.

## 6. Per-artifact measures

Recorded for every Manager packet and every learner plan:

- Time to complete the artifact
- Section completeness, and which sections stayed empty
- Number of material omissions caught by the human
- User corrections, by section
- Override frequency, and what was overridden
- Unsupported claims caught before export
- Cognitive burden, self-reported, with the task named
- Confidence before and after — never equated with competence
- Reviewer acceptance, and rework required
- Intention to reuse, and actual reuse
- Willingness to pay, and actual payment

Patient outcomes are not measured. No lane in this plan is positioned to affect them, and measuring them would imply otherwise.

## 7. How measurement stays inside the boundary

Instrumentation follows the same rules as the product. No PHI enters telemetry. No measure is attributable to a named person for any employment, competency, disciplinary, promotion, or termination purpose, and none is shared with an employer at individual grain. Sponsored learners' reflections and unassisted checks are closed to sponsors by default and by data model. Participation is compensated where it costs someone their time, and consent to use a session as an evaluation case is separate, specific, and revocable.

## 8. Falsifiers stated in advance

The plan is wrong, and should be visibly said to be wrong, if:

- Managers value the drafting and discard the governance sections. The differentiation is imaginary.
- Approvers accept packets with planted omissions. The artifact manufactures confidence.
- Learners return for streaks and reminders rather than for the plan. The value is habit design, available elsewhere.
- Every paying customer is a personal contact of the founder at Gate 1 **and** Gate 2. There is no acquisition path, only credibility.
- The spine does not carry: Cycle 2 costs as much to build as Cycle 1. The reuse thesis in [STRATEGY §3](STRATEGY.md#3-the-spine-build-once-instantiate-three-times) is false and the sequencing argument weakens with it.
- Capability packs are only ever authored by the founder. There is no platform, only a template library.

Each falsifier has a cycle in which it would show. None of them is fatal to the project; all of them are fatal to a specific claim, and the claim is what would need to change.
