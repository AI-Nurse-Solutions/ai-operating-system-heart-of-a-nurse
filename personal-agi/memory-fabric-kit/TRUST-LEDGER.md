# Trust Ledger

This file is the evidence base for every handoff your AI runs. It answers one question honestly: *has this card earned the action mode it holds?* Copy it into `Memory/TRUST-LEDGER.md` and log every run — including the boring ones. Especially the boring ones: the entry you skip because "it went fine" is the first brick in autopilot.

## How to log

One line per run. Thirty seconds. The "Read it all?" column is the one that matters — it is your automation-complacency alarm. If you find yourself writing N there, or hesitating, the card's action mode narrows until the habit recovers.

Every field follows the no-PHI standard from the card template: no patient-adjacent detail, no credentials, no employer-confidential content, no third-party private information. A run halted by a stop condition is logged as `BLOCKED: <stop condition name>` in the "What the AI prepared" column — never the sensitive content that triggered the halt.

| Date | Card | Mode used | What the AI prepared | Read it all? (Y/N) | Corrections | Outcome |
|---|---|---|---|---|---|---|
| 2026-08-12 | Pre-Shift Setup Brief | Draft | Brief for Tue day shift | Y | Swapped stale commute note | Used as-is after fix |
| 2026-08-13 | Pre-Shift Setup Brief | Draft | Brief for Wed day shift | Y | None | Used as-is |
|  |  |  |  |  |  |  |

## Promotion and demotion

A card changes action mode only here, in writing, by you.

**To widen a card's mode** (e.g., Draft → Recommend), all five must be true over the trailing month:

1. at least 10 logged runs in the current mode;
2. "Read it all?" is Y on every one of them;
3. corrections were minor (wording, staleness) — never wrong-target, invented content, or scope creep;
4. the target mode sits within the ceilings — a Green card stops at Draft, Recommend requires a Yellow card, and nothing in this kit promotes past Recommend. If the tier itself seems wrong, that's a card revision made against the EDENA Stewardship Lens first, separately from — and never inside — a ledger promotion;
5. you can say why widening helps *you*, not just the AI.

Record it: `PROMOTED: <card> to <mode>, <date>, because <reason>`.

**To narrow or revoke a card** — any one of these, same day, no debate:

- a wrong-target or invented-content error, however small;
- you approved something you hadn't fully read;
- the card touched anything outside its declared scope;
- it brushed against the no-PHI boundary in any way (this one also triggers the self-audit in MONTHLY-MEMORY-REVIEW.md).

Record it: `REVOKED/NARROWED: <card>, <date>, because <reason>`.

## Ceilings

Recommend is the widest mode any card in this kit can ever reach — the public ceiling of the governance kit (`governance-kit/GOVERNANCE.yaml`) — and only ever inside the personal, interest, professional (non-clinical), and community spheres. Prepare Action, Act With Approval, and Constrained Autonomy require a separately, formally authorized environment that this kit cannot grant. No ledger streak — however clean — promotes a card past that ceiling or toward patient data, employer systems, or clinical surfaces. Those ceilings belong to [DESIGN.md](../DESIGN.md) and `GOVERNANCE.yaml`, not to this file.

## Promotion log

```text
(example)
PROMOTED: CEU-Renewal-Tracker to Recommend, 2026-09-15, because a month of
clean Draft runs and I want the renewal plan recommended with evidence,
not just tracked.
```
