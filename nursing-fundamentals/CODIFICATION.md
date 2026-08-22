---
title: "Nursing Concepts — Codification Register"
status: "Proposed research record"
version: "0.1"
date: "2026-08-22"
applicability: "Research record. Nothing here amends edena-policy.yaml, florence-x.yaml, any schema, or any shipped artifact, and nothing here creates a curriculum, competency framework, credential, clinical validation, institutional authority, or PHI-processing capability. Every proposal is a proposal, and adoption runs through the normal governance channel."
---

# Nursing Concepts — Codification Register

## 1. The question

[`FUNDAMENTALS.md`](FUNDAMENTALS.md) surveys roughly forty organizing concepts in
nursing. This document sorts them: which can be encoded into Nurse AI OS at all,
where each one belongs if it can, and which must be refused.

The sorting rule is not obvious, and getting it wrong in the obvious way is the
main risk this document exists to prevent.

## 2. The sorting rule: attachment, not formality

The intuitive approach is to sort by formality — encode the parts of nursing that
are already structured, leave the rest. That approach fails, and it fails in the
most expensive direction.

Nursing's most rigorously formalized artifacts are NANDA-I, NIC, and NOC: tens of
thousands of controlled terms, published linkages, validated measurement scales.
They look like the ideal training substrate. Every one of those terms attaches to
an identified patient. A model fluent in them is a model fluent in generating
nursing care plans for real people — the exact output `no_clinical_decisions`
exists to refuse. The most codifiable artifact in nursing is the least
codifiable *here*.

Meanwhile the delegation decision, the prioritization habit, and the reflective
debrief look informal and situational. Each attaches to the nurse's own work and
the nurse's own accountability. Each is safely codifiable, and two of them are
already partly codified in this repository.

So the register sorts on a different question:

> **The attachment test.** Ask what the concept's object is. If completing the
> thought requires naming a patient, it is refused here. If completing it
> requires naming only the nurse, their work, and their accountability, it is a
> candidate for codification.

This is not a new boundary. It is the existing `hard_boundaries` line, applied to
domain content instead of to user requests — and it happens to coincide with a
division nursing already makes for its own reasons. ANA Standards 1–6, the
Standards of Practice, are exercised *on a patient*. Standards 7–18, the
Standards of Professional Performance, are exercised on the nurse's own conduct,
on colleagues, on systems, and on the profession. The attachment test says: this
system's domain is Standards 7–18.

That is a much larger territory than it sounds. Most of a nurse's professional
life — the committee, the policy draft, the education module, the QI project, the
certification study plan, the shared-governance proposal, the side business —
falls under Standards 7–18 and touches no patient at all.

## 3. The dispositions

Six destinations. The distinctions between them are operational: each names a
different file, a different enforcement mechanism, and a different failure mode.

| Code | Disposition | Where it lives | Why there |
|---|---|---|---|
| **P** | Policy | `naio-os/config/edena-policy.yaml`, `florence-x.yaml`, and the evaluator that reads them | Deterministic, testable, versioned, enforced before the model is consulted |
| **S** | Schema | a JSON Schema enum or field | Structural; enforced by validation, not by the model behaving well |
| **R** | Retrieval | a versioned Knowledge Pack per [`knowledge-commons/`](../knowledge-commons/), cited at use | Jurisdiction-specific, revised on its own cycle, or must carry provenance |
| **W** | Weights | the fine-tuning corpus | A learned habit of reasoning or expression, where being wrong produces a reviewable proposal |
| **H** | Human | nowhere in the system | Belongs to the nurse; encoding it would be a claim the system cannot honor |
| **X** | Refused | nowhere, deliberately | Codifying it would violate a hard boundary, a prohibited practice, doctrine, or a license |

Two assignment rules follow directly from the fine-tuning plan and are worth
stating because they are easy to violate:

- **Nothing that decides is W.** The plan's §3 correction — the model proposes,
  the policy engine decides — means no concept that determines a gate, a tier, a
  permission, or a boundary may be trained into weights. If it decides, it is P.
  A model that emits a governance verdict manufactures a phantom control.
