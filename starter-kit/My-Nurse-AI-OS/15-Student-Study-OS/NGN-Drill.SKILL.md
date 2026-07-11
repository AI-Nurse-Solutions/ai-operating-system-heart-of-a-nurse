---
name: ngn-drill
description: Generates Next Generation NCLEX–style practice items structured on the NCSBN clinical-judgment steps, with rationales revealed only after the student commits.
version: 1.0.0
edena_tier: green
human_gate: every-output
reversibility: reversible
no_phi: true
owner: <student name>
last_reviewed: 2026-07-11
requires: Academic-Integrity-Header.md
---

# NGN Drill

## Purpose
Practice items in the shape of the Next Generation NCLEX, exercising the six cognitive steps NCSBN's Clinical Judgment Measurement Model makes measurable: **recognize cues → analyze cues → prioritize hypotheses → generate solutions → take actions → evaluate outcomes**. This skill drills; it does not predict.

## Boundaries (non-negotiable)
- Academic-Integrity-Header applies. All patients are fictional — invented by this skill, never drawn from the student's placements.
- **Standing non-claim, said whenever scores are shown:** "These are practice signals, not a prediction of your NCLEX result, and not certification of anything."
- The NCJMM is NCSBN's *measurement* model for the exam; this skill uses its steps as practice structure, not as a claim of equivalence to the exam.

## Procedure
1. Ask for topic/system and item style: single-episode case, unfolding case, or mixed drill. Styles to rotate: matrix/grid, extended multiple response, cloze (drop-down), highlight-the-findings, bow-tie, trend.
2. Present a fictional client scenario with realistic data (vitals, labs, notes). One item at a time.
3. **Commit-then-reveal:** the student answers before any rationale appears. Then give the rationale for every option — why right is right and each wrong is wrong — naming which clinical-judgment step the item exercised.
4. Track per session and cumulatively in `Memory/study-analytics.md`: items by client-needs category, by clinical-judgment step, accuracy trend. Weakest area drives the next drill's weighting.
5. **Confidence, separately:** once per session ask "1–5, how confident do you feel about this area?" and log it apart from accuracy — the two move independently, and both matter.
6. End with a two-line Kardex: what was drilled, what to hit next.

## When the student misses repeatedly
Do not keep drilling. Switch to the Socratic-Tutor skill for the underlying concept, then return.
