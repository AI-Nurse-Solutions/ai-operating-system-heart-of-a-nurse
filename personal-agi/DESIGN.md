---
title: "Personal AGI for Nursing Roles — Sphere-First Design Doctrine"
status: "Proposed design doctrine"
version: "0.1"
applicability: "Design record; no operational capability, hardware program, EHR integration, or institutional authority is created by publication"
---

# Personal AGI for Nursing Roles — Sphere-First Design Doctrine

## 1. Purpose

This document records how Nurse AI OS can become a personal AGI — a persistent, personalized, agentic companion — for different nursing roles, starting from the personal sphere. It responds to an external signal: Hark-style personal AI built on multi-modal hands-free hardware, "Handoff" agentic computer use, persistent personalized memory, and proactive reasoning. The distilled signal record is [`signals/2026-08-09-hark-personal-agi.json`](signals/2026-08-09-hark-personal-agi.json).

It answers one sequencing question honestly: **which of these capabilities is the critical first step for a frontline healthcare initiative?**

## 2. The verdict, stated plainly

The critical first step is **not** the two headline capabilities.

- Ambient multi-modal hardware at the bedside captures PHI and third-party audio without an existing consent framework. It is a horizon design, not a first step.
- "Handoff" EHR navigation is machine-to-EHR action. Even fully gated, it requires institutional authorization, vendor terms-of-service review, and audit infrastructure that no personal deployment can self-confer. It is a deferred design.

The critical first step is **personalized persistent memory, built in the personal sphere** — with the handoff (agentic computer use) muscle practiced there first, on screen work that contains no PHI and touches no institutional system.

Four reasons:

1. **It is the substrate.** Handoff without personal memory is generic screen automation; proactive reasoning without memory is generic alerting. Every other capability in the signal presumes an AI that already knows this nurse — routines, shorthand, priorities, spheres, season of life. Memory is what "thinks like you" is made of.
2. **It is the only capability buildable now inside standing boundaries.** The no-PHI boundary, EDENA data classes, and the anti-surveillance doctrine already permit a D0/D1, Green/Yellow personal memory fabric. Nothing must be weakened to begin.
3. **It is where trust is earned before it is spent.** A nurse who has watched their own agent prepare, stage, and correctly complete a hundred gated personal-sphere handoffs has an evidence base — a trust ledger — for any future conversation about clinical surfaces. A nurse handed an EHR agent on day one has only a vendor's word.
4. **It matches how this project already sequences.** SOUL files, the Life & Projects Quiz (3 spheres, 17 domains), the local-first dashboard, and the post-setup role lanes all begin with the nurse's own life and grow outward. The personal AGI is the same ladder, climbed with an agent.

> Carry the lamp. Keep the ledger. Hermes supports. Humans judge. Nurses steward.

## 3. Mapping the four capabilities onto NAIO

| Hark-style capability | NAIO translation | EDENA posture today | Where it starts |
|---|---|---|---|
| Persistent personalized memory | Sphere-scoped memory fabric: SOUL + life-domain map + local-first vault the nurse owns, inspects, exports, deletes | D0/D1, Green/Yellow — buildable now under a hard no-PHI invariant | **Personal sphere, now — the first step** |
| "Handoff" agentic computer use | Delegated screen-work agent under the action-mode ladder | Personal/non-clinical: Green/Yellow, buildable now. EHR-facing: Orange, deferred | Personal sphere now; EHR never by personal progression |
| Proactive and predictive reasoning | Anticipatory briefs from personal memory (pre-shift setup, renewal reminders, study pacing). Clinical physiological monitoring is a separate, likely regulated device function | Personal anticipation: Green. Clinical monitoring: Orange/Red-E, outside this design | Personal-sphere proactivity now |
| Ambient multi-modal hardware | Perception-locality wearable (an edge-node concept) | Recording in patient areas: refused by default; consent, institutional authority, and on-device processing are unproven preconditions | Horizon; not in scope |

## 4. The Sphere Ladder

The personal AGI grows through spheres, in order, and each promotion is a human decision recorded in the trust ledger — never an automatic graduation on performance.

```text
1. Personal sphere        — own health, family logistics, home, finances, rest & renewal
2. Interest sphere        — hobbies, creative projects
3. Professional sphere    — shift organization, learning & certification, career map,
   (non-clinical)           evidence reading, precepting prep — never patient data
4. Community sphere       — advocacy, public education, side-gig work
                            (publication gated by per-artifact human approval)
──────────── hard governance break ────────────
5. Institutional-clinical — EHR, devices, patient-specific work: reachable only through
                            separately provisioned institutional governance (SAFETY.md),
                            never through personal progression
```

The break above rung 5 is the load-bearing design decision. A personal AGI that could carry itself into the clinical sphere by being good at the personal one would convert every consumer capability gain into an ungoverned clinical capability gain. The ladder therefore ends, by design, at the community sphere; the clinical sphere has its own door, its own keys, and its own keyholders.

## 5. One spine, many role editions

