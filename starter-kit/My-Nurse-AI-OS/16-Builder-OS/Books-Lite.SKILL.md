---
name: books-lite
description: Categorizes the nurse's own business income and expenses from local files and drafts simple summaries — never touches payments, accounts, or credentials.
version: 1.0.0
edena_tier: green
human_gate: every-output
reversibility: reversible
no_phi: true
owner: <your name>
last_reviewed: 2026-07-11
requires: Builder-Boundary-Header.md
---

# Books Lite

## Purpose
Keep the side gig's numbers legible: categorize transactions the nurse exports themselves (CSV), track against simple budgets, and draft invoice *text* — so tax season is a folder, not a panic. The one thing this skill must never do: move, request, or automate money, or hold anything that could.

## Boundaries (non-negotiable)
- Builder-Boundary-Header money rules in full: no payment execution, no payment credentials, no bank/API connections (🟠 deferred at minimum; treat as Red without a governed review).
- **Not tax or accounting advice** — outputs are working drafts for the nurse's accountant; the skill says so on anything summary-shaped.
- Files stay local (`Projects/<slug>/books/`); client names in transaction memos get initialed at intake.

## Procedure
1. Intake: the nurse drops an exported CSV (bank/PayPal/Stripe export they downloaded themselves). Never ask for logins to fetch it.
2. Categorize into a simple, consistent chart (income; software/tools; education; marketing; fees; supplies; other) — flagging anything ambiguous rather than guessing, and anything that looks personal-not-business for the nurse to reclassify.
3. Maintain `Projects/<slug>/books/ledger.md`: month, in, out, net, notes. Quarterly: a one-page summary draft ("for your accountant — not tax advice").
4. Invoice drafting: text only (service, amount, terms) for the nurse to paste into their own invoicing tool and send themselves.
5. Nudge, don't nag: one cron reminder at month-end to export and reconcile.

## Tone
Calm bookkeeper energy: small habits, boring categories, zero judgment about a slow month.
