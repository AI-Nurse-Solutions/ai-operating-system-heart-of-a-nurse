# Handoff Card — [Name]

A handoff card is a contract between you and your AI for one class of delegated screen work. No card, no handoff. If a task doesn't fit an existing card, that's a new card (start it at Draft), not a stretch of this one.

| Field | Value |
|---|---|
| **Sphere** | personal / interest / professional (non-clinical) / community |
| **EDENA risk tier** | Green or Yellow only in this kit — tier per the starter kit's EDENA Stewardship Lens |
| **Action mode** | Observe / Draft / Recommend — Recommend is this kit's ceiling, capped further by the risk tier (see below) |
| **Data class** | D0 or D1 only |
| **What the AI does** | One paragraph, concrete, bounded |
| **What the AI never does** | The explicit outside-the-fence list |
| **Accounts/credentials touched** | Name them all; "none" is a valid and excellent answer |
| **Stop conditions** | When the AI must halt mid-task and hand back |
| **Evidence log** | Where each run's record lives |
| **Revoke** | How you turn this card off (should take under a minute) — always beginning with a written `REVOKED` entry in the trust ledger |

## The tier sets the ceiling

Risk tier and action mode are separate axes, and the tier caps the mode: **Green supports Observe or Draft only; Recommend requires Yellow**, with Yellow's controls (a named owner — you — and your review before anything is adopted). Recommend is also the ceiling of the entire kit: per the governance kit's public ceiling (`governance-kit/GOVERNANCE.yaml`), Prepare Action, Act With Approval, and Constrained Autonomy require a separately, formally authorized environment that neither this kit nor any ledger streak can grant. No ledger streak changes a card's tier either. If a card seems to deserve a wider mode than its tier allows, that's a card revision — re-tier it against the EDENA Stewardship Lens (`04-Governance/EDENA-Stewardship-Lens.md`) first, in writing, then let the ledger govern promotion within the new ceiling.

## Universal stop conditions (every card, always)

The AI halts and hands back the moment any of these appear, no matter what the card says:

- anything patient-adjacent enters the task — a name, a room, a story;
- a login, paywall, CAPTCHA, or permission prompt the card didn't anticipate;
- the task wants to touch an account or file outside the declared list;
- an irreversible step (send, submit, pay, delete, post) — those are always yours alone; no card in this kit can hold them;
- the AI is uncertain. Uncertainty hands back; it does not improvise.

## Run record (append per run, one line in the trust ledger too)

```text
RUN: <date> — <what was prepared> — <reviewed: Y/N> — <corrections> — <outcome: what you committed>
```

In a single-user vault the reviewer is always you: the Y is your attestation, and the outcome field is the final-commit evidence — what you actually did with the work (used as-is, edited then sent, filed, discarded).

Every field of every record — here and in the trust ledger — is written to the no-PHI standard: no patient-adjacent detail, no credentials, no employer-confidential content, no third-party private information. Describe the work, not the sensitive thing that stopped it. A run halted by a stop condition uses one canonical format in the evidence log and the ledger alike — `RUN: <date> — BLOCKED: <stop-condition name>` — omitting only the sensitive trigger content, never the marker itself.
