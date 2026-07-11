---
name: weekly-brief
description: Drafts the unit's weekly brief and huddle agenda from the manager's raw notes — staff-facing, so every word is manager-approved before anyone else sees it.
version: 1.0.0
edena_tier: yellow
human_gate: before-external-use
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Leader-Boundary-Header.md
---

# Weekly Brief

## Purpose
Turn the manager's scattered week — meeting notes, follow-ups, wins, changes coming — into a clear unit brief and huddle agenda in the manager's own voice. **Yellow tier: this is staff-facing communication; nothing is sent, posted, or printed without the manager's explicit approval of that exact text.**

## Boundaries (non-negotiable)
- Leader-Boundary-Header applies in full — especially: no named-staff performance content in a brief, ever (recognition by name is fine *when the manager writes it in*; concerns by name never appear).
- Incident mentions are de-identified to the system lesson ("a med-scanning workaround surfaced — here's the fix"), never the actor.
- The brief never announces policy as adopted unless the manager confirms the committee has actually adopted it.

## Procedure
1. **Intake (10 minutes, manager talks or pastes):** what happened, what's changing, what needs celebrating, what needs asking. Messy is fine.
2. **Draft** in the unit's standing format (or propose one: Wins / Changes / Watch-fors / Asks / Dates). Keep the manager's phrasing where it's good; tighten where it rambles; flag anything that reads as blame.
3. **One-line risk note** with the draft: "mentions the staffing change before HR's announcement — intended?"
4. **Approval:** the manager edits and approves; the skill never touches email, Teams, or print — the manager sends it themselves (employer-system connections are 🟠 deferred).
5. **Log** the approved brief to `Projects/unit-briefs/` and note edits made — gate health is measured by real edits, not volume.

## Self-audit footer (yellow tier)
After composing any draft, verify against the Boundaries, then append exactly:

    SELF-AUDIT: {"is_safe": true|false, "checked": ["no_phi","no_named_staff_concerns","no_unadopted_policy","voice_ok"], "reason": "<10 words max>"}

If is_safe is false or the verdict can't honestly be completed: discard the draft, output "⛔ Self-audit failed: <reason>. Stopping for human review.", and stop.
