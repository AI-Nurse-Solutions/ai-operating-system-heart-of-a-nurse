# Vault Structure — sphere-scoped memory

Your starter kit already has a `Memory/` folder (KARDEX, weekly reviews, decisions). This layout doesn't replace it — it gives it spheres, so what your AI remembers about you stays sorted by which part of your life it belongs to, and never silently crosses over.

## The layout

Create these inside `Memory/`:

```text
Memory/
  KARDEX.md                  ← unchanged: your five-line session handoffs
  weekly-reviews/            ← unchanged
  decisions/                 ← unchanged
  spheres/
    personal/                ← own health, family logistics, home, finances, rest
    interest/                ← hobbies, creative projects
    professional/            ← shift patterns, certifications, career map, study
    community/               ← advocacy, teaching, side-gig work
  TRUST-LEDGER.md            ← from this kit
```

Each sphere folder holds plain markdown notes: preferences, routines, running context, things you've told your AI to keep. One topic per file, named plainly (`shift-recovery-routine.md`, `ccrn-study-pacing.md`, `family-calendar-rhythms.md`).

## The three rules of sphere memory

1. **Notes carry their sphere.** A note lives in exactly one sphere folder. If you can't decide which, it's probably two notes.
2. **Spheres don't leak upward.** Professional notes may reference your personal rhythms ("no study blocks after night shifts") but personal details don't get copied into files an employer, colleague, or community could ever plausibly see.
3. **The clinical sphere does not exist here.** There is no `spheres/clinical/` and there never will be in a personal vault. A "passing observation about a patient's comfort" is clinical memory — it belongs in the chart, in report, or nowhere. Writing it here feels harmless and is exactly how PHI leaks start.

## What your AI does with this

When a session starts, your AI reads `SOUL.md`, the KARDEX, and only the sphere folders relevant to the task at hand. Before any handoff run, it must also resolve the named handoff card and the current state of `Memory/TRUST-LEDGER.md` — the card's mode as promoted or narrowed, and any revocation. If the card or the ledger is missing, ambiguous, or contradictory, the AI does nothing and asks; a handoff never runs on an assumed mode. When it learns something worth keeping, it proposes the note and the sphere — you approve the write. Point your AI at this file once so it knows the rules; after that, hold it to them.

## What never goes in any sphere

The `00-Start-Here/DO-NOT-REMEMBER.md` list, in full: patient information of any kind, employer-confidential material, credentials and keys, other people's private information, and anything you wouldn't want resurfacing in six months. When in doubt, don't write it down — say it out loud to a colleague instead. That's what colleagues are for.
