---
name: naio-activity-log
description: Record what you just did to the NAIO Mission Control activity log. Use this at the end of any task worth remembering — a draft produced, a ritual run, a file changed, a boundary refused. Also use it when you decline to do something, because a refusal is the most valuable row in the ledger.
---

# NAIO activity log

You just did something. Write it down.

Nursing already has this rule — *if it isn't charted, it didn't happen* — and NAIO extends it: **if it isn't in the ledger, it didn't happen.** The ledger is what lets a nurse show an educator, a manager, or a skeptic exactly how she uses AI, without either of you having to remember.

## When to log

Log **once, at the end** of any task worth repeating or defending:

- work produced — a draft, a summary, a study set, a plan
- a scheduled ritual that ran
- a file you created or changed in the vault
- **any refusal** — you were asked for something near a boundary and declined
- any failure — the task did not complete

Do **not** log every tool call, every intermediate thought, or a task the nurse abandoned mid-sentence. One meaningful row beats forty noisy ones, and a noisy log stops being read.

## How

Call `mc-log`. It is the only interface; there is nothing else to configure.

```bash
mc-log --agent florence \
       --task "Drafted the weekly ledger entry" \
       --status completed \
       --model "anthropic/claude-sonnet-4" \
       --tier green \
       --sphere career \
       --detail "workspace/content/florence/2026-08-11-weekly.md"
```

| Flag | Required | Notes |
|---|---|---|
| `--agent` | yes | your agent id, lowercase |
| `--task` | yes | one short human-readable line, past tense |
| `--status` | yes | `completed` · `failed` · `refused` · `in_progress` |
| `--model` | yes | **the model you actually used.** Never `unknown` — `mc-log` rejects it |
| `--tier` | no | the EDENA tier the action ran under |
| `--sphere` | no | the SOUL sphere it belongs to |
| `--detail` | no | an artifact path or one clarifying sentence |

If Mission Control is not running, `mc-log` says so and exits 0. **A dashboard being down must never break a nurse's actual work.**

## Logging a refusal

This is the row that matters most, so make it specific:

```bash
mc-log --agent florence \
       --task "Refused: patient-specific dosing question" \
       --status refused \
       --model "anthropic/claude-sonnet-4" \
       --tier green --sphere career \
       --detail "Rail 2 — no patient-specific clinical reasoning. Offered the public guideline instead."
```

Name the rail. A refusal with a reason is evidence; a refusal without one looks like a malfunction.

## What must never go in a log line

- **No PHI.** No names, record numbers, room numbers, dates of care, or a story that could identify a patient — not in `--task`, not in `--detail`. If you are unsure whether something counts: it counts. The nightly PHI lint scans these columns, but the lint is a backstop, not permission.
- **No secrets.** No keys, tokens, or credentials, ever.
- **No employer-confidential content.** Protocols, forms, and internal materials stay where they are.
- **No student records, no personnel content** where the nurse's role carries those regimes.

## What this skill cannot do

It cannot approve a gate, raise a tier, schedule a job, or write runtime memory. No such command exists, deliberately — the log is an observation surface, and the control plane stays where the human is.

*Agents propose. Humans judge. Nurses steward.*
