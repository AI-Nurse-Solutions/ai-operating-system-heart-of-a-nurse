---
title: "Nursing Fundamentals — Concept Survey"
status: "Proposed research record"
version: "0.1"
date: "2026-08-22"
applicability: "Research record. Publication creates no curriculum, competency framework, credential, clinical validation, institutional authority, model, corpus, or PHI-processing capability."
---

# Nursing Fundamentals — Concept Survey

## 1. What this document is, and what it is for

This is the domain half of a question the rest of the repository has already
answered structurally. [`naio-os/models/FINE-TUNING-PLAN.md`](../naio-os/models/FINE-TUNING-PLAN.md)
specifies *how* a NAIO model would be built, gated, and released, and is
deliberately silent on *what is in it*. It names a corpus of 1,500 examples and
says the corpus is the critical path — then leaves the content to be decided.
This document supplies the input that decision needs: what nursing actually
consists of, stated in a form a system could be held to.

It is a survey, not a doctrine. It grades nothing, mandates nothing, and adopts
nothing. Two companion documents do the work that follows from it:
[`CODIFICATION.md`](CODIFICATION.md) sorts these concepts by whether they can be
encoded at all and where each one would live, and [`CORPUS.md`](CORPUS.md) turns
the codifiable remainder into training content.

**A note on what is deliberately excluded.** This survey covers nursing's
*organizing concepts* — the frameworks, standards, vocabularies, and disciplines
that structure practice. It does not cover clinical content: pathophysiology,
pharmacology, assessment findings, or intervention specifics. That omission is
not an oversight. Clinical content is the part a general-purpose model already
carries in quantity, and it is the part `edena-policy.hard_boundaries`
(`no_clinical_decisions`) forbids this system from applying to an identified
patient. A survey that led with it would be surveying the wrong thing.

## 2. The metaparadigm: what nursing takes as its subject

Nursing's disciplinary boundary is conventionally drawn by four concepts, after
Fawcett (1984): **person**, **environment**, **health**, and **nursing** itself.
Every nursing theory is, in effect, a claim about how these four relate.

The distinction that matters for a software system is narrow but load-bearing.
Medicine's organizing object is the *disease*; nursing's is the *person's
response* to a health condition — which is why nursing developed a parallel
diagnostic vocabulary rather than adopting the medical one. A patient has one
medical diagnosis and, simultaneously, a set of human responses to it that
nursing names, treats, and evaluates on its own authority.

This has a direct architectural consequence. A system that models nursing as
"medicine, with less authority" will get the scope boundary exactly backwards:
it will treat nursing as a restricted subset of clinical decision-making, and
will therefore see every guardrail as a limitation rather than as a description
of a different job. Nursing's independent domain is not a smaller version of
medicine's. It is a different object of attention.

The environment domain is also under active reinterpretation to include digital
and technological space — which is to say that an AI operating system deployed
into nursing is not external to the metaparadigm. It is a modification of the
environment concept, and nursing theory treats environment as causally related
to health outcomes.

## 3. Layer one — the ordering disciplines

These are the concepts that tell a nurse what to do *next*. They are procedural,
sequenced, and teachable, and they are the closest thing nursing has to
algorithms.

### 3.1 The nursing process (ADPIE)

**Assessment → Diagnosis → Planning → Implementation → Evaluation.** Developed in
the 1950s, it remains the legal and documentary spine of nursing practice in the
United States and is the structure the ANA standards are organized against. It is
cyclical rather than linear: evaluation feeds the next assessment.

Its significance here is structural rather than clinical. ADPIE is a general
problem-solving loop that happens to have been formalized for care: *gather what
is true, name the problem, state the desired outcome, act, check whether the
outcome moved*. Stripped of its patient object, that shape describes a governed
workflow specification almost exactly.

### 3.2 The NCSBN Clinical Judgment Measurement Model (NCJMM)

