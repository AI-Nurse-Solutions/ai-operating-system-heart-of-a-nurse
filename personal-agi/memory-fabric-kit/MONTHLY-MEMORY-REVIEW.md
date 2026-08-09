# Monthly Memory Review

Once a month, you audit what your AI remembers about you. This is the ritual that keeps a personal memory fabric *yours* — inspected, corrected, and prunable — instead of a drift of half-true notes you no longer control. Twenty minutes. Put it on the calendar; pair it with a weekly review you already do.

## The review, in order

### 1. What did my AI learn about me this month?

Ask your AI directly: *"List every memory note you added or changed this month, by sphere, with one line each."* Read the list. For each item: keep, correct, or delete. Correcting is normal — a memory fabric that never needs correcting is one you're not reading.

### 2. What should be forgotten?

Some notes age out (a resolved family logistics thread, a finished course). Delete them. Forgetting on purpose is a feature: it keeps retrieval sharp and keeps old context from steering new decisions. If a note keeps resurfacing unhelpfully, that's your cue.

### 3. Is anything in the wrong sphere?

Skim the sphere folders. Personal details drifting into `professional/` or `community/` notes is the quiet failure mode — fix placements now, while the drift is one note and not a habit.

### 4. The PHI-leak self-audit

This is the non-negotiable section. Even careful nurses leak by accident — a debrief note after a hard shift is how it usually happens.

**Do this section offline, by hand — with your AI closed.** Use your text editor's or file manager's *local* search only, with any cloud, AI, or "smart search" features off. Never type a patient name, room number, or MRN into an AI chat, a connected search box, or anything that syncs or retains history — searching that way *is* the exposure this audit exists to catch. (Steps 1–3 above talk to your AI; this step never does.) If you use a terminal instead, use a search that doesn't leave the terms in your shell history. Review any match with your own eyes before deleting or recording anything.

- [ ] Local-search the whole vault (not just `Memory/`) for patient names you can think of from this month. Any hit: delete the content, then note the miss below.
- [ ] Local-search for room/bed numbers, MRN-shaped numbers, and dates paired with clinical events ("the code on the 14th").
- [ ] Skim every note created after a hard shift. Venting is healthy; venting *into the vault* with identifying detail is a leak.
- [ ] Check where the vault actually lives: what syncs it, what backs it up, what device it's on. Still all yours? Still off employer hardware?
- [ ] Re-read one handoff card's evidence log and confirm nothing patient-adjacent rode along in a "helpful" summary.

**Any hit — contain, then record:**

1. Stop the related card or memory habit now: a written `NARROWED` or `REVOKED` entry per TRUST-LEDGER.md.
2. Delete the content locally — then hunt the copies: sync targets, backups, exports, evidence logs, and any AI conversation where the note's content appeared (delete those conversations and any stored AI memory of them).
3. Record the miss below and in the ledger as non-sensitive metadata only — what kind of detail, where it was found, what was cleaned — never the detail itself.
4. If the content ever reached a hosted or connected AI, treat it by the incident posture of [`SAFETY.md`](../../SAFETY.md) §4: report through the applicable channel without repeating the PHI.

One leak is a lesson; an unrecorded leak is a pattern waiting.

### 5. Attest and log

Append one block per review to the bottom of this file:

```text
REVIEW: 2026-09-01
Notes kept/corrected/deleted: 14 / 3 / 5
Sphere misplacements fixed: 1
PHI self-audit: CLEAN | MISS (see ledger, card narrowed)
Ledger reviewed: Y — promotions/demotions handled in TRUST-LEDGER.md
One thing my AI now understands better about me: ...
```

## Review log

```text
(your entries accumulate here)
```
