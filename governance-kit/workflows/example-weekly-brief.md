# Workflow: Monday morning brief

<!-- EXAMPLE — a Green workflow running near its ceiling. Low risk, high value,
     mostly automated. This is what "boring and compounding" looks like. -->

```
Tier:                    Green
Claim type:              None
Evidence requirement:    None (owner's own notes and lists only)
PHI status:              No PHI allowed
Patient-specific:        No
Human review required:   No (Green; owner reads the brief itself)
Nurse-governed review:   No
External-facing:         No
Ledger entry required:   No (weekly summary entry only)
Automation ceiling:      L4
Escalation owner:        [owner's name]
```

## Purpose

A brief the owner can read in the elevator: what matters this week, what's due, what's stuck, and one question worth deciding today.

## Steps

| # | Step | Who | Level |
|---|------|-----|-------|
| 1 | Trigger: first session of the week | — | — |
| 2 | Review task list, calendar notes, and last week's brief | AI | L1 |
| 3 | Draft the brief in SBAR shape: Situation (this week), Background (carried over), Assessment (what's at risk of slipping), Recommendation (top three, in order) | AI | L2 |
| 4 | Update task list and reminders to match | AI | L4 |
| 5 | Owner reads; reorders if the AI's priorities are wrong | Human | — |
| 6 | If the owner reorders two weeks running: flag the pattern for the improvement loop | AI | L3 |

## Escalation triggers for this workflow

- Anything in the notes that looks Yellow or Red (a named person, an external commitment) → pull it out of the brief and flag it separately.

## Last reviewed

2026-07-03 — Initial version. Leads with deadlines (see ledger 2026-07-03).