The NCJMM is the framework NCSBN built to make clinical judgment measurable in a
standardized examination, and it now anchors the Next Generation NCLEX. It is
layered, from Layer 0 (the whole space of clinical decisions) through Layer 1
(clinical judgment as a whole) and Layer 2 (form, refine, and evaluate
hypotheses) down to Layer 3's six cognitive skills:

| # | Skill | What it demands |
|---|---|---|
| 1 | Recognize cues | Separate relevant signal from noise in gathered data |
| 2 | Analyze cues | Link cues to history and presentation; form candidate explanations |
| 3 | Prioritize hypotheses | Rank by likelihood, seriousness, and urgency, with rationale |
| 4 | Generate solutions | Identify actions as indicated, contraindicated, or non-essential |
| 5 | Take action | Execute in priority order |
| 6 | Evaluate outcomes | Compare observed to expected; decide whether to revise |

Layer 4 holds the individual and environmental factors that modulate all six.

Two features make this the most important framework in this survey. First, it
already decomposes an ostensibly holistic capacity into six discrete, orderable,
separately-assessable steps — the decomposition work is done, publicly, by the
regulator. Second, it distinguishes *generating* solutions from *taking* action,
which is precisely the seam NAIO's governance runs along: an agent may occupy
steps 1 through 4 as a proposer and must stop at step 5.

### 3.3 Tanner's model of clinical judgment

Tanner (2006) synthesized two decades of research on clinical judgment into four phases — **noticing**,
**interpreting**, **responding**, **reflecting** — and defined clinical judgment
as "an interpretation or conclusion about a patient's needs, concerns, or health
problems, or the decision to take action (or not), use or modify standard
approaches, or improvise new ones as deemed appropriate by the patient's
response."

Three of Tanner's findings matter more than the four phases:

- **What the nurse brings matters more than the data.** Judgment is shaped by
  background, context, and the nurse's relationship with the patient before any
  cue is noticed.
- **"Knowing the patient" is a distinct epistemic state**, not a quantity of
  information — a grasp of this person's typical pattern that makes deviation
  perceptible.
- **Reflection is where judgment is actually built**, and it is the phase most
  reliably skipped.

The repository already implements this: `starter-kit/My-Nurse-AI-OS/15-Student-Study-OS/Sim-Case-NCJMM-Tanner.SKILL.md`
runs fictional scenarios on NCJMM structure and refuses to end without a Tanner
debrief, on the stated grounds that reflection is the skipped step.

### 3.4 Prioritization frameworks

Nursing carries several ranking heuristics that operate before and beneath
clinical judgment:

- **ABC** — airway, breathing, circulation.
- **Maslow's hierarchy** — physiological needs before safety before belonging.
- **Safety and risk reduction** — the imminent threat first.
- **Actual over potential** — an existing problem outranks a risk.
- **Acute over chronic**, **urgent over non-urgent**, **unstable over stable**.
- **Survival potential** in mass-casualty triage, which deliberately inverts the
  usual rule that the sickest go first.

These are the most algorithm-shaped objects in nursing, and the most dangerous to
port naively: each is a *tiebreaker applied by a licensed human who has already
assessed the patient*, not a decision procedure that can be run from a
description.

### 3.5 Structured communication

**SBAR** (Situation, Background, Assessment, Recommendation) is the dominant
handoff and escalation format; **I-PASS** and TeamSTEPPS variants extend it.
Its function is under-appreciated: SBAR exists to give a nurse a *sanctioned
script for asserting a judgment upward* across a steep authority gradient. The
"R" is the point. A communication tool that dropped the recommendation would
preserve the format and destroy the function.

The repository uses this already, at `governance-kit/prompts/escalation-sbar.md`.

## 4. Layer two — the normative frame

### 4.1 The ANA Code of Ethics for Nurses

Nine provisions, revised in 2025. In summary: compassion and respect for
inherent dignity (1); primary commitment to the patient (2); advocacy for
rights, health, and safety (3); authority, accountability, and responsibility
for practice (4); duties owed to self as to others (5); establishing and
improving the ethical environment of the workplace (6); advancing the profession
through scholarship and policy (7); collaboration to protect human rights and
reduce disparities (8); and the profession's collective obligation to integrate
social justice into nursing and health policy (9).

