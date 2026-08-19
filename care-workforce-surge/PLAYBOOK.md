---
title: "Care Workforce Surge Operational Playbook"
status: "Proposed operating playbook"
version: "0.1"
date: "2026-08-19"
applicability: "Manual-first operating method; capabilities remain inactive until built and verified. Nothing here is clinical guidance, and no procedure here authorizes institutional or patient-facing use."
---

# Care Workforce Surge Operational Playbook

## 1. What this playbook is

The runnable half of the [Doctrine](DOCTRINE.md) and the [Implementation Plan](IMPLEMENTATION.md). It contains the procedures, the interaction contracts, the review rituals, and the metric definitions needed to operate a supervision-multiplying system for low-tenure care workers.

**One standing instruction governs every procedure below.** The clinical *content* of any scope or escalation artifact is authored and reviewed by a qualified human clinical authority for the specific role, setting, and jurisdiction it serves — an employer's clinical leadership, a program's faculty, or a named specialty reviewer. This playbook supplies **structure, sequence, and governance**. It does not supply clinical content, and any structure below that appears filled in is an illustrative shape, not guidance to follow.

## 2. Roles and decision rights

| Role | May | May not |
|---|---|---|
| **Care worker (entrant)** | Use the personal edition; own their learning record; decline any sharing | Be required to expose their questions to an employer as a condition of using the personal edition |
| **Preceptor / supervising nurse** | See a consented dyad record; teach; decide what is ready | Be replaced in the escalation path; be given a system-generated readiness score |
| **Clinical authority (employer or program)** | Author and approve Scope Cards and Escalation Cards for their setting | Delegate that authorship to the system or to this project |
| **Localization reviewer** | Approve boundary, refusal, and escalation text in a named language for a named population | Approve clinical substance outside their competence |
| **Unit/program leader** | See aggregate load and gaps; change supervision arrangements | Use any view in an employment determination |
| **The system (Hermes / Nurse AI OS)** | Orient, hold scope, shape questions, rehearse, refuse, route, record | Answer out-of-scope clinical questions, triage, score competence, decide anything |
| **Founder / accountable steward** | Publish, refuse, halt, and record decisions within actual authority | Claim clinical, institutional, credentialing, or regulatory authority not held |

**Separation rule.** The party that authors a Scope Card does not also certify that the system enforces it. Authorship and verification are different people.

## 3. The Ask Ladder

The single habit the wedge exists to install. Taught on day one, reinforced in every rehearsal, and printed on the Escalation Card.

| Rung | Name | Use it when | The system's behavior |
|---|---|---|---|
| **1** | **Look** | The answer is on the care plan, the assignment sheet, the label, the posted policy | Points to *where* to look; does not read the answer out as fact |
| **2** | **Ask the system** | It is about your role, your scope, your process, your words, your rehearsal | Answers only within role/process; states plainly when a question is above rung 2 |
| **3** | **Ask a person** | Anything about this person's condition, care, medication, or any judgment call | Helps form the question; routes to the named role; never answers instead |
| **4** | **Escalate now** | Any signal on the Escalation Card, or any time you are unsure whether it is a rung-4 | Stops assisting; surfaces the escalation path immediately; no shaping, no queue |

**The rule that overrides all four:** *When in doubt, go up a rung.* Ambiguity resolves upward, always. A system that resolves ambiguity downward — toward answering — is out of doctrine.

**Rung 4 is unconditional.** It is never gated behind a form, a shaping step, a login, a connectivity check, or a "let me help you word that." The latency budget for rung 4 is measured in seconds and tested adversarially, including against vague, non-native, and distressed phrasing.

## 4. Day One procedure (entrant)

Runs in under twenty minutes, in the browser, with no account and no PHI.

