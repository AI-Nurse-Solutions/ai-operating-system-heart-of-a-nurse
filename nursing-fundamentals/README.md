# Nursing Fundamentals

> **Status: proposed research record, version 0.1 (2026-08-22).** These documents survey a body of professional knowledge and propose how it could be encoded. They establish no curriculum, competency framework, credential, assessment instrument, clinical validation, institutional authority, model, training corpus, or permission to process PHI. Nothing here amends `naio-os/config/edena-policy.yaml`, `florence-x.yaml`, or any shipped schema.

[`naio-os/models/FINE-TUNING-PLAN.md`](../naio-os/models/FINE-TUNING-PLAN.md)
specifies how a NAIO model would be built and gated, names the corpus as the
critical path, and leaves its contents open. This directory supplies the missing
half: what nursing consists of, which parts of it a system may encode, and what
the training content would actually be.

## The finding

The intuitive way to decide what to encode is to sort nursing by formality —
take the parts that are already structured and leave the rest. That approach
inverts the correct answer.

> Nursing's most rigorously formalized artifacts — NANDA-I, NIC, NOC, tens of
> thousands of controlled terms with published linkages — attach to an
> identified patient. Fluency in them is fluency in the output
> `no_clinical_decisions` exists to refuse. They are the **least** codifiable
> thing here, precisely because they are the most codified thing in nursing.
>
> Meanwhile the delegation decision, the prioritization habit, and the
> reflective debrief look situational and informal. Each attaches to the nurse's
> own accountability. They are the **most** codifiable, and two are already
> partly encoded in this repository.

So the register sorts on attachment rather than on structure:

> **The attachment test.** If completing the thought requires naming a patient,
> it is refused here. If completing it requires naming only the nurse, their
> work, and their accountability, it is a candidate.

That line is not new — it is the existing hard boundary, applied to content the
project authors rather than to requests users make. What is new is noticing that
it coincides with a division nursing already makes: ANA Standards 1–6 are
exercised on a patient; Standards 7–18 are exercised on the nurse's own conduct,
on colleagues, on systems, and on the profession. **This system's domain is
Standards 7–18** — which is where most of a nurse's working life happens.

A second finding runs underneath the first. Nursing's delegation doctrine is a
mature, regulator-published answer to the exact problem an agentic system poses:
how a licensed human safely hands work to a less capable actor while remaining
answerable for it. Its holdings are that nursing judgment is never delegable and
that **accountability does not transfer**. `edena-policy.yaml` already encodes
both — in `no_clinical_decisions`, in the non-removable Green and Yellow gates,
and in `delegation.oversight_follows_delegation` — having reached them through
OWASP and Knight Columbia. Nursing got there through malpractice law. It is the
same rule, and the policy does not yet cite the nursing source.

## Documents

- **[Concept Survey](FUNDAMENTALS.md)** — what nursing is, in six layers: the
  ordering disciplines (ADPIE, NCJMM, Tanner, prioritization, SBAR), the
  normative frame (ANA Code and Provision 7.5, the 18 Standards, ICN, WHO), the
  accountability structures (licensure, scope, the Five Rights of Delegation),
  the formal vocabularies (NNN, the recognized terminologies, nurse-sensitive
  indicators), competence and formation (Benner, QSEN, the AACN Essentials), and
  the part that does not formalize. Closes with the evidence on how nursing
  actually fails — surveillance, missed care, failure to rescue, documentation
  burden — with sources.
- **[Codification Register](CODIFICATION.md)** — every concept sorted into six
  dispositions (Policy, Schema, Retrieval, Weights, Human, Refused), what is
  already encoded today, the three-item delta, five ways this goes wrong, and
  what is refused outright.
- **[Corpus Specification](CORPUS.md)** — the four task slices mapped to their
  nursing ancestors, content inventories against the plan's slice sizes, the
  composition of a nursing-grounded frozen eval set, a nursing-specific injection
  suite, and the corpus exclusion list.
- **[Illustrative records](examples/illustrative-records.jsonl)** — one record
  per task, validated by the shipped dataset gate. Not a corpus: `dataset_version`
  is `0.0.0`, every record is `draft`, none carries a `split`.

## Governing maxims

> **Sort by what a concept attaches to, not by how formal it looks.**

> **The corpus is nursing's reasoning shape, exercised on the work nurses do that is not care.**

> **Nursing already solved delegation. The answer was never to make the delegatee more trustworthy — it was to keep accountability where the license is.**

> **The beneficial target is documentation burden. The protected function is surveillance. Time reclaimed from the first is the supply of the second.**

## The three proposed changes

Stated here so they are not buried. Each is a proposal; none is adopted by
publication, and each would run through the normal governance channel.

1. **Rewrite the Five Rights pre-flight against the enforced vocabulary.**
   `governance-kit/prompts/five-rights-preflight.md` is the repository's most
   direct nursing codification, and it classifies in `D0–D4`, `Red-P`, and
   `Red-E` — the phantom vocabulary the fine-tuning plan §3 identifies as
   existing nowhere in the runtime. The Five Rights map cleanly onto
   `tool_classes`, `reversibility`, `sphere`, `hard_boundaries`, and the five
   `gates`; this is a translation, not a redesign.
2. **Cite the nursing ancestor in the policy.** `edena-policy.review_basis`
   lists nine sources and omits the 2019 ANA/NCSBN *National Guidelines for
   Nursing Delegation*, which is the origin of its deepest structural
   commitment.
3. **State the attachment test as a corpus rule.** The hard boundaries are
   enforced against user input; nothing states the corresponding rule for content
   the project itself authors.

## Relationship to the rest of Nurse AI OS

This is **not** a post-setup role lane, a build kit, a download, or a curriculum.
It is a research record that feeds documents which already exist:

- [**`naio-os/models/`**](../naio-os/models/) — the plan this specifies content
  for. Its method, gates, and the model-proposes/engine-decides rule are
  inherited unchanged, gate zero included: if the prompted baseline passes, no
  corpus is authored.
- [**EDENA**](../naio-os/config/edena-policy.yaml) — the enforced vocabulary.
  Every disposition in the register resolves to a file that exists; no document
  here introduces governance language the runtime cannot enforce.
- [**Nurse Formation**](../nurse-formation/) — supplies the learning doctrine the
  register defers to: commit-then-compare, AI never grading alone, never gating a
  career.
- [**Care Workforce Surge**](../care-workforce-surge/) — reaches the same
  constraint from workforce evidence that §9 of the survey reaches from
  patient-outcome evidence. Supervision is the scarce resource; surveillance is
  what it buys.
- [**Knowledge Commons**](../knowledge-commons/) — the destination for every
  concept graded **R**: versioned, provenance-bearing, retrieved with an
  effective date rather than memorized into weights.

## What is deliberately absent

No clinical content — no pathophysiology, pharmacology, assessment findings, or
intervention specifics. No nursing diagnosis, care plan, or standardized-
terminology vocabulary usable about a person. No competence score, readiness
metric, or Benner-stage assignment. No inference of a nurse's emotional state,
burnout risk, or moral distress. No jurisdiction-specific scope claim stated
without retrieval. No simulated caring.

## Licensing

Repository documentation, under the documentation license stated in the root
[README](../README.md).