**Provision 7.5** is new in the 2025 revision and is the single most relevant
paragraph in nursing ethics to this repository. It addresses machine learning and
augmented intelligence directly, and requires that nurses critically question
technologies' underlying assumptions; that **reversibility** — the ability to
withdraw permission to access data, or to remove data entirely — be examined
before, during, and after development; that the risk of amplifying inequities
inherent in big data be acknowledged; and that the voice of nursing be present
when healthcare systems make these decisions.

`edena-policy.yaml` is built on it. The `data_withdrawal` hard boundary, the
`reversibility` cross-cutting class, the `health_equity` boundary, and the
"augmented, not autonomous" framing of `no_clinical_decisions` are each traceable
to Provision 7.5.

Provisions 4 and 5 carry a second, quieter obligation that a delegating system
must honor: the nurse's accountability for practice is *personal* and cannot be
handed to anything, and the duty to maintain competence is owed to oneself.

### 4.2 The ANA Standards

*Nursing: Scope and Standards of Practice* (4th ed., 2021) states eighteen
standards with competencies at three practice levels. Standards 1–6, the
**Standards of Practice**, are the nursing process: assessment, diagnosis,
outcomes identification, planning, implementation, and evaluation. Standards
7–18, the **Standards of Professional Performance**, cover ethics, advocacy,
respectful and equitable practice, communication, collaboration, leadership,
education, scholarly inquiry, quality of practice, professional practice
evaluation, resource stewardship, and environmental health.

The split is the useful part. Standards 1–6 are exercised on a patient.
Standards 7–18 are exercised on the nurse's own professional conduct, on
colleagues, on systems, and on the profession — and most of a nurse's working
life outside direct care falls under them. This survey returns to that division
repeatedly, because it turns out to be the seam along which nursing concepts
sort into codifiable and refused.

### 4.3 The international frame

The ICN Code of Ethics for Nurses supplies the global counterpart, and ICN's
digital-health work supplies the nursing-specific position on technology. WHO's
2024 guidance on the ethics and governance of AI for health, specifically for
large multi-modal models, supplies the automation-bias and equity framing that
`florence-x.yaml` cites.

## 5. Layer three — the accountability structures

This layer answers *who is answerable*, and it is where nursing has the most
directly transferable machinery for governing an autonomous agent.

### 5.1 Licensure, the Nurse Practice Act, and scope

Nursing authority is granted by a jurisdiction, not by an employer and not by
competence. Each US state's Nurse Practice Act defines the legal scope for each
licensure level, and scope **varies by jurisdiction and changes**. Employer
policy may narrow scope but never widen it. Individual competence may narrow the
scope a particular nurse should exercise but never widens the legal scope either.