1. **Declare scope.** Role, setting, jurisdiction, start date. This becomes the scope object the system enforces. It is the user's statement, not a credential check, and the system says so.
2. **Read the Scope Card** for that role and setting — in, out, always-escalate — with its authorship and review date visible.
3. **Read the Escalation Card** and identify, by name and role, the human this worker escalates to on their next shift. If that person is unknown, the first task is to find out; the system says this plainly rather than proceeding.
4. **Two rehearsals, commit-first.** Two synthetic scenarios. The user states what they see, what they think, what they will do. Only then does the system respond.
5. **Take the wallet card.** Escalation Card saved to the phone, offline-available, in the user's language.
6. **Set the unassisted check.** A date is set for the first assistance-off practice run.

**Success for Day One is not satisfaction.** It is: the user can state one thing that is out of their scope, and can name who they escalate to.

## 5. Commit-then-compare microdrill

The core learning loop, borrowed from [`nurse-formation/DOCTRINE.md`](../nurse-formation/DOCTRINE.md) and enforced in the interaction contract.

```text
Scenario (synthetic)
      ↓
User states: what I see · what I think · what I will do   ← nothing is shown until this is entered
      ↓
System compares: where the read aligns · where it differs · which rung this was
      ↓
User revises, or escalates
      ↓
Recorded to the user's own record — not scored, not ranked
```

Three rules make it real:

- **No preview.** No hint, no partial answer, no suggested option before the commit. A leaked hint destroys the measurement and the learning.
- **The rung is part of the answer.** Every drill asks not only "what would you do" but "whose call is this." Scope reasoning is the skill being trained.
- **Difference is discussed, not graded.** The system describes the difference between the user's read and the reference read. It does not assign a number, and it never reports the number it did not assign.

## 6. Weekly preceptor ritual (Phase 2)

Fifteen minutes, both people, same record.

1. **Recurrence.** What did this learner hit repeatedly? Framed as topics to teach.
2. **Escalations.** Which went up appropriately; which went up late; which should have and did not. Reviewed as system-and-situation, not as personal fault.
3. **One teach.** The preceptor names one thing to teach this week. It goes on the record as a teaching commitment, not a learner deficit.
4. **Interruption check.** Preceptor states whether shaping helped or got in the way. If it got in the way, shaping loosens — the ratio is not worth a delayed catch.

**Prohibited in this ritual:** ratings, readiness scores, comparisons between learners, and anything exportable into an employment file.

## 7. Monthly unassisted check

Required by doctrine P7, because assistance is known to erode unaided skill.

1. Assistance is disabled for a fixed scenario set.
2. The user works the set alone.
3. Results compare the user to **their own prior unassisted runs**, never to other people.
4. **If unassisted performance declines, the response is less assistance, not more.** More rehearsal, fewer answers, more rung-3 routing. This is counterintuitive and it is the point.
5. Cohort-level trends are reviewed by the project; a sustained cohort decline halts feature expansion (Implementation Phase 1 stop condition).

## 8. Escalation Card structure

The card is short enough to hold in one hand and is authored locally. The **structure** is fixed by this playbook; the **content** is not supplied here.

| Section | What it holds | Who authors it |
|---|---|---|
| **Tell someone now** | The locally defined signals that never wait | Employer or program clinical authority |
| **Who** | Name and role of the person on this shift, plus the backup | Employer; verified by the worker on day one |
| **How to say it** | A fixed four-part sentence: what I saw, when, what I did, what I need | Structure fixed here; examples authored locally |
| **What never waits** | The short list that overrides any other instruction, including one from this system | Clinical authority |
| **If you cannot reach anyone** | The local chain, including emergency services | Employer; reviewed |
| **Language** | The worker's own language, reviewed by a named human | Localization reviewer |

**Card rule:** if any section is empty for a given setting, the pack does not ship for that setting. An escalation card with a blank "who" is worse than no card, because it teaches that raising a hand is optional.

## 9. Incident procedure

Applies to any event where the system may have contributed to harm, near-miss, delayed escalation, scope violation, privacy exposure, or a false claim.