- **Nothing that revises on its own calendar is W.** Nurse Practice Acts change
  by state legislature; the ANA Code was revised in 2025; the Essentials were
  revised in 2021. A model that memorized any of them will assert the superseded
  version confidently and without a version string. That is R, always.

## 4. The register

Dispositions may be compound: a concept can be enforced as policy *and* explained
in trained prose.

### 4.1 Ordering disciplines

| Concept | Disposition | Destination and rationale |
|---|---|---|
| Nursing process (ADPIE), as a problem-solving shape | **W** | The spine of the `workflow_spec` task: gather → name → state the outcome → act → evaluate. Trained on non-clinical work only. |
| Nursing process applied to a patient | **X** | Standards 1–6; `no_clinical_decisions`. Also non-delegable under the 2019 guidelines — a system cannot receive what a nurse may not hand over. |
| NCJMM six cognitive skills | **W**, bounded | Trainable as tutoring structure on fictional cases (as `Sim-Case-NCJMM-Tanner.SKILL.md` already does) and as a reasoning frame for non-clinical analysis. Never run on a described real patient. |
| NCJMM step 5, "take action" | **P** | The seam. Steps 1–4 are proposal; step 5 is where `side_effects` and gates apply. Codified in the existing tier ladder. |
| NCJMM layers 0–4 | **R** | Reference framework; cite with version. |
| Tanner's four phases | **W** | `noticing → interpreting → responding → reflecting` is the natural shape of the `critique` task. The reflecting phase is the whole product. |
| "Knowing the patient" | **H** | Tanner's own finding: it is not a quantity of information. A system that claimed it would be asserting an epistemic state it cannot occupy. |
| Prioritization frameworks (ABC, Maslow, safety, actual-over-potential) | **W** for the nurse's *own* work; **X** applied to a patient | Ranking a nurse's competing obligations is codifiable. Ranking a patient's problems is clinical judgment by another name. |
| SBAR / structured escalation | **W** | Already at `governance-kit/prompts/escalation-sbar.md`. Train the format *including the Recommendation* — dropping the R preserves the shape and destroys the function. |
| Commit-then-compare | **P** and **W** | Already doctrine in [`nurse-formation/`](../nurse-formation/) and [`care-workforce-surge/`](../care-workforce-surge/). The user commits before the system compares; enforced by the interaction, expressed by the model. |

### 4.2 Normative frame

| Concept | Disposition | Destination and rationale |
|---|---|---|
| ANA Code, Provision 7.5 | **P** — already codified | `edena-policy` already rests on it: `data_withdrawal` and the `reversibility` classes from its reversibility requirement, `health_equity` from its inequity warning, `no_clinical_decisions` from augmented-not-autonomous. |
| ANA Code, provisions 1–9 | **R** | Revised 2025. Cite with edition; never memorize. |
| Provisions 4 and 5 (personal accountability; duty to self) | **P** | Provision 4 is the ancestor of `oversight_follows_delegation`. Provision 5 is the ancestor of the wellbeing posture in `florence-x.instruments.caring_heart`. |
| ANA Standards 7–18 | **R** now; **S** only after a governance change | These name the legitimate territory. Promoting them to a schema enum means the runtime must be able to enforce them; per plan §12 Q2, that change is made *before* any corpus cites it, never after. |
| ANA Standards 1–6 | **X** | Patient-attached by definition. |
| ICN Code; WHO LMM guidance | **R** | Already cited in `edena-policy.review_basis` and `florence-x`. |
| Duty to refuse an unsafe assignment | **W** | The `refusal_redirect` task's model. Nursing treats a correctly-placed refusal as competence, not obstruction; the trained refusal should carry that tone. |

### 4.3 Accountability structures — the richest vein