The personal AGI is one memory-and-handoff spine personalized per role by SOUL files and the existing role lanes — not a separate product per role.

| Role | Existing lane | Personal-sphere memory emphasis | First handoff catalog (examples) |
|---|---|---|---|
| Student nurse / assistant | FUTURE | study pacing, exam calendar, clinical-rotation logistics (no patient data) | Socratic study sessions staged from the reading list; CEU/assignment tracker updates; scholarship application prep |
| Staff nurse | SHIFT | shift pattern, recovery routine, certification renewals, commute/childcare logistics | pre-shift setup brief; schedule-swap request drafts; personal inbox triage; renewal paperwork staging |
| Nurse practitioner (USA) | WINGS | licensure/DEA renewal calendar, CME ledger, panel-agnostic reading queue | CME evidence file assembly; renewal form staging; conference travel planning |
| Leader / manager | LEAD | meeting cadence, decision journal, program milestones | huddle agenda drafts; decision-record filing; recurring report skeletons from prior structure |
| Educator | TEACH | course calendar, content pipeline, learner-facing material versions | lesson scaffold staging; slide/handout revision passes; workshop logistics |

Adjacent lanes (ROUNDS, BREATHE, DISCOVER, STEWARD, THRIVE) inherit the same spine in their own isolated namespaces.

In every row, the pattern is identical: the memory fabric makes the agent *this nurse's* agent; the handoff catalog is bounded, no-PHI, and gated; and what accrues is a role-specific trust ledger.

## 6. Memory doctrine

*Sections 6 and 7 have a runnable v0.1 implementation: the [Personal Memory Fabric Kit](memory-fabric-kit/).*

- **Sphere-scoped namespaces.** Memory writes are tagged by sphere and may not silently cross spheres or rise in data class.
- **Local-first ownership.** The fabric is files and a local index the nurse can read, export, and delete. Hosted sync is opt-in and never a condition of use.
- **The no-PHI invariant.** No patient name, identifier, or reconstructable patient narrative enters memory — including the Hark scenario of "recalling a passing observation about a patient's comfort from hours ago." That capability is real and valuable, and it is *clinical memory*: it belongs behind the governance break, inside institutional systems, or nowhere. The personal fabric remembers the nurse's life, not the patient's.
- **Anti-surveillance.** The fabric must never feed employer analytics, competency scoring, cohort ranking, or discipline. On employer-owned devices, the fabric does not install.
- **Inspection as a habit.** A monthly memory review (what was learned about me, what should be corrected, what should be forgotten) is part of the operating rhythm, with a PHI-leak self-audit included.

## 7. Handoff doctrine

- **Action-mode ladder.** Observe → Draft → Recommend → Prepare Action → Act With Approval. Constrained Autonomy is unavailable in v0.1; unrestricted autonomy is prohibited everywhere.
- **Handoff cards.** Every delegated task class is registered with scope, credentials touched, permitted mode, stop conditions, and where its evidence log lives — with one-touch revoke.
- **Draft-and-attest.** The agent gathers, prepares, and stages; the human reviews and commits. This is the interaction standard the OS would later demand of any clinical agent, so it is practiced from day one where the stakes are groceries and CEUs, not orders and charts.
- **Complacency is the tracked failure mode.** Approval-without-review rate is the metric that decides whether a handoff class keeps its action mode.

## 8. Deferred designs and their preconditions

Recorded so ambition has an honest shape; none of these are activated by this document.

1. **EHR handoff agent.** Requires: named institutional authorization; EHR vendor terms and security review; per-action human validation gates; a draft/file write boundary; complete audit trails; incident and rollback pathways; and Florence X-class registry, monitoring, and kill-switch infrastructure.
2. **Ambient multi-modal wearable.** Requires: consent and disclosure frameworks accepted by institutional counsel; on-device processing with no raw audio/video retention as a design precondition; staff and patient opt-out that actually works; and a regulatory determination for any clinical inference it performs.
3. **Proactive clinical monitoring.** Predicting deterioration from vitals and labs with "prepared protocols" is likely software-as-a-medical-device. It enters through a regulatory and institutional pathway or not at all — never as a feature flag on the personal companion.

## 9. What success looks like

The personal AGI is succeeding when a nurse can say: *my system knows my life, carries my screen burden in my own spheres, briefs me before I ask, and has never once touched a patient's data or acted without my hand on the gate* — and when the ledger behind that sentence is inspectable. It is not succeeding merely because it is more autonomous, more ambient, or more predictive.

## 10. Amendment

Material changes — any PHI-adjacent memory, any EHR-facing handoff, any perception hardware, any Constrained Autonomy — touch the safety posture of `SAFETY.md` and are therefore substantial changes under [`GOVERNANCE.md`](../GOVERNANCE.md) §3: a proposal issue, an open comment period, and a steward decision recorded with published rationale, where the default answer is no. Founder judgment is exercised through that recorded process, not in place of it. AI may draft amendments; it may not ratify them.

---

*Agents propose. Humans judge. Nurses steward.*
