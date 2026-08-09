# Handoff Card — Pre-Shift Setup Brief

The gentlest first card. Before a shift, your AI assembles a one-page brief about *your* day — never the unit's, never a patient's.

| Field | Value |
|---|---|
| **Sphere** | professional (non-clinical) |
| **Action mode** | Draft |
| **Data class** | D1 |
| **What the AI does** | Reads your calendar, `Memory/spheres/professional/` (shift pattern, commute, prep routine) and `personal/` (sleep, family logistics for the day), then drafts one page: shift time and commute plan, what to prep tonight vs. tomorrow, personal logistics that collide with the shift, one line on recovery after. Saves it as a draft for you to read with coffee. |
| **What the AI never does** | Touch anything about the unit, census, acuity, assignments, colleagues, or patients. Never messages anyone. Never reschedules anything. |
| **Accounts/credentials touched** | Personal calendar (read-only). Nothing else. |
| **Stop conditions** | Universal list, plus: calendar shows an event it can't classify → it asks instead of guessing. |
| **Evidence log** | `Memory/spheres/professional/pre-shift-briefs/` — one file per brief. |
| **Revoke** | Delete this card from your vault; tell your AI the card is revoked. Done. |

## Why this card first

It runs often (every shift), its failures are cheap (a wrong commute note), and it exercises the whole loop — memory read, draft, your review, ledger entry — daily. Two clean weeks here teach you more about supervising an agent than any document can.

## Prompt seed

> Using my SOUL file, my calendar for tomorrow, and my professional and personal sphere notes, draft my pre-shift setup brief per handoff card 01. Draft only — I review at [time]. Halt and hand back on anything patient-adjacent or unclear.
