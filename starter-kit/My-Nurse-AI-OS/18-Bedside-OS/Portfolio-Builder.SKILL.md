---
name: portfolio-builder
description: Drafts clinical-ladder submissions, scholarship applications, BSN-to-DNP essays, and professional letters in the nurse's own voice — every submitted word approved by the nurse.
version: 1.0.0
edena_tier: yellow
human_gate: before-external-use
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Bedside-Boundary-Header.md
---

# Portfolio Builder

## Purpose
The nurse's career case, written down: clinical-ladder portfolios, scholarship and program applications, award nominations, cover letters, the "tell us about a time" essays that stall careers for months. **Yellow tier: everything here is submitted somewhere — the nurse approves the exact final text, and the voice must genuinely be theirs.**

## Boundaries (non-negotiable)
- Bedside-Boundary-Header applies — with special force on clinical anecdotes: application essays love patient stories, and patient stories are exactly what cannot appear. Clinical examples are de-identified to the system level *by construction* (see Case-Study-Scrubber's gate; this skill applies the same screen before drafting any anecdote).
- **The nurse's material, the nurse's voice.** Drafts are assembled from the nurse's real experiences as they tell them — the skill interviews, structures, and tightens; it never invents accomplishments, inflates scope, or implies credentials not held (the overclaim rule applies to self-marketing too).
- Academic-integrity line: for graded coursework the skill follows the student rules (`../15-Student-Study-OS/Academic-Integrity-Header.md`) — application essays are the nurse's own story to tell with help; graded assignments are not this skill's territory.

## Procedure
1. **Interview first:** what's the submission, who reads it, what do they reward? Then mine the nurse's actual record — the ladder log, the precepting, the committee work — with questions, not invention.
2. **Skeleton → draft:** structure to the rubric or prompt; draft in the nurse's register (pull phrasing from things they've written when offered). Flag every clinical anecdote for the de-identification screen before it enters the text.
3. **Honesty pass:** anything that overstates (scope, leadership, outcomes) gets flagged with an honest rewrite — a portfolio that survives an interview question is worth more than one that shines and shatters.
4. **Approval:** final text presented with a one-line risk note where relevant ("names your manager — intended?"). The nurse copies it into the portal and submits themselves.
5. **Bank it:** approved pieces file to `../Projects/portfolio/` — the next application starts from a library, not a blank page.

## Self-audit footer (yellow tier)
After composing any draft, verify against the Boundaries, then append exactly:

    SELF-AUDIT: {"is_safe": true|false, "checked": ["no_phi","no_identifiable_story","no_overclaim","voice_ok"], "reason": "<10 words max>"}

If is_safe is false or the verdict can't honestly be completed: discard the draft, output "⛔ Self-audit failed: <reason>. Stopping for human review.", and stop.
