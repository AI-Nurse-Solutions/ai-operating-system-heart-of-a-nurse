# Handoff Card — CEU & Renewal Tracker

Your AI keeps the running ledger of continuing-education hours, certifications, and renewal deadlines — and, once promoted, recommends your renewal plan with its evidence. It never submits anything.

| Field | Value |
|---|---|
| **Sphere** | professional (non-clinical) |
| **EDENA risk tier** | Yellow — named owner (you), your review before anything is adopted; permits Recommend |
| **Action mode** | Draft (promotable to Recommend via `Memory/TRUST-LEDGER.md` — the kit's ceiling) |
| **Data class** | D1 |
| **What the AI does** | Maintains `Memory/spheres/professional/ceu-ledger.md`: courses completed, hours by category, certificates on file, every renewal deadline (license, BLS/ACLS, specialty certs) with lead-time reminders surfaced in your daily/weekly brief. **At Recommend, additionally:** recommends your renewal plan — which forms to complete, which certificates to gather, what's missing and by when — as a checklist with its supporting evidence, for you to assemble and submit yourself. |
| **What the AI never does** | Submit forms, make payments, contact a board or certifying body, log in to licensing portals, or mark anything "complete" that you haven't confirmed. |
| **Accounts/credentials touched** | None at Draft or Recommend — portal logins remain yours; the AI works from files you drop in the vault. |
| **Stop conditions** | Universal list, plus: any discrepancy between your records and a requirement (hours short, category mismatch) → it flags loudly rather than papering over. |
| **Evidence log** | `Memory/spheres/professional/ceu-ledger.md` (append-only run notes at the bottom). |
| **Revoke** | Record `REVOKED: CEU & Renewal Tracker` in the trust ledger, tell your AI the card is revoked, then delete the card. The CEU ledger file stays — it's yours. |

## Why this card second

It's the first card with a real promotion path, so it's where your trust ledger starts doing its job. A missed renewal is expensive; a wrong recommendation you catch at review is nearly free. That asymmetry is exactly what the Draft → Recommend path was designed for.

## Prompt seed

> Per handoff card 02, update my CEU ledger from the certificates in [folder] and show me what changed, plus any deadlines inside their lead time. Draft mode: update the ledger file and flag gaps — stage nothing, submit nothing.
