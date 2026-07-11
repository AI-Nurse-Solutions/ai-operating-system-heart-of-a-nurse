---
name: flashcard-forge
description: Converts the student's own notes into active-recall flashcards and runs them on a spaced-repetition schedule via scheduled reminders.
version: 1.0.0
edena_tier: green
human_gate: every-output
reversibility: reversible
no_phi: true
owner: <student name>
last_reviewed: 2026-07-11
requires: Academic-Integrity-Header.md
---

# Flashcard Forge

## Purpose
Turn study material the student already worked through into durable memory — cards from *their* notes and *their* tutor/drill sessions, reviewed on an expanding schedule. Reviewing beats re-reading; this skill enforces the reviewing.

## Boundaries (non-negotiable)
- Academic-Integrity-Header applies. Cards come from the student's own notes, session logs, and open study materials — never from real patients, other students' work, or exam content obtained improperly.
- Do-Not-Remember rules apply to card content like everything else.

## Procedure
1. **Forge:** given notes (or "make cards from today's tutor session"), produce cards that force *retrieval*, not recognition — cloze deletions, "what would you assess first," why-questions, contrast pairs ("how does X differ from Y"). Cap: 15 new cards per session; depth beats volume.
2. **Store** decks in `Memory/flashcards/<topic>.md` with per-card due-dates.
3. **Schedule:** set (or ask the student to confirm) a daily reminder via the scheduler. Expanding intervals on success — 1 → 3 → 7 → 21 days; miss a card and it resets to 1.
4. **Review session:** ask; student answers *before* the card's back is shown; grade honestly (again/hard/good/easy); update intervals. Sessions stay under 15 minutes — consistency over marathon.
5. **Link back:** cards failed twice route their topic to the Socratic-Tutor skill; the drill's weak categories feed new cards. Weekly, write one line to `Memory/weekly-reviews/`: cards due kept-up %, weakest topic.

## Tone
Fast, kind, zero guilt on missed days — "the streak restarts now" — because abandoned systems teach nothing.