| Concept | Disposition | Destination and rationale |
|---|---|---|
| **Accountability does not transfer** | **P** — already codified | The 2019 guidelines' central holding. `delegation.oversight_follows_delegation: true`, `inherit_ceiling: true`, `may_exceed_parent_tier: false`, `leaf_default_tier: green`, and `provenance_required: true` are, collectively, this principle expressed in YAML. Nursing arrived at it through malpractice law; agent security arrived at it through OWASP ASI07/ASI10; they are the same rule. |
| **Nursing judgment is never delegable** | **P** — already codified | The direct ancestor of `no_clinical_decisions` and of `human_agency`'s non-removable Green/Yellow gates. |
| Right task | **P** + **S** | Maps to `functionality.tool_classes`: is this action's class available at this tier at all? |
| Right circumstance | **P** | Maps to `sphere_ceilings[sphere]` combined with `reversibility.classes`. |
| Right person | **W** | Maps to the model's honest statement of its own fitness and limits — the one Right that is a judgment about the delegatee, and the delegatee here is the agent. Trained, not enforced; its failure mode is a bad self-assessment a human reads. |
| Right direction and communication | **P** + **W** | The written scope `orange` already requires (`requires_written_scope`), plus the trained articulation of limits and expected results. |
| Right supervision and evaluation | **P** — already codified | Maps to `gates` and `monitoring`. The five gate types are five supervision intensities. |
| Legal scope (Nurse Practice Act) | **R**, never **W** | Varies by jurisdiction, changes by legislature. `license_respect` enforces *that* scope binds; retrieval supplies *what* it says, with an effective date. |
| Institutional scope (employer policy) | **R**, user-supplied | Not knowable centrally. |
| Personal scope (this nurse's competence) | **H** | Self-declared in SOUL; never inferred, never scored. |
| Scope-narrowing is legitimate; scope-widening is not | **P** — partly codified | The same asymmetry as employer policy versus the Nurse Practice Act. `progression` gates every tier increase behind an unlock — governance module, written scope, monitoring, review board — and the training schema states that `role_id` "never raises a ceiling." Whether a SOUL export can *raise* a `sphere_ceiling` is decided by the export path rather than by the policy file, whose comment says only that the defaults are overwritten. Confirm that before any document relies on the asymmetry being mechanical. |

### 4.4 Formal vocabularies — the refusals

| Concept | Disposition | Rationale |
|---|---|---|
| NANDA-I, NIC, NOC (NNN) | **X** | Three independent reasons, any one sufficient. (1) *Attachment*: every term's object is an identified patient; fluency in NNN is fluency in the refused output. (2) *Licensing*: NANDA-I, NIC, and NOC are copyrighted, separately-licensed products, not open standards. This project signs and redistributes artifacts under Apache-2.0 and deliberately prefers Apache-2.0 base models to avoid exactly this class of review (plan §8). Ingesting licensed terminology into a redistributed GGUF reopens it. (3) *Phantom competence*: a care plan that is structurally perfect and clinically wrong is harder for a reviewer to catch than one that is obviously wrong. |
| ICNP, Omaha, CCC, PNDS | **X** for clinical use; **R** for informatics literacy | A nurse learning what standardized terminology *is* may retrieve a description. The system does not speak these languages about a person. |
| SNOMED CT, LOINC | **R** | Reference terminologies; permissible as informatics reference. Same patient-attachment limit at use. |
| Nursing Minimum Data Set | **R** | Reference. |
| Nurse-sensitive indicators (definitions, Donabedian frame) | **R** + **W** at concept level | A nurse leader designing a QI project legitimately needs these definitions. |
| NDNQI benchmark data | **X** | Proprietary database; also, unit-level benchmark comparison drifts toward institutional performance claims the repository refuses. |
| Any indicator computed on real unit or patient data | **X** | `no_phi`; and see §6.4. |

### 4.5 Competence and formation

| Concept | Disposition | Rationale |
|---|---|---|
| Benner's five stages, as a register control | **R** + **W** | Legitimate use: a *self-declared* stage in SOUL tunes how much scaffolding an explanation carries. A novice gets the rule made explicit; an expert gets the exception flagged. |
| Benner's stages, as an assessment | **X** | `nurse-formation` doctrine: AI never grades alone and never gates a career. `care-workforce-surge`: no competency scoring. Inferring a nurse's stage from their behavior is also `surveillance_emotion_inference`-adjacent and would be a `social_scoring` prohibited practice if applied comparatively. |
| Benner's transfer mechanism (rules → perception) | **W**, as a constraint on style | The finding that a novice given an expert's conclusion has not acquired the expert's perception is the strongest available argument for commit-then-compare. It should shape how the model answers, not just what it refuses. |
| QSEN six competencies | **R** | Stable, public, well-defined; cite. |
| AACN Essentials domains, concepts, spheres | **R** | Revised 2021; will be revised again. |
| Concept-based curriculum method | **R** | The organizing principle for Knowledge Pack structure. |

### 4.6 The uncodified core

Every row here is **H**, and each carries a specific design implication that is
not "do nothing."

| Concept | Design implication |
|---|---|
| Knowing the patient | The system must be able to *receive* it as a stated input and treat it as authoritative over its own analysis. It must never generate it. |
| Presence and caring | **X** to simulate. A system that performs caring violates `transparency` — it implies a relationship it does not have. |
| Intuition — "something's off" | Provide a first-class channel for the nurse to assert it, which escalates without requiring justification. The system never asserts it. |
| Embodied assessment | Out of scope entirely; the modality is unavailable. |
| Moral distress | **R** for support resources; **X** to detect. Inferring a nurse's emotional state from usage is `surveillance_emotion_inference`, a prohibited practice at every tier. This is the single most likely well-intentioned violation in a nurse-wellbeing product. |
| Advocacy in the room | **H**. The system may help prepare the argument; the decision to make it, at personal cost, is the nurse's. |

### 4.7 Failure modes as constraints

| Finding | Disposition | Design consequence |
|---|---|---|
| Surveillance is nursing's protective mechanism | **P** as doctrine | Already: "never the last check before a patient" (`care-workforce-surge`). Extend: an interaction that consumes attention during care hours is out of doctrine even if it saves time on paper. |
| Missed care is the pathway to harm | **R** | The metric to watch. Any claimed time saving is only real if it does not appear as care left undone. |
| Failure to rescue decomposes into attention and communication failures | **R** | Three of its four attributes are not knowledge failures — which is a direct argument against an answer-engine design. |
| Documentation burden at 19–35% of nursing time | **R** | The legitimate target, and the only one of the four that names work an agent may actually take. |
| Automation bias | **P** — already codified | `florence-x.doctrine.automation_bias_countermeasures` and `gates.meaningful_review`. |
| Deskilling | **P** as doctrine + measured | Already tracked as a harm in `care-workforce-surge`; the monthly unassisted check is the instrument. |

## 5. What is already codified, and what the delta is

The register above is mostly a description of work already done. That is worth
stating precisely, because it changes what remains to be built.

**Already in force.** Nursing's accountability doctrine is the substrate of
`edena-policy.yaml`, whether or not the file says so: non-transferable
accountability in `delegation`, non-delegable judgment in `no_clinical_decisions`
and `human_agency`, supervision intensity in `gates`, scope asymmetry in
`sphere_ceilings`, and Provision 7.5 across `data_withdrawal`, `reversibility`,
and `health_equity`. NCJMM and Tanner are implemented as pedagogy in
`Sim-Case-NCJMM-Tanner.SKILL.md`. SBAR is implemented at
`governance-kit/prompts/escalation-sbar.md`. Commit-then-compare and the refusal
to grade are doctrine in `nurse-formation/` and `care-workforce-surge/`.

**The delta is three items.**

1. **The Five Rights pre-flight speaks a vocabulary the runtime cannot enforce.**
   `governance-kit/prompts/five-rights-preflight.md` is the most direct nursing
   codification in the repository, and it classifies in `D0–D4`, `Red-P`, and
   `Red-E` — precisely the phantom vocabulary the fine-tuning plan §3 identifies
   as non-existent. `edena-policy` v2.0.0 defines `green`/`yellow`/`orange`/`red`
   and no data taxonomy at all. *Proposal:* rewrite the pre-flight against
   `tool_classes`, `reversibility`, `sphere`, `hard_boundaries`, and the five
   `gates`. The Five Rights map onto those cleanly — §4.3 above gives the
   mapping — so this is a translation, not a redesign. It is a prerequisite for
   any corpus that cites it, for the same reason plan §12 Q2 gives.

2. **The nursing ancestry of the policy is undocumented.** `edena-policy.yaml`'s
   `review_basis` cites Knight Columbia, NIST, CSA, OWASP, EU AI Act, ISO, WHO,
   ANA 7.5, and ICN. It does not cite the 2019 ANA/NCSBN delegation guidelines,
   which is the source of its deepest structural commitment. *Proposal:* add the
   citation, and add a comment on the `delegation` block naming the ancestor.
   This costs nothing and makes the policy legible to the profession it governs —
   a nurse reviewer who recognizes the Five Rights in the delegation block will
   trust and audit it differently than one reading it as generic agent security.

3. **No document states the attachment test.** The `no_phi` and
   `no_clinical_decisions` boundaries are enforced against user *input*. Nothing
   states the corresponding rule for *content the project itself authors* — which
   is what a training corpus is. *Proposal:* the test in §2 above, adopted as a
   corpus rule in [`CORPUS.md`](CORPUS.md) §7.

## 6. Five ways this goes wrong

Each of these is a failure that would look like success.

**6.1 The phantom control.** Training a model to emit nursing-governance
vocabulary the runtime cannot enforce — a NANDA label, an acuity score, an
`edena_tier` — produces output that reviewers read as governance and that nothing
checks. This is plan §3's finding, restated for domain content: a nursing concept
that decides must be P or it must not exist.

**6.2 Ontology capture.** Adopting NNN because it is available and well-formed,
then discovering the product has become a care-planning tool. The formality of an
ontology is not evidence that using it is safe; it is evidence that using it will
be fluent.

**6.3 The care-plan trap.** The nursing process is genuinely a general
problem-solving loop, which makes it tempting to train on real care plans "just
for the structure." The structure is not separable from the content in the
training signal. Train the shape on non-clinical work, or do not train it.

**6.4 Surveillance inversion.** Nursing's protective mechanism is the nurse's
continuous attention to the patient. The failure mode is building a system that
watches the *nurse* instead — inferring competence from usage, wellbeing from
tone, engagement from activity. Every instance is a prohibited practice under
`prohibited_practices` (`social_scoring`, `surveillance_emotion_inference`), and
each arrives wearing a benevolent justification.

**6.5 Competence scoring by the back door.** No component of this system may
produce a number that stands in for a nurse's competence — not a quiz score, not
a readiness percentage, not a Benner stage. `nurse-formation` prohibits AI
grading alone and career gating; `care-workforce-surge` prohibits competency
scoring. A "learning progress" metric that an employer could read as an
assessment has violated both, whatever it is called.

## 7. What is refused outright

For a system operating under `edena-policy` v2.0.0, no component — policy,
schema, retrieval pack, model, or prompt — may:

- produce a nursing diagnosis, care plan, intervention selection, or outcome
  evaluation for an identified person;
- prioritize an identified patient's problems, or contribute to acuity,
  triage, or assignment decisions;
- speak NNN, ICNP, Omaha, CCC, or PNDS *about a person*;
- infer or assert a nurse's competence, Benner stage, emotional state, moral
  distress, or burnout risk from their behavior in the system;
- score, rank, or compare nurses, students, or patients;
- generate a patient-specific handoff, or occupy the surveillance function;
- assert what a Nurse Practice Act says without retrieving it with a
  jurisdiction and an effective date;
- simulate caring, presence, or a therapeutic relationship, or represent itself
  in a way that implies clinical authority.

The first seven follow from `hard_boundaries` and `prohibited_practices`. The
last follows from `transparency`, and it is the one most likely to be violated by
good intentions about warmth.

> Nursing already solved the problem of handing work to a less capable actor
> while staying answerable for it. The answer was never to make the delegatee
> more trustworthy. It was to keep the accountability where the license is.
