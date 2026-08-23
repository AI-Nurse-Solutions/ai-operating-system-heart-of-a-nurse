---
title: "Three-Lane Operating Playbook"
status: "Proposed operating playbook"
version: "0.1"
date: "2026-08-23"
applicability: "Operating record. It describes how the work would be conducted if undertaken. It creates no product, cohort, program, partnership, pricing, institutional relationship, clinical validation, or authority to process PHI."
---

# Three-Lane Operating Playbook

## 1. Discovery runs in every cycle

Building one lane does not mean ignoring the other two. Discovery is continuous and parallel; only construction is serial.

**Per cycle, minimum:** eight interviews in the lane under construction, four in each of the other two archetypes, and two with cross-cutting roles ([SEGMENTS §5](SEGMENTS.md#5-cross-cutting-roles-that-are-not-lanes)). Direct-care nurses are included in every cycle regardless of which lane is building.

**The interview rule:** ask about the last time, not about the general case. "Walk me through the last governance packet you had to assemble" produces evidence. "Would you use a tool that helps with governance packets?" produces agreement, which is worthless.

**What is collected, every time:** the artifact they actually had to produce; how long it took; what got sent back and why; what they copied from last time; what they left out because there was no time; and who read it after them.

**What is watched for, and written down the same day:** what they corrected, what they ignored, what they overrode, what they refused, and what they did next.

## 2. Session conduct

Sessions are observed, not demonstrated. The founder's instinct to rescue a struggling user destroys the only data the session was for.

- The user drives. The observer takes notes and does not touch the keyboard.
- When the user gets stuck, wait. Note the duration. Intervene only after the user asks twice or the session would end in frustration.
- Never explain the architecture. If a user needs the ecosystem vocabulary to receive value, the onboarding has failed and that is the finding.
- End every session with two questions: *What would you do next with this?* and *What would you have done instead if this did not exist?*
- Ask for the second problem at the end of the **second** session, not the first — and then stop asking. A third ask converts a real signal into a favor.

## 3. Onboarding sequence

```text
One role
    ↓
One real professional goal
    ↓
One bounded finished artifact
```

Architecture is revealed only after the useful result. The first experience answers six questions and nothing else:

1. What do I receive?
2. Where does it run?
3. Is installation required?
4. What can I complete right now?
5. What information must I never enter here?
6. What is still emerging and not to be relied on?

Question 5 appears before the first input field, not in a policy page. Question 6 is answered honestly per feature rather than as a global disclaimer, because a global disclaimer is read as "nothing here works," which is both untrue and unhelpful.

**Vocabulary discipline.** NAIO, NIN, EDENA, Florence-X, Mission Control, SOUL, Kernel, Registry, and capability packs are internal architecture. A first-time user meets none of them. The user-facing surface names the artifact, the boundary, and the reviewer.

## 4. The refusal ritual

Refusals are a product surface, not an error state. Every refusal states three things:

1. **What was declined** — the specific content, not a category label.
2. **Why** — in the user's terms: "this names an identifiable staff member's performance," not "policy violation 7.3."
3. **The nearest permitted path** — a synthetic equivalent, a de-identified restatement, a citation-only route, or the named authorization that would be required and who grants it.

Refusals are logged with what the user did next. A refusal that users route around by rephrasing is not working, and the fix is in the workflow rather than in the wording.

## 5. Commit-then-compare

Applied in the Learner lane and, in a modified form, in the Manager lane.

The user commits to their own answer before the system offers one. In the Manager lane this means the user states the problem, the affected people, and the risks in their own words before any draft appears. The comparison that follows is the learning event, and the divergence is the most valuable thing in the session record.

This is also the honest defense against the product becoming an answer engine: a user who has committed can evaluate. A user who has not is only proofreading.

## 6. The packet review ritual

For the Manager lane, per packet:

1. **Pre-flight** — classify risk, data, and action independently before drafting. Run the Five Rights pre-flight before any Yellow recommendation.
2. **Draft** — sections rendered, unknowns marked as unknown.
3. **Human pass** — the user corrects; corrections are captured, not silently absorbed.
4. **Named reviewer** — a specific human, identified before submission, approving the exact artifact rather than the workflow.
5. **Disposition recorded** — accepted, returned, or escalated, with the reason.
6. **Case capture** — anything that went wrong becomes a stored evaluation case the same week.

Step 6 is the one that gets skipped under time pressure and the one that builds the only compounding asset. Treat a skipped case capture as a missed deliverable.

## 7. Incidents

An incident is any of: PHI entering the system; a refusal that should have fired and did not; an artifact that reached a reviewer with a fabricated claim, citation, or source; a capability pack distributed with an unresolved rights question; or any output that could be read as a clinical recommendation.

Response, in order: stop the workflow; preserve the session record; notify the affected user and any named reviewer who received the artifact; determine whether an artifact must be withdrawn from a live decision; write the case into the evaluation corpus; publish the change with a version. No incident is closed by explanation alone — it closes with a test that would have caught it.

## 8. Rights and sources

- Source and rights registers are maintained continuously, not reconstructed at release.
- Production language is original. Research reading and distributable artifacts are separated by procedure, not by intention.
- Licenses are obtained before any terminology mapping or standards integration, never after a mapping exists.
- Clean-room drafting where a restrictive source has been read by anyone on the team.
- Every distributable artifact carries a removal and rollback path.
- IP counsel is engaged before any commercial corpus, ontology, or standards release.

## 9. Community participation

A community is a moat only when members change the product. Participation that cannot change anything is an audience.

- Reviewers are compensated. Unpaid nurse labor to legitimize a commercial product is not community participation.
- Direct-care representation is required, not optional, and is not satisfied by leaders who used to be at the bedside.
- Patient, family, disability, language-access, and cultural-safety representation is included where the work affects them.
- Disagreement is documented and published, including disagreement that was not adopted.
- Version history is public.
- No "ratified" designation until the governance conditions in [IMPLEMENTATION](IMPLEMENTATION.md#what-runs-across-all-three-cycles) are met.

## 10. Cadence

**Weekly:** session notes written the same day; corrections and refusals reviewed; evaluation cases captured.

**Monthly:** unassisted checks for active learners; evaluation suite run against the current model; regressions triaged before feature work.

**Per cycle:** gate review against [EVIDENCE §3](EVIDENCE.md#3-the-cycle-gates), decided against the stated conditions rather than against momentum; falsifiers checked explicitly; the next lane started, the current one repeated, or the plan re-opened.

**On any model change:** the evaluation suite runs before the change ships. A model change that breaks a previously safe workflow is a release blocker, and no silent fallback to a less-governed model is permitted.

## 11. The discipline this playbook exists to enforce

> **Three lanes of listening. One lane of building. One artifact at a time, in front of the person who has to accept it.**
