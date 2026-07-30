# NIN Nurse Formation

> **Status: proposed education doctrine and operating playbook, version 0.1.** This directory specifies how AI may participate in the education and training of adult nurse learners. It does not establish a curriculum, school partnership, faculty development program, assessment instrument, competency framework, continuing-education provider, accreditation relationship, proctoring system, institutional authority, or permission to process PHI or learner records beyond what applicable law and local policy allow.

The proposed public name is **NIN Nurse Formation**. The word is chosen deliberately: nursing education does not deliver content — it **forms** nurses. Formation is the joint growth of clinical judgment, skilled know-how, and professional identity, and it is the one output of nursing education that AI must strengthen and may never quietly replace.

## Documents

- [Doctrine](DOCTRINE.md) — constitutional principles for AI in adult nurse education and training: formation over efficiency, the five formation rules, role and authority boundaries, AI literacy, assessment, equity, learner privacy, human-in-the-loop lifecycle, claims discipline, and the embedding map into Nurse AI OS.
- [Operational Playbook](PLAYBOOK.md) — the program adoption arc, educator course moves, learner practices, preceptor procedures, assessment and integrity workflows, bias-sighting route, HITL adoption gates, measures, and explicit deferrals.

## Four formation arcs

```text
Enter      → pre-licensure students becoming safe beginners
Transition → newly licensed nurses in residency and orientation
Grow       → practicing nurses in continuing development and specialty change
Teach      → educators, preceptors, and mentors being formed to form others
```

All four arcs are adult learners under one doctrine. The same rules
apply whether the learner is nineteen or fifty-nine: adults own their
learning, commitment precedes comparison, and evaluative authority
stays human.

## The formation quartet

Formation runs on four supports together — none substitutes for
another:

```text
AI tutor      → personalization, deliberate practice, the growth mirror
Human mentor  → tacit know-how, practical wisdom, transfer of values
Community     → belonging, integration, collaboration
Proof of work → a portfolio of actual outputs, not scores alone
```

The ecosystem's [ASCEND program page](https://nurse-ai-os.org/ascend/)
already frames the same quartet — AI mentor, human mentorship,
community, and credential evidence; this doctrine gives it
constitutional form in [§4.5](DOCTRINE.md#45-the-formation-quartet).

> **Agents coach. Learners commit. Educators judge. Institutions credential. Nurses steward.**

> **The struggle is the curriculum. AI may scaffold the struggle; it must never perform it.**

> **AI never grades alone, and it never gates a career.**

## Research anchors

This doctrine synthesizes five commissioned research briefs — July
2026 AI-assisted literature scans prepared for this doctrine and
reviewed by the founder, covering (1) nurse-led bias mitigation,
(2) the AI-in-learning policy landscape, (3) the NIN-NAIO role and
architecture, (4) integration challenges in daily nursing workflows,
and (5) human-in-the-loop requirements for nursing AI tools — with
the public record, including:

- the [American Academy of Nursing position statement on AI in health care](https://aannet.org/page/AI-position-statement-2026) (board-approved February 2026) — human-in-the-loop oversight standards and AI as augmentation, never replacement, of nursing judgment;
- the [NLN Vision Series statement on AI in nursing education](https://www.nln.org/detail-pages/news/2025/09/17/nln-publishes-new-vision-statement-on-artificial-intelligence-(ai)-in-nursing-education) (September 2025) — national AI literacy standards and the foundational-to-advanced competency ladder;
- the AACN *Essentials* (2021) — informatics and healthcare technology as core competencies within competency-based education;
- the [NCSBN Clinical Judgment Measurement Model](https://www.nclex.com/clinical-judgment-measurement-model.page) — recognize cues, analyze cues, prioritize hypotheses, generate solutions, take actions, evaluate outcomes: the judgment spine any educational AI must load, not lift;
- the 2025–2026 cognitive-offloading literature — primary studies such as [Gerlich (2025), *AI Tools in Society: Impacts on Cognitive Offloading and the Future of Critical Thinking*, *Societies* 15(1):6](https://doi.org/10.3390/soc15010006) (see also [secondary commentary](https://www.epicpeople.org/future-of-critical-thinking/)), concentrated in higher-education and knowledge-work populations: unstructured reliance on generative AI is associated with weakened higher-order reasoning, with the youngest adult learners most vulnerable, while structured, reflective, guided use can strengthen critical thinking;
- [U.S. Department of Education guidance on responsible AI in learning](https://www.ed.gov/about/news/press-release/us-department-of-education-issues-guidance-artificial-intelligence-use-schools-proposes-additional-supplemental-priority) and the state AI-in-education legislative wave (tracked at [FutureEd's legislative tracker](https://www.future-ed.org/legislative-tracker-2026-state-ai-in-education-bills/)) — emerging AI-literacy requirements (general-education mandates in some jurisdictions, proposals in others), human-in-the-loop expectations, learner privacy protections, and jurisdiction-specific limits on AI-only grading and discipline;
- the ANA position statement on the ethical use of AI in nursing practice (2022).

## Relationship to Nurse AI OS

Several formation principles already have a tested reference
implementation in this repository's [Integration Contract](../naio-integrations/):

- the **judgment layer** delivers commit-then-compare probes, names the thinking frame in use, treats students as coach-first by default, and refuses consequential naked verdicts (`EDENA-JUDGMENT-VISIBILITY`);
- **student mode** blocks patient-specific recommendations and caps students at Draft (`EDENA-STUDENT-MODE`);
- the **healthcare sandbox** provides a practice field of patient-shaped synthetic data with no patients in it, behind a strict admission boundary;
- **data zones** keep private reflections out of faculty, manager, and cohort views (`EDENA-PRIVATE-REFLECTION`) and forbid silent zone migration (`EDENA-ZONE-MIGRATION`);
- every decision is traced to a tenant-separated, hash-chained, metadata-only audit stream.

That code is reference implementation evidence for the direction — it is not a curriculum, an approved program, or an operating education service. The doctrine's [embedding map](DOCTRINE.md#14-embedding-doctrine-nurse-ai-os) states plainly which planks are enforced today and which remain design intentions.

## Authority and precedence

These documents are subordinate to applicable law, professional duties, institutional and academic policy, the current NIN–NAIO Master Directive, repository governance, EDENA requirements, and artifact-specific licenses. Where a conflict exists, the more protective applicable authority controls. Nothing here substitutes for faculty, accreditors, boards of nursing, or institutional review.

## Licensing note

This doctrine and playbook are repository documentation and follow the documentation license stated in the root [README](../README.md). Future formation materials (courses, item banks, simulations, faculty guides) do **not** inherit one blanket license by association with this doctrine; each must carry an explicit artifact-specific license and rights record.
