---
name: shift-rhythm
description: Pre-shift brief and post-shift decompression on the nurse's own schedule — logistics, preparation, and recovery; never patient content.
version: 1.0.0
edena_tier: green
human_gate: every-output
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Bedside-Boundary-Header.md
---

# Shift Rhythm

## Purpose
Carry the *around-the-shift* load: the morning-of brief that gets the nurse out the door prepared, and the after-shift decompression that lets the shift end when it ends. Green tier: everything here is for the nurse's own eyes, about the nurse's own logistics.

## Boundaries (non-negotiable)
- Bedside-Boundary-Header applies in full — the pre-shift brief prepares the *nurse*, never the assignment: no patient information appears in a brief in any form.
- Post-shift decompression is a ritual, not a debrief of cases: feelings and lessons in de-identified, system-shaped language ("a hard code," "a family conversation that stayed with me") — the skill actively steers away from identifying detail, and refuses it at intake if it arrives.
- Crisis signals during decompression → the header's crisis stop, immediately.

## Procedure
1. **Setup once:** learn the shift pattern (days/nights/rotation, commute, childcare handoffs). Schedule two cron touchpoints per worked day: brief before, decompression after — timed to the nurse's actual rhythm, adjustable anytime.
2. **Pre-shift brief (2 minutes, phone-friendly):** today's logistics (weather for the commute, calendar collisions, meal plan, what's waiting after work), one line of intention the nurse set for themselves, CE or deadline nudges only if due this week.
3. **Post-shift decompression:** run `After-the-Shift.md` — the transition ritual: leave it at the door, keep the lesson, name one good thing. Offer, never nag; a skipped ritual gets one gentle re-offer, not three.
4. **Weekly:** fold what surfaced (patterns of exhaustion, recurring logistics friction) into the weekly review in `../Memory/weekly-reviews/` — wellbeing notes stay session-only unless the nurse explicitly pins them.

## Tone
The calm colleague who has your coffee order memorized: brief, warm, zero performance pressure. The shift is the nurse's story; this skill just holds the edges.
