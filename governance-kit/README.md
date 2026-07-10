# The Governance Kit

*Domondon Dominium™ Level 1 — governance as files. Part of Nurse AI OS.*

This folder makes your AI system **governed**: every task classified before it runs, human judgment gates where they belong, and a written record of what was done and who decided. It works with Hermes or any AI chat system that can read files.

🕯️ *Carry the lamp. Keep the ledger. Agents propose. Humans judge. Nurses steward.*

## What's in the kit

| File | What it is |
|---|---|
| `CHARTER.md` | Who you are, what your system is for, and what it must never do. **Fill this in first.** |
| `GOVERNANCE.yaml` | The rulebook: risk tiers, automation levels, the prohibited zone, escalation rules. Works as written; edit with care. |
| `LEDGER.md` | The append-only record. The AI writes an entry for every significant piece of work. |
| `workflows/_TEMPLATE.md` | Blank workflow with the governance header. Copy it for each repeatable task. |
| `workflows/example-education-article.md` | A filled-in example: drafting a public-facing article, fully governed. |
| `workflows/example-weekly-brief.md` | A second example: your Monday brief, low-risk and mostly automated. |
| `prompts/session-start.md` | Paste at the start of every session — loads the governance into the AI. |
| `prompts/five-rights-preflight.md` | The delegation check the AI runs on itself before any task. |
| `prompts/escalation-sbar.md` | How the AI escalates to you when it's uncertain or blocked. |
| `prompts/improvement-loop.md` | The monthly 30-minute loop that makes the system better. |

## Setup (10 minutes)

1. **Drop this folder** into your Nurse AI OS starter kit, next to your SOUL file.
2. **Fill in `CHARTER.md`** — name, mission, boundaries. Ten minutes, honest answers.
3. **Start every session** by pasting `prompts/session-start.md` (or telling your AI: *"Read the governance-kit folder and confirm the rules back to me"*).
4. That's it. The AI now classifies work by tier, runs the Five Rights before acting, stops at your gates, and writes the ledger.

## The three rules under everything

1. **Tasks delegate. Judgment does not. Accountability never moves.** The AI drafts, retrieves, organizes, and reminds. You decide. Everything the AI produces is a draft until you say otherwise.
2. **No patient data. Ever.** No names, charts, screenshots, room numbers, dates, or stories that could identify a patient — in any AI tool, at any level. If you're unsure whether something counts: it counts.
3. **If it isn't in the ledger, it didn't happen.** Significant work gets an entry. That record protects your patients, your license, and you.

## Honest limits (read this)

Level 1 governance is **behavioral**: the AI follows these rules because its instructions demand it, and models follow instructions imperfectly. These files make a well-intentioned AI governable — they do not make a system tamper-proof. That is why the gates in this kit are *yours*, not the AI's: nothing external-facing, patient-adjacent, or irreversible happens without a human hand on it. Structural enforcement (permissions, scoped access, real audit infrastructure) is what Florence-X exists for.

---
*Domondon Dominium™ © 2026 Robert Domondon · Free for nurses and nursing students during the founding year.*
