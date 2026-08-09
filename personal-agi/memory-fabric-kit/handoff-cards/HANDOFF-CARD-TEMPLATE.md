# Handoff Card — [Name]

A handoff card is a contract between you and your AI for one class of delegated screen work. No card, no handoff. If a task doesn't fit an existing card, that's a new card (start it at Draft), not a stretch of this one.

| Field | Value |
|---|---|
| **Sphere** | personal / interest / professional (non-clinical) / community |
| **Action mode** | Observe / Draft / Recommend / Prepare Action / Act With Approval |
| **Data class** | D0 or D1 only |
| **What the AI does** | One paragraph, concrete, bounded |
| **What the AI never does** | The explicit outside-the-fence list |
| **Accounts/credentials touched** | Name them all; "none" is a valid and excellent answer |
| **Stop conditions** | When the AI must halt mid-task and hand back |
| **Evidence log** | Where each run's record lives |
| **Revoke** | How you turn this card off (should take under a minute) |

## Universal stop conditions (every card, always)

The AI halts and hands back the moment any of these appear, no matter what the card says:

- anything patient-adjacent enters the task — a name, a room, a story;
- a login, paywall, CAPTCHA, or permission prompt the card didn't anticipate;
- the task wants to touch an account or file outside the declared list;
- an irreversible step (send, submit, pay, delete, post) — those are yours alone unless the card explicitly holds Act With Approval *for that step*;
- the AI is uncertain. Uncertainty hands back; it does not improvise.

## Run record (append per run, one line in TRUST-LEDGER.md too)

```text
RUN: <date> — <what was prepared> — <reviewed: Y/N> — <corrections> — <outcome>
```
