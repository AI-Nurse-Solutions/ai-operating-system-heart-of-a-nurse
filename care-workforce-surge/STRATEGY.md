---
title: "Care Workforce Surge Strategy"
status: "Proposed strategy"
version: "0.1"
date: "2026-08-19"
applicability: "Strategic record. It commits this project to a direction and to stated stop conditions; it creates no product, partnership, program, or institutional relationship."
---

# Care Workforce Surge Strategy

## 1. The position

> **Nurse AI OS is a supervision multiplier for a permanently low-tenure care workforce.**

Not a nurse. Not a clinical assistant. Not a staffing product. The unit of value is *safe supervisory throughput per experienced nurse* — how many entrants one nurse can orient, delegate to, verify, and rescue without either dropping a catch or burning out.

This position is chosen over the two obvious alternatives because of what the evidence says.

| Candidate position | Why not |
|---|---|
| "AI that helps new care workers answer clinical questions" | Directly contradicted. Models that score 94.9 percent alone deliver under 34.5 percent through untrained users, no better than no assistance at all ([VALIDATION §4.2](VALIDATION.md)). The failure is in the pairing, and shipping the pairing anyway is how someone gets hurt. |
| "AI that lets facilities run with fewer nurses" | Sells the labor savings that this project's doctrine forbids (P12), competes on the one axis where wages, not software, decide the outcome, and puts the product on the wrong side of the people it claims to serve. |

The chosen position also has the property of being *true when the market turns*: if the surge fails to materialize, supervision of low-tenure staff is still the binding constraint in every setting that has turnover.

## 2. What the strategy is aimed at

Three numbers define the opportunity and are restated here without embellishment:

- **~9.7 million** projected direct-care job openings, 2024–2034, counting exits and transfers.
- **39.9 percent** of RNs report intent to leave or retire within five years; median age 50.
- **~75 percent** annual turnover in home care; near **100 percent** historically for nursing-home aides.

The first number is the demand. The second is the constraint. The third is why the constraint never resolves on its own. A product aimed at the first number alone will drown in the third.

## 3. Sequencing: person → dyad → unit → institution

The order is deliberate, and each stage earns the right to the next.

**Stage 1 — The person (no institutional authority required).** A single care worker, on their own device, in their own language, with no PHI and no employer involvement. This is where Nurse AI OS already operates and where nothing has to be authorized by anyone. Deliverable: orientation, scope literacy, the escalation habit, and rehearsal on synthetic scenarios.

*Why first:* it is the only stage that can begin today under existing doctrine, and it is the only stage where the user is unambiguously the beneficiary.

**Stage 2 — The dyad (preceptor + entrant).** Two consenting people who already work together. The entrant's questions arrive at the preceptor better-formed, batched where safe, and immediate where not. The preceptor gets a picture of what this learner keeps hitting.

*Why second:* this is where the supervision ratio actually moves, and it is the smallest unit where that can be measured. It requires consent from both humans, not an institutional contract.

**Stage 3 — The unit (named accountable human).** Visibility into supervision load: where escalations cluster, which shifts leave entrants unsupervised, which topics recur. Never a per-person score.

*Why third:* it needs governance that Stage 2 has to prove first, and it is the first stage where an employment-decision risk exists (doctrine P9).

**Stage 4 — The institution.** Formal pilot under separate named authorization, with data agreements, local review, and an evidence protocol.

*Why last:* institutional deployment is where a wrong design gets locked in. Everything above must have survived contact with real users before anything is sold to an employer.

**Gate rule:** no stage begins until the previous stage has produced its stated evidence. Adoption is not evidence, satisfaction is not safety, and enthusiasm from a buyer is not permission to skip a stage.

## 4. The wedge

Of the four stages, the first thing to build is narrow enough to state in one sentence:

> **A browser-only, no-install, no-PHI Entrant Orientation Pack that teaches one thing well: what is mine to do, and how do I raise a hand.**

Why this wedge:

- It is the highest-frequency, lowest-risk, most universally needed content in the entire surge, and it is currently delivered by whoever happens to be on shift.
- It sits entirely inside the personal edition's EDENA ceiling (Yellow / D1 / Recommend).
- It has an honest success measure that is not a vanity metric: *did the worker escalate the things that should be escalated, and did they stop trying to answer the things that are not theirs?*
- It requires no employer, no integration, no clinical validation, and no institutional authority — which means it can ship, be measured, and be wrong cheaply.

Deliberately **not** the wedge: documentation help (owned by ambient-AI vendors with EHR access), clinical Q&A (contradicted by evidence), competency tracking (an employment determination), scheduling (an employment determination).

## 5. Landscape, honestly

