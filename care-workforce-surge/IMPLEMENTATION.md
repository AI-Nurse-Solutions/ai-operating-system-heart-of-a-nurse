---
title: "Care Workforce Surge Implementation Plan"
status: "Proposed staged plan"
version: "0.1"
date: "2026-08-19"
applicability: "Plan of record. Capabilities described here are inactive until built and verified; no phase authorizes the next by being written down."
---

# Care Workforce Surge Implementation Plan

## 1. How to read this

Five phases. Each has artifacts, non-goals, an **evidence gate**, and **stop conditions**. A phase is complete when its gate passes on evidence, not when its artifacts exist. A phase that fails its gate is published as a failure and either redesigned or abandoned — it is not carried forward on optimism.

Everything here is solo-founder-scale and manual-first, in the pattern of the [Knowledge Commons Playbook](../knowledge-commons/PLAYBOOK.md): deterministic files and human review before accounts, APIs, services, or integrations.

**EDENA posture for the whole plan through Phase 3:** risk ceiling **Yellow**, data class ceiling **D1**, action ceiling **Recommend**. Orange, Red-E, D2–D4, and any Act mode are outside this plan and require separate authorization.

## 2. Honest starting position

| Already exists in this repository | Genuinely new work |
|---|---|
| SOUL Quiz and role personalization; Life & Projects mapping | Role **scope objects** — declared role, setting, jurisdiction, tenure — enforced at the boundary |
| Starter Kit, workbook, Local HTML dashboard (browser-only, no PHI) | Entrant Orientation Pack aimed at the unlicensed direct-care entrant, who is not currently a served population |
| EDENA risk/data/action dimensions and the public governance kit | Refusal catalog as an executable test bundle |
| Knowledge Pack contract and fail-closed intake (personal knowledge-base pilot) | Escalation as an instrumented surface with a latency budget |
| Nurse Formation doctrine: commit-then-compare, human evaluative authority | Unassisted-practice measurement as a shipped requirement |
| Mission Control Lite (browser-local dashboards) | The preceptor dyad as a first-class two-person object |

Nothing in the left column becomes a surge capability by being adjacent to one.

---

## Phase 0 — Instrument before building

**Purpose.** Decide how this will be judged before there is anything to defend.

**Artifacts.**