1. **Stop the surface.** The affected capability is disabled first. Diagnosis happens after, not before.
2. **Preserve.** Prompts, outputs, versions, pack versions, refusal-test results, timestamps. No editing.
3. **Notify.** The affected user, the accountable steward, and — where a deployment exists — the named institutional owner, within the deployment's stated window.
4. **Classify** by EDENA risk, data class, and action mode, and by which doctrine principle was implicated.
5. **Fix and test.** The fix ships with a new adversarial test that would have caught it, added permanently to the refusal bundle.
6. **Publish.** A public record of what happened and what changed. Failed experiments become harvested learning, not deleted branches.
7. **Re-enable only** after the new test passes and a named human signs off.

**Never:** silent patch, retroactive edit of a published claim, or an incident record that names a worker as the cause.

## 10. Localization procedure

Doctrine P11 makes this a safety procedure, not a marketing one.

1. Boundary, refusal, and escalation strings are translated by a qualified human, never machine-translated and shipped.
2. A **second** named reviewer, native in the language and familiar with the care setting, confirms that the *boundary still reads as a boundary* — hedged translations are the failure mode, not mistranslated nouns.
3. Refusal tests run in every shipped language, including authority-framing and urgency-framing variants.
4. Review dates are recorded and expire. An expired locale is withdrawn, not carried.
5. No locale ships without both reviewers.

## 11. Metric definitions

Operational definitions, so that results cannot be reshaped after the fact.

| Metric | Definition | Collection | Known bias |
|---|---|---|---|
| **Appropriate escalation rate** | Escalations matching a locally defined always-escalate signal ÷ occasions where such a signal was present in a rehearsal scenario | Rehearsal only; never inferred from real care | Rehearsal ≠ shift conditions; overstates performance |
| **Out-of-scope attempt rate** | Requests classified out-of-scope ÷ total requests | System-side, aggregate | Learning to phrase around the boundary looks like improvement |
| **Escalation latency (rung 4)** | Time from trigger detection to escalation path displayed | Instrumented, adversarially tested | Measures the system, not the human's next action |
| **Unassisted-practice score** | Performance on the fixed assistance-off set, versus the same user's prior runs | Monthly | Practice effects; set must rotate |
| **Low-value interruption rate** | Preceptor-marked "did not need me" ÷ total questions received | Preceptor marks, weekly | Preceptor mood, workload, and relationship all contaminate it |
| **Supervision load** | Consented entrants per available supervising nurse, by shift | Aggregate only | Availability is not the same as attention |

**Two metrics are deliberately absent:** anything resembling a competence score, and engagement. Neither may be introduced without a doctrine amendment.

## 12. Cadence

| Ritual | Frequency | Output |
|---|---|---|
| Refusal bundle run | Every change to a prompt, pack, or model | Pass/fail record, versioned |
| Preceptor ritual | Weekly, per dyad | One teach; interruption check |
| Unassisted check | Monthly, per user | Own-baseline comparison |
| Scope Card review | Quarterly, or on any regulatory change | Re-dated card or withdrawal |
| Localization expiry review | Quarterly | Locale continues or is withdrawn |
| Doctrine and validation review | On any falsifier movement; at minimum annually | Amendment or restatement |

## 13. Standing refusals in operation

The [refusal catalog](DOCTRINE.md#6-refusal-catalog) is operational, not aspirational. Three notes on running it:

- **Refusals are tested, not asserted.** A class without a passing adversarial test is not a refusal; it is a hope.
- **Loosening requires a decision record.** Any change that narrows a refusal class is a doctrine amendment with a named author, a date, the evidence relied on, and the risk accepted. It is never a product decision.
- **The pressure is predictable.** "Users keep asking," "the competitor answers it," "it is only the simple ones," "a nurse reviewed the content once." None of these is evidence, and all of them will arrive.

## 14. What this playbook does not authorize

No curriculum, competency framework, credential, continuing-education credit, proctoring, employment process, institutional deployment, clinical decision support, or PHI processing is created or permitted by this document. Every procedure above operates inside the personal edition ceiling — Yellow risk, D1 data, Recommend action — until separate named authorization exists.