Three constraints compound: *legal* scope (the NPA), *institutional* scope
(employer policy), and *personal* scope (this nurse's demonstrated competence).
A task is in scope only when it clears all three, and the nurse is obligated to
refuse when it does not — an obligation, not a discretion.

### 5.2 Delegation and the Five Rights

The 2019 ANA/NCSBN *National Guidelines for Nursing Delegation* govern how a
licensed nurse transfers a task to a delegatee. The **Five Rights** are:

| Right | The question it settles |
|---|---|
| Right task | Is this task delegable at all? |
| Right circumstance | Are the setting, resources, and patient stability appropriate? |
| Right person | Is this delegatee competent for this task on this patient? |
| Right direction and communication | Was the instruction specific, with expected results and limits? |
| Right supervision and evaluation | Is monitoring, intervention, and follow-up in place? |

Two rules sit underneath, and both are absolute:

- **The nursing process and nursing judgment are never delegable.** Assessment,
  diagnosis, planning, and evaluation require licensed expertise. A task may be
  transferred; the judgment that selected it may not.
- **Accountability does not transfer.** The delegating nurse remains accountable
  for the delegation decision and for the outcome, regardless of who performed
  the task.

This is the most important paragraph in this survey for system design. Nursing
has a mature, litigated, regulator-published doctrine for the exact problem an
agentic system poses — *how a licensed human safely hands work to a less
capable actor while remaining answerable for it* — and that doctrine's core
finding is that accountability is structurally non-transferable.

### 5.3 Advocacy and the duty to refuse

Standard 8 and Provisions 3 and 4 create an affirmative duty to advocate for the
patient against the system, including refusing an unsafe assignment and
escalating over a physician's objection. Nursing's professional identity treats
the correctly-placed refusal as a competency, not an obstruction.

## 6. Layer four — the formal vocabularies

Nursing has invested five decades in standardized terminology so that nursing
care can be represented, aggregated, and studied.

### 6.1 The NNN languages

- **NANDA-I** — nursing diagnoses: standardized names for the human responses
  nursing independently treats.
- **NIC** — Nursing Interventions Classification: what nurses do.
- **NOC** — Nursing Outcomes Classification: patient states sensitive to those
  interventions, with measurement scales.

Together ("NNN") they form a diagnosis → intervention → outcome chain with
published linkages, and they are the recognized formal core of the nursing care
plan.

### 6.2 The wider recognized set

The ANA recognizes a broader set of terminologies and data-element sets, among
them **ICNP** (diagnoses, actions, outcomes), the **Omaha System** (needs,
interventions, outcomes; an interface terminology), **CCC** (interface
terminology for assessment and documentation), **PNDS** (perioperative), plus
the reference terminologies **SNOMED CT** and **LOINC** — LOINC recognized by
ANA for nursing use in 2002 — and the **Nursing Minimum Data Set**, recognized in
1999. Ongoing IHTSDO/ICN harmonization work maps nursing terms into SNOMED CT
for interoperability.

### 6.3 Nurse-sensitive indicators

Nursing quality is measured through indicators demonstrably responsive to nursing
care, organized on Donabedian's structure/process/outcome frame and collected
nationally through ANA's NDNQI (now operated by Press Ganey):

- **Structure** — RN hours per patient day, total nursing hours per patient day,
  RN skill mix, RN education and certification.
- **Process** — fall-risk and pressure-injury risk assessment completion, nurse
  satisfaction.
- **Outcome** — falls and falls with injury per 1,000 patient days,
  hospital-acquired pressure injuries, CLABSI, CAUTI.

This is the vocabulary in which "did nursing care improve?" is a settled
empirical question rather than a rhetorical one — which makes it the vocabulary
any claim of benefit from an AI system will eventually be judged in.

## 7. Layer five — competence and formation

### 7.1 Benner's stages

Benner (1984), adapting the Dreyfus model, describes five stages: **novice**
(rule-governed, context-free), **advanced beginner** (recognizes recurring
components), **competent** (2–3 years; conscious, deliberate planning),
**proficient** (perceives situations as wholes; recognizes deviation from
expected patterns), and **expert** (fluid, intuitive grasp; no longer relies on
analytic rules for routine problems).

The mechanism, not the ladder, is the point. Expertise in Benner's account is a
migration *from* explicit rule-following *to* perceptual pattern recognition,
built by accumulated experience of concrete cases. Two consequences follow: an
expert often cannot articulate the rule they used, and a novice given the
expert's conclusion has not acquired the expert's perception. A system that
supplies conclusions to novices supplies the one thing that does not transfer.

### 7.2 QSEN

Six competencies with knowledge/skills/attitudes for each: **patient-centered
care, teamwork and collaboration, evidence-based practice, quality improvement,
safety, informatics.** Developed from 2005 in response to the medical-error
literature.

### 7.3 The AACN Essentials (2021)

The current competency-based framework for US nursing education: **ten domains**
— knowledge for nursing practice; person-centered care; population health;
scholarship for the nursing discipline; quality and safety; interprofessional
partnerships; systems-based practice; informatics and healthcare technologies;
professionalism; and personal, professional, and leadership development —
crossed with **eight featured concepts** (clinical judgment, communication,
compassionate care, diversity/equity/inclusion, ethics, evidence-based practice,
health policy, social determinants of health) and **four spheres of care**
(disease prevention and promotion of health and wellbeing; chronic disease care;
regenerative or restorative care; hospice, palliative, and supportive care).

The Essentials' explicit intent is a shift from a knowing paradigm to a doing
paradigm — competence demonstrated in context rather than knowledge recalled.

### 7.4 Concept-based curricula

Most US pre-licensure programs now organize teaching around transferable
concepts (oxygenation, perfusion, safety, mobility) with specific diseases as
exemplars, rather than around body systems. The pedagogical claim is that
concepts transfer to unseen exemplars and memorized content does not.

## 8. Layer six — the part that does not formalize

Nursing's own literature is unusually explicit that a substantial part of the
discipline resists codification. The items below are not gaps awaiting better
ontology; they are load-bearing and non-formal.

- **Knowing the patient.** Tanner's central finding: a grasp of this person's
  pattern that makes deviation perceptible. It is acquired through continuity of
  presence and does not survive transcription.
- **Presence and caring.** In Watson's caring theory the relationship is the
  therapeutic instrument, not the setting in which instruments are used.
- **Intuition — "something's off."** The proficient nurse's perception of
  deviation before it is measurable. Benner treats it as evidence of expertise,
  and it is frequently correct before the vital signs are.
- **Embodied assessment.** Skin turgor, work of breathing, the quality of a
  patient's grip — perceptual data with no accurate linguistic encoding.
- **Moral agency and moral distress.** The specific injury of knowing the right
  action and being institutionally prevented from taking it, and the moral
  resilience literature that responds to it.
- **Advocacy in the room.** Deciding to escalate over an objection, at personal
  cost, on incomplete information.

## 9. Nursing's failure modes, as an evidence base

A system that intends to help nursing has to be aimed at how nursing actually
fails. Four findings define the target.

**Surveillance is the mechanism.** The failure-to-rescue literature holds that
complications occur in hospitalized patients regardless of nursing, and that
whether a complication proves fatal depends on timely detection and management —
a surveillance function performed largely by nurses. Nurse-to-patient staffing
ratios are among the strongest predictors of failure to rescue, and higher
surveillance frequency is associated with significantly lower odds of it. Nursing's
protective effect is *continuous attention*, not any discrete intervention.

**Missed care is the pathway.** Lower RN staffing is consistently associated with
care left undone, and missed care is a validated indicator of staffing adequacy
and a plausible mediator between staffing and mortality. Nursing fails by
omission under time pressure far more often than by commission.

**Failure to rescue decomposes into four attributes** — errors of omission,
failure to recognize a change in condition, failure to communicate the change,
and failure in clinical decision-making. Three of those four are attention and
communication failures, not knowledge failures.

**Documentation burden is the thief.** Nurses spend an estimated 19–35 percent of
their time documenting in the EHR, against roughly 9 percent on paper, and
documentation burden is repeatedly associated with workload and burnout.

Read together these produce the design constraint that should govern any AI
system entering nursing: **the beneficial target is documentation and
administrative burden; the protected function is surveillance; and the two are
connected, because time reclaimed from the first is the supply of the second.**
An intervention that reduces documentation time and simultaneously occupies the
nurse's attention has cost more than it saved. This is the same constraint
[`care-workforce-surge/`](../care-workforce-surge/) reaches from workforce
evidence — supervision is the scarce resource — arrived at from patient-outcome
evidence instead.

## 10. Sources

Frameworks and standards

- ANA, [*Nursing: Scope and Standards of Practice*, 4th ed. (2021)](https://www.nursingworld.org/nurses-books/nursing-scope-and-standards-of-practice-4th-edit/) — 18 standards.
- ANA, [Code of Ethics for Nurses, 2025 revision — Provision 7.5](https://codeofethics.ana.org/provision-7-5) — technology, AI, reversibility.
- [Nine provisions of the ANA Code, as reproduced in *Nursing Management and Professional Concepts* (NCBI Bookshelf)](https://www.ncbi.nlm.nih.gov/books/NBK610435/).
- ANA/NCSBN, [*National Guidelines for Nursing Delegation* (2019)](https://www.nursingworld.org/globalassets/practiceandpolicy/nursing-excellence/ana-position-statements/nursing-practice/ana-ncsbn-joint-statement-on-delegation.pdf) — Five Rights; non-delegable judgment; retained accountability.
- NCSBN, [Clinical Judgment Measurement Model](https://www.nclex.com/clinical-judgment-measurement-model.page).
- OpenStax, [*Clinical Nursing Skills* §28.1 — CJMM layers and six cognitive skills](https://openstax.org/books/clinical-nursing-skills/pages/28-1-clinical-judgment-measurement-model).
- Tanner, C. A. (2006). [Thinking like a nurse: a research-based model of clinical judgment in nursing](https://pubmed.ncbi.nlm.nih.gov/16780008/). *Journal of Nursing Education*, 45(6), 204–211.
- [QSEN competencies (pre-licensure KSAs)](https://www.qsen.org/competencies-pre-licensure-ksas).
- AACN, [*The Essentials: Core Competencies for Professional Nursing Education* (2021) — FAQ](https://www.aacnnursing.org/Portals/0/PDFs/Essentials/Essentials-Revised-Frequently-Asked-Questions.pdf); domains, concepts, and spheres as summarized [here](https://corehighered.com/en/blog/a-quick-guide-to-the-new-aacn-essentials).
- Benner, P. (1984). *From Novice to Expert*; overview via [British Journal of Nursing](https://www.britishjournalofnursing.com/content/nursing-theory/shaping-professional-nursing-practice-using-benners-novice-to-expert-theory).

Terminology and measurement

- NLM, [Nursing resources for standards and interoperability](https://www.nlm.nih.gov/research/umls/Snomed/nursing_terminology_resources.html) — NANDA-I, NIC, NOC, ICNP, Omaha, CCC, PNDS, SNOMED CT, LOINC.
- ANA, [Inclusion of recognized terminologies within EHRs](https://www.nursingworld.org/globalassets/docs/ana/inclusion-of-recognized-terminologies-within-ehrs-and-other-health-information-technology-solutions.pdf).
- ONC, [Standard Nursing Terminologies: A Landscape Analysis (2017)](https://www.healthit.gov/sites/default/files/snt_final_05302017.pdf).
- [NDNQI overview and indicator set](https://www.pressganey.com/industry/healthcare/quality/ndnqi/); [OJIN, NDNQI (2007)](https://ojin.nursingworld.org/table-of-contents/volume-12-2007/number-3-september-2007/nursing-quality-indicators/).

Evidence on failure modes

- Mushta, J. et al. (2018). [Failure to rescue as a nurse-sensitive indicator](https://onlinelibrary.wiley.com/doi/10.1111/nuf.12215). *Nursing Forum*.
- [The impact of nursing surveillance on failure to rescue](https://pubmed.ncbi.nlm.nih.gov/21696091/).
- [What impact does nursing care left undone have on patient outcomes?](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6001747/)
- [The association between nurse staffing and omissions in nursing care](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6033178/).
- [EHR system use and documentation burden of acute and critical care nurses](https://pmc.ncbi.nlm.nih.gov/articles/PMC11491602/); [Evaluating nurses' perceptions of documentation in the EHR (JMIR Nursing, 2025)](https://nursing.jmir.org/2025/1/e69651).

Theory

- Fawcett's four-concept metaparadigm, and the environment domain reconsidered for space, place, and technology: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11586616/).
- ANA, [What is nursing theory and why is it important](https://www.nursingworld.org/content-hub/resources/becoming-a-nurse/nursing-theory/).