1. `METRICS.md` — operational definitions for: *appropriate escalation rate*, *out-of-scope attempt rate*, *escalation latency*, *unassisted-practice score*, *low-value interruption rate*, *preceptor load*. Each with numerator, denominator, collection method, and known bias.
2. **Refusal test bundle** — one adversarial test set per class in [DOCTRINE §6](DOCTRINE.md#6-refusal-catalog), including paraphrase, role-play pressure, urgency framing, authority framing ("my supervisor said to ask you"), multilingual variants, and content-embedded instruction. Machine-runnable, versioned, published.
3. **Baseline protocol** — how a matched comparison is constructed without an employer, without PHI, and without deceiving participants.
4. **Consent and data language** — plain-language statement of what is recorded, what is local-only, and what a supervisor can never see. Reviewed before any user sees the product.
5. **Synthetic scenario corpus v0** — 30 scenarios spanning home care, residential, and acute-adjacent settings. Synthetic only; no reconstructed real cases.

**Non-goals.** No user-facing product. No recruitment. No pilot conversations.

**Evidence gate.**
- Every refusal class has at least one test that *fails* against a deliberately weakened prompt — proving the tests detect, rather than passing vacuously.
- Two people who are not the author can compute each metric from the definition alone and agree.
- The consent language survives a hostile read: can a supervisor infer a named worker's struggles from anything the design exposes? If yes, the design changes.

**Stop conditions.** If metrics cannot be defined without access to PHI or employer data, the personal-edition premise is wrong and Phase 1 does not start.

---

## Phase 1 — Entrant Orientation Pack (the wedge)

**Purpose.** Teach one thing well: *what is mine to do, and how do I raise a hand.*

**Artifacts.**

1. **Scope Card** — per role (home care aide, personal care aide, nurse aide), per setting, per jurisdiction where declared: what is in role, what is out, what is always escalated. Ships with an explicit "this varies by state and employer; your employer's policy governs" statement and the date it was reviewed.
2. **The Ask Ladder** — the four-rung habit taught in the [Playbook](PLAYBOOK.md#3-the-ask-ladder): *Look → Ask the system → Ask a person → Escalate now.* Each rung with its own examples and, critically, the signals that mean **skip to rung four immediately**.
3. **Escalation Card** — the wallet-sized artifact: who to tell, how to say it, what to say first, what never waits. Localized.
4. **Commit-then-compare rehearsal** — synthetic scenarios where the user states their read and intended action *before* the system responds. No answer is shown until the user commits.
5. **Unassisted check** — a periodic scenario set run with assistance disabled, scored against the user's own history, visible only to the user.
6. **Localization set** — Scope Card, Escalation Card, and every refusal string in the site's existing locale set, each with a named human reviewer and review date.

**Delivery.** Browser-only, no install, no account required, no PHI, works offline once loaded, on a phone. The entrant population cannot be assumed to have a laptop, a stable connection, or employer-provided hardware.

**Non-goals.** No clinical questions answered. No documentation help. No employer integration. No competency scoring. No certificate that implies credential.

**Evidence gate.**
- ≥ 95 percent pass on the Phase 0 refusal bundle, including the multilingual and authority-framing variants; any clinical-answering leak is a hard fail regardless of aggregate score.
- In supervised sessions with real entrants, out-of-scope attempt rate declines and appropriate-escalation rate rises versus their own pre-use baseline — or the result is published as negative.
- Unassisted-practice scores do not decline across the measurement window.
- Comprehension of the Scope Card is demonstrated in each shipped language by a native-speaking reviewer who did not write it.

**Stop conditions.** Any confirmed case where the pack delayed or displaced an escalation. Any locale where the boundary text cannot be reviewed by a qualified human — that locale does not ship.

---

## Phase 2 — The Preceptor Loop (the dyad)

**Purpose.** Move the supervision ratio, and prove it moved.

**Artifacts.**

1. **Dyad pairing** — two consenting humans, both of whom see the same record. No silent observation; the entrant always sees exactly what the preceptor sees.
2. **Question shaping** — before a question reaches the preceptor, the entrant states what they saw, what they think, and what they plan. The preceptor receives a formed question, not a raw one.
3. **Urgent passthrough** — anything matching an escalation signal bypasses shaping entirely, with a latency budget measured in seconds. Shaping must never become a queue in front of a nurse.
4. **Recurrence digest** — what this learner keeps hitting, phrased as topics to teach, never as a judgment of the person.
5. **Preceptor-side non-goals, enforced in the product** — no rating control, no readiness score, no exportable evaluation.

**Non-goals.** No supervisor without consent. No institutional rollout. No integration with assignment or scheduling.

**Evidence gate.**
- Measured reduction in low-value interruptions **with no increase in missed or delayed escalations.** Both halves are required; the first alone is a failure dressed as a success.
- Urgent passthrough meets its latency budget in adversarial testing, including when the entrant's phrasing is vague, non-native, or panicked.
- Preceptors report the digest as teachable rather than evaluative, in structured feedback from people who were told they may say no.

**Stop conditions.** Any evidence that shaping delayed an urgent escalation. Any request to convert the digest into an evaluation, accepted.

---

## Phase 3 — Unit visibility, non-evaluative

**Purpose.** Give a named accountable human an honest picture of supervision load.

**Artifacts.**

1. **Load view** — where escalations cluster by time, setting, and topic; where entrants are working without an available supervisor. Aggregated; never a per-person score.
2. **Gap report** — shifts and settings where the supervision ratio is outside what the unit itself declared acceptable.
3. **Doctrine notice** — every view carries the statement that it is not a performance record and may not be used in an employment determination.

**Non-goals.** No individual scoring, ranking, discipline, promotion input, scheduling automation, or productivity measurement. No PHI.

**Evidence gate.**
- A hostile review — conducted by someone asked to try — cannot re-identify a named worker's performance from any shipped view.
- At least one leader states, in writing, a supervision decision they changed because of the view. If nobody changes anything, the view is decoration and does not ship.

**Stop conditions.** First request to add per-person performance data. Refuse, record, and if refusal is not accepted, do not proceed with that partner.

---

## Phase 4 — Institutional pilot, separately authorized

**Purpose.** Test the whole loop in a real setting under real governance.

**Preconditions, all required.** Named accountable owner on both sides; written scope; data agreement; local review; incident procedure with a stop switch; EDENA classification recorded for every artifact in scope; published evidence protocol including how negative results will be reported.

**Artifacts.** Pilot charter; local Scope Card review by the employer's own clinical authority; escalation-path mapping to the employer's actual chain; termination and rollback plan.

**Non-goals unchanged.** No PHI in the personal edition. No employment determinations. No clinical decision support. No claim that the pilot reduces required staffing or supervision.

**Evidence gate.** Pre-registered outcomes, reported whether they favor the system or not, with the negative-result publication commitment made *before* the pilot begins.

**Stop conditions.** Any deployment accompanied by reductions in orientation, preceptor time, or staffing (doctrine P12) — support is withdrawn, in writing.

---

## 3. Build order and dependencies

```text
Phase 0  metrics + refusal tests + consent  ─┐
                                             ├─→ Phase 1  Entrant Orientation Pack
Existing: SOUL scope, EDENA ceiling,        ─┘        (browser-only, no PHI, localized)
Knowledge Pack contract, formation doctrine                     │
                                                                ▼
                                              Phase 2  Preceptor dyad (consent both sides)
                                                                │
                                                                ▼
                                              Phase 3  Unit load view (non-evaluative)
                                                                │
                                                                ▼
                                              Phase 4  Institutional pilot (separate authority)
```

No arrow may be skipped. No phase authorizes itself.

## 4. Sequencing discipline for a solo founder

- **One phase at a time.** Parallel phases mean neither gate gets honest scrutiny.
- **Manual before automated.** Human review of every Scope Card and every localization before any pipeline exists.
- **Deterministic files before services.** Packs, cards, and tests are files in version control with provenance and review dates, per the Knowledge Commons contract.
- **Publish the failures.** A negative gate result is a repository artifact, not a deleted branch.
- **Refuse the shortcut that always appears.** The request to "just let it answer the simple clinical ones" will arrive in every phase. The refusal catalog is version-controlled precisely so that loosening it requires a doctrine amendment with a written decision record, not a product decision made under deadline.

## 5. What this plan does not do

Publication of this plan does not create a curriculum, a training program, a competency framework, a credential, continuing-education credit, a pilot, a partnership, an institutional relationship, a hosted service, a clinical capability, or authorization to process PHI. Every phase above is inactive until built and verified, and Phase 4 additionally requires authority this project does not currently hold.
