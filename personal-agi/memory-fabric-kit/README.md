# Personal Memory Fabric Kit — v0.1

This kit turns the [Sphere-First Design Doctrine](../DESIGN.md) (sections 6–7) into files a nurse can actually run. It gives your Nurse AI OS the first layer of a personal AGI: a memory fabric that knows *your* life — never a patient's — and a gated way to hand off your own screen work.

Downloading or copying this kit does not install anything, activate any agent, or authorize any institutional use.

## What's inside

```text
memory-fabric-kit/
  README.md                  ← you are here
  VAULT-STRUCTURE.md         ← sphere-scoped memory layout for your vault
  TRUST-LEDGER.md            ← the record that earns (or revokes) agent trust
  MONTHLY-MEMORY-REVIEW.md   ← the review ritual, with the PHI-leak self-audit
  handoff-cards/
    HANDOFF-CARD-TEMPLATE.md
    01-Pre-Shift-Setup-Brief.md
    02-CEU-Renewal-Tracker.md
    03-Schedule-Swap-Draft.md
```

## Before you start

1. You have a `SOUL.md` (from the [SOUL Quiz](https://nurse-ai-os.org/soul-quiz.html) or the starter kit).
2. You've read `00-Start-Here/NO-PHI-BOUNDARY.md` and `00-Start-Here/DO-NOT-REMEMBER.md` in the starter kit. This kit assumes both, everywhere, always.
3. Optional but recommended: a `naio-projects.json` export from the [Life & Projects Quiz](https://nurse-ai-os.org/life-quiz.html). Its 17 domains carry sphere tags that map onto this fabric's four folders: `personal` → personal, `interest` → interest, `professional` → professional, and both `community` and `sidegig` → community.

## Day one

The kit follows the starter kit's split: numbered folders are the library you read; `Memory/` is yours to fill.

1. Copy this folder into your vault as `My-Nurse-AI-OS/19-Memory-Fabric/`. It stays there as the reference library — the cards and guides are read from it and edited in place when you revise a card.
2. Create the sphere folders under `Memory/` as described in `VAULT-STRUCTURE.md`, and copy `TRUST-LEDGER.md` to `Memory/TRUST-LEDGER.md` — that copy is your working ledger; every run, promotion, and revocation is recorded there (the kit copy stays as a clean template).
3. Pick **one** handoff card — Pre-Shift Setup Brief is the gentlest — and run it with your AI for a week, logging every run in `Memory/TRUST-LEDGER.md`. Evidence logs live where each card says, under `Memory/spheres/`.
4. Put the monthly memory review on your calendar now, before enthusiasm fades.

Do not start with three cards. One card, reviewed honestly, beats three approved on autopilot.

## The rules this kit lives under

- **No PHI, ever.** No patient names, identifiers, room numbers, or stories that could re-identify anyone — not even "just for tonight." The fabric remembers your life, not your patients'.
- **Local-first.** These are your files, on your device. Sync is your explicit choice, never a default. On an employer-owned device, this kit does not install.
- **Draft-and-attest.** Your AI gathers, prepares, and stages. You review and commit. No card in this kit sends, submits, or files anything on its own.
- **Trust is earned in the ledger.** A card's action mode widens only when your own ledger says it should — never because the AI performed well yesterday, and never automatically.
- **Not a bridge to the bedside.** Nothing here graduates toward EHRs, patient data, or clinical systems. That door has its own keys, and they are not personal ones (see DESIGN.md, section 4).

*Agents propose. Humans judge. Nurses steward.*
