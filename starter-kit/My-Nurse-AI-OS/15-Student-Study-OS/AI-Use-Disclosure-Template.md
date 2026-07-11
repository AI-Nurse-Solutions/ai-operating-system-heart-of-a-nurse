---
name: ai-use-disclosure
description: Generates an honest, specific disclosure block a student can attach to submitted work, built from the process log.
version: 1.0.0
edena_tier: yellow
human_gate: before-external-use
reversibility: reversible
no_phi: true
owner: <student name>
last_reviewed: 2026-07-11
requires: Academic-Integrity-Header.md
---

# AI-Use Disclosure Template

## Purpose
Make honest disclosure the easy default. Detection tools are unreliable and their false positives hurt honest students; a specific, dated disclosure — backed by a process log — is stronger protection than any detector score. **Yellow tier: the student reviews and approves the disclosure before anything is submitted, and their program's own AI policy always wins over this template.**

## The template

> **AI-use disclosure.** In preparing this work I used an AI study assistant (Nurse AI OS on the Hermes runtime) as follows:
> - **Used for:** [e.g., Socratic tutoring on <topic> (dates), practice questions with rationales, feedback on an outline I wrote]
> - **Not used for:** composing the submitted text; generating references; [anything else the assignment prohibits]
> - **All submitted writing, reasoning, and conclusions are my own.** A dated process log of my AI study sessions is available on request.
> - Course AI policy consulted: [yes — policy name/date].

## Procedure
1. When the student asks (or when any Study OS session touches an assignment), offer to draft the disclosure from the process log — filled with real dates and activities, nothing generic.
2. Show the draft and the relevant process-log lines side by side; the student edits and approves. Never auto-attach.
3. If the AI was used in a way the course prohibits, say so plainly and help the student decide honestly what to do — the template is never a fig leaf.

## Self-audit footer (yellow tier)
After composing a disclosure, verify: specific (dates/activities) not generic · claims match the process log · nothing overstated or understated. Then append:

    SELF-AUDIT: {"is_safe": true|false, "checked": ["matches_log","specific","policy_noted"], "reason": "<10 words max>"}

If is_safe is false or the verdict can't honestly be completed: discard, output "⛔ Self-audit failed: <reason>. Stopping for human review.", and stop.
