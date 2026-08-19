# Care Workforce Surge

> **Status: proposed workforce doctrine, strategy, implementation plan, and playbook, version 0.1 (2026-08-19).** These documents specify a direction and a set of boundaries. They do not establish a product, curriculum, training program, competency framework, credential, pilot, partnership, institutional authorization, clinical validation, employment process, or permission to process PHI.

Healthcare is entering a decade in which caregiving absorbs more new jobs than any other occupation in the economy — and loses nearly as many workers as it gains. This directory works out what that means for Nurse AI OS, starting from evidence rather than from the assumption.

## The finding

The projection under review was that healthcare will face an influx of workers transitioning into caregiving, and that a Nurse AI OS will be critical infrastructure to upskill, manage, and coordinate them.

The evidence supports the flow and corrects its shape:

> Healthcare is not receiving a wave of new caregivers who stay. It is settling into a **permanent high-volume, low-tenure workforce** — roughly 9.7 million projected direct-care openings over 2024–2034, sustained by turnover near 75 percent in home care, met by a shrinking pool of experienced nurses, 39.9 percent of whom intend to leave or retire within five years.
>
> **The binding constraint is not labor supply. It is supervisory capacity per experienced nurse.**

That changes what the software is for. A system built to add capacity competes with a wage problem and loses. A system built to **multiply supervision** addresses the actual bottleneck.

And it constrains how the co-pilot may work. The strongest evidence for novice-first design — AI assistance helps less-experienced workers most — sits directly alongside evidence that the naive implementation fails: models scoring 94.9 percent alone delivered under 34.5 percent through untrained users, no better than no assistance at all. So the novice-facing product is **not an answer engine**. It orients, holds scope, makes the user commit before it compares, and routes to a human fast.

## Documents

- **[Validation Record](VALIDATION.md)** — the three claims graded separately, the evidence with sources, the restated projection, and the falsifiers stated in advance.
- **[Doctrine](DOCTRINE.md)** — thirteen principles, the populations served, the refusal catalog, and what this work refuses to become.
- **[Strategy](STRATEGY.md)** — the supervision-multiplier position, the wedge, the person → dyad → unit → institution sequence, the landscape, and the stop conditions.
- **[Implementation Plan](IMPLEMENTATION.md)** — five phases, each with artifacts, non-goals, an evidence gate, and stop conditions.
- **[Operational Playbook](PLAYBOOK.md)** — the Ask Ladder, Day One, commit-then-compare, the preceptor ritual, the unassisted check, incidents, localization, and metric definitions.

Public summary page: [`index.html`](index.html) — published at <https://nurse-ai-os.org/care-workforce-surge/>.

## Governing maxims

> **Supervision is the scarce resource. Multiply it; never simulate it.**

> **The system is never the last thing between a worker and a patient.**

> **Novice-first does not mean answer-first. Orient, commit, compare, escalate.**

> **If a deployment coincides with less supervision, the deployment is out of doctrine.**

## Relationship to the rest of Nurse AI OS

This is **not** a post-setup role lane, a build kit, or a download. It is a design record that governs future surge work, and it inherits from documents that already exist:

- [**EDENA**](../governance-kit/) supplies the risk, data, and action dimensions. The whole plan sits at the personal-edition ceiling: Yellow risk, D1 data, Recommend action.
- [**Nurse Formation**](../nurse-formation/) supplies the learning method — commit-then-compare, human evaluative authority, AI never grading alone, and never gating a career.
- [**Knowledge Commons**](../knowledge-commons/) supplies the distribution contract: versioned, reviewed, provenance-bearing Knowledge Packs, and evaluation bundles as first-class assets.
- **SOUL** personalizes by role, setting, language, and tenure, and may never raise scope or unlock a refusal.
- **Hermes** is the local runtime; it proposes and retrieves, and authorizes nothing.

## What is deliberately absent

No competency scoring. No credential gating. No staffing-optimization or labor-savings claim. No clinical decision support for unlicensed workers. No productivity monitoring of the lowest-paid workers in healthcare. No system that presents, or could be mistaken for, a nurse — which is doctrine here and law in a growing number of states.

## Licensing

These are repository documentation and follow the documentation license stated in the root [README](../README.md).