| Category | Examples of the category | What they solve | The gap this strategy occupies |
|---|---|---|---|
| Ambient clinical documentation for nursing | Vendors now extending ambient scribing into nursing workflow; early leader-reported satisfaction, outcomes still maturing ([KLAS first-look coverage](https://www.beckershospitalreview.com/healthcare-information-technology/ai/hows-ambient-ai-for-nurses-an-early-review/)) | Documentation burden for licensed staff inside the EHR | Requires institutional deployment and EHR access; does nothing for the unlicensed entrant and nothing for the preceptor relationship |
| Virtual nursing | Inpatient virtual nursing programs; qualitative evaluations report reduced administrative burden and overtime | Redistributes licensed nursing work | Real supervision, but supply-limited by the same scarce nurses; complementary, not competing |
| Competency / compliance LMS | Enterprise healthcare learning platforms | Mandatory education, tracking, compliance | Institution-owned, compliance-shaped, and evaluative — the opposite of a worker-owned formation tool |
| Staffing marketplaces | Per-diem and gig staffing platforms | Filling shifts | Optimize placement, not competence or supervision |
| Consumer health chatbots | General assistants | Answering questions | Precisely the design the evidence rules out for this population |

The gap is consistent across the table: **nobody is building for the unlicensed entrant as the user, and nobody is building for the preceptor dyad as the unit.** That gap exists because it is unglamorous, low-margin at the individual level, and legally constrained. Those are also the reasons it is defensible.

## 6. What compounds

Advantages that accumulate rather than being bought:

1. **Governed packs.** Orientation, scope, and escalation content distributed as versioned, reviewed Knowledge Packs with provenance and retirement paths ([`knowledge-commons/`](../knowledge-commons/README.md)). Content that says what it is authorized for is harder to copy than content that does not.
2. **Refusal and evaluation assets.** The refusal catalog in [DOCTRINE §6](DOCTRINE.md#6-refusal-catalog) with adversarial tests attached is a professional asset in its own right. Most products cannot say what they will refuse; this one can prove it.
3. **Localization with named review.** Serving a workforce that is 28 percent immigrant means scope statements reviewed by humans in each language — slow, unfashionable, and exactly the moat that machine translation cannot cross.
4. **Nurse trust and stewardship.** The project's standing rests on nurses steering it. Every shortcut that trades that for distribution destroys more than it gains.
5. **Public evidence trail.** Publishing what failed, including this document's own falsifiers, is a durable differentiator in a category where everyone claims outcomes.

## 7. Business model boundaries

Consistent with the project's published access terms, and stated here so no future pressure can quietly move them:

- The personal edition — orientation, scope, escalation, rehearsal — stays free to individual care workers. The population that most needs it earns a median of under $26,000 a year.
- Paid work, if it exists, is institutional: pilots, implementation support, governance work, and program design, priced to organizations, never to entrants.
- No revenue model may depend on labor-savings claims (doctrine P12), competency determinations (P6, P9), or engagement of low-wage workers as a metric.
- No sale of worker learning data. Ever. This is not a pricing decision.

## 8. Strategic bets and confidence

| Bet | Confidence | What it rests on | What would break it |
|---|---|---|---|
| The surge produces sustained low-tenure staffing, not a one-time cohort | High | BLS projections; PHI turnover; wage data | Durable wage/benefit reform lifting retention |
| Supervision, not headcount, is the binding constraint | High | NCSBN intent-to-leave; AACN capacity data | Faculty and preceptor capacity expanding materially |
| Novice-facing AI helps most when it does not answer | Moderate–high | Bean/Payne 2026; Lyell 2017; Lancet 2025; QJE 2025 gains concentrated in novices | A trial showing scoped clinical answering is safe and superior for this population |
| The individual worker is a viable first user without an employer | Moderate | The personal edition already operates this way | Individual adoption fails without employer distribution |
| Regulation will keep tightening around AI clinical identity and consequential decisions | Moderate–high | DE, OR, CA, WA title laws; multi-state consequential-decision statutes | Federal preemption relaxing the regime |
| The dyad is measurable | Low–moderate | Untested; the measurement design is the risk | Preceptors will not use it, or the signal is too noisy |

The lowest-confidence bets are load-bearing. That is why Stage 2 exists as a gate rather than an assumption.

## 9. Risks and stop conditions

| Risk | Early signal | Stop condition |
|---|---|---|
| **Harm through over-reliance** | Users acting on system output outside scope; escalation rates falling without a change in acuity | Any confirmed instance of the system standing between a worker and a needed escalation halts the affected surface until redesigned |
| **Deskilling** | Unassisted-practice scores declining over time in cohort measurement | Sustained decline halts feature expansion and triggers assistance reduction, not more assistance |
| **Scope creep into clinical answering** | Roadmap pressure framed as "users keep asking" | The refusal catalog is version-controlled; loosening a refusal class requires a written decision record and doctrine amendment, never a product decision |
| **Employer capture** | A pilot buyer requesting per-worker scores or productivity views | Refuse the feature; lose the deal if necessary; record it |
| **Understaffing alibi** | A deployment accompanied by reduced orientation, preceptor time, or staffing | Withdraw support for that deployment (doctrine P12) |
| **Regulatory foreclosure** | A jurisdiction classifying scope guidance to unlicensed workers as regulated clinical decision support | Stop in that jurisdiction; do not reinterpret the rule |
| **Founder-scale overreach** | Committing to institutional pilots the project cannot govern | Stage gates; no Stage 4 without named accountable capacity |

## 10. What success looks like in three years

Stated as falsifiable outcomes rather than aspirations:

1. A published, replicated measurement showing entrants using the orientation pack escalate appropriately more often and attempt out-of-scope judgments less often than matched controls — or a published finding that they do not.
2. Preceptors reporting, in instrumented measurement rather than testimonial, fewer low-value interruptions without a rise in missed escalations.
3. Unassisted performance in cohort measurement flat or improving, never quietly unmeasured.
4. A refusal catalog with adversarial tests that a third party can run.
5. Zero employment determinations made by the system. Not "few." Zero.

If items 1–3 come back negative and honestly published, this strategy has done its job. The failure mode to avoid is not being wrong; it is being unfalsifiable.
