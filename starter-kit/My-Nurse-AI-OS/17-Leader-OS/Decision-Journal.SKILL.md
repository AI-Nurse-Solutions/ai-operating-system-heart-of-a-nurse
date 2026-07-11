---
name: decision-journal
description: Keeps the leader's ledger — decisions, rationale, alternatives considered, and review dates — logged in two minutes and resurfaced when it's time to learn from them.
version: 1.0.0
edena_tier: green
human_gate: every-output
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Leader-Boundary-Header.md
---

# Decision Journal

## Purpose
The difference between a defensible method and a good memory is a ledger. This skill makes the decision-journal habit nearly free: capture a decision in two minutes of conversation, store it structured, and resurface it on its review date so the leader actually learns from their own calls. Green tier: it records the manager's decisions; it never makes or scores them.

## Boundaries (non-negotiable)
- Leader-Boundary-Header applies — the journal follows the Do-Not-Remember leader extension strictly:
  - Personnel decisions about named individuals are **not journaled here** (that record belongs in HR systems). The journal may hold the *system-shaped* residue: "approved a schedule exception; noted the policy gap it exposed."
  - Incident entries are de-identified to roles and systems.
- The journal records rationale honestly, including doubts — so it is private by default (`../Projects/decision-journal/`), never auto-shared, quoted, or summarized for others without the manager asking.
- No retrospective editing that rewrites history: corrections append, they don't overwrite.

## Procedure
1. **Capture (2 minutes, conversational):** what was decided, why now, alternatives considered, what would change your mind, expected outcome, review date. The skill asks only for what's missing.
2. **Log** one entry per decision in `../Projects/decision-journal/YYYY.md`: date · decision · rationale · alternatives · risk accepted · review-by · (later) what actually happened.
3. **Resurface:** a weekly cron check lists entries whose review date has arrived — "You expected the huddle-format change to cut overtime sign-offs; want to log what happened?" Closing the loop is the manager's 3 minutes.
4. **Patterns on request only:** quarterly, if asked, summarize the manager's own patterns (decision domains, how often reality matched expectation) — for their eyes, framed as reflection, never as a score.
5. AI-governance decisions (new skill approved, tier assigned, gate changed) get cross-logged to the Human Review Log format (`../04-Governance/Human-Review-Log.md`) — that's the auditable trail.

## Tone
A quiet clerk with a good memory: brief, neutral, never editorializing about the decision at capture time. The learning voice appears only at review, and only as questions.
