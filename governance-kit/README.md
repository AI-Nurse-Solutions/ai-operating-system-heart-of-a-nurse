# The Governance Kit

*Domondon Dominium™ Level 1 — governance as files. Part of Nurse AI OS.*

This folder provides an **advisory governance practice**: classify risk, data, and action independently; place human judgment gates where they belong; and keep a written record of what was proposed and who decided. It works with Hermes or any AI chat system that can read files, but it does not mechanically enforce controls.

🕯️ *Carry the lamp. Keep the ledger. Agents propose. Humans judge. Nurses steward.*

## What's in the kit

| File | What it is |
|---|---|
| `CHARTER.md` | Who you are, what your system is for, and what it must never do. **Fill this in first.** |
| `GOVERNANCE.yaml` | The Directive v1.1 rulebook: independent risk tiers, data classes, action modes, the prohibited zone, and escalation rules. |
| `LEDGER.md` | The append-only record. The AI drafts entries; the human reviews and appends them. |
| `STEWARD-COUNCIL.md` | Proposed advisory-council template for future human review of a shared skill library; it does not establish a seated body or authority. |
| `workflows/_TEMPLATE.md` | Blank workflow with the governance header. Copy it for each repeatable task. |
| `workflows/example-education-article.md` | A filled-in example: drafting a public-facing article, fully governed. |
| `workflows/example-weekly-brief.md` | A second example: your Monday brief, low-risk and draft-only. |
| `prompts/session-start.md` | Paste at the start of every session — loads the governance into the AI. |
| `prompts/five-rights-preflight.md` | The delegation check the AI runs on itself before any task. |
| `prompts/escalation-sbar.md` | How the AI escalates to you when it's uncertain or blocked. |
| `prompts/improvement-loop.md` | The monthly 30-minute loop that makes the system better. |

## Setup (10 minutes)

1. **Drop this folder** into your Nurse AI OS starter kit, next to your SOUL file.
2. **Fill in `CHARTER.md`** — name, mission, boundaries. Ten minutes, honest answers.
3. **Start every session** by pasting `prompts/session-start.md` (or telling your AI: *"Read the governance-kit folder and confirm the rules back to me"*).
4. Ask the AI to classify risk, data, and action before drafting, and to run the Five Rights before any Yellow recommendation. You review the result and append any ledger entry yourself.

## The three rules under everything

1. **Tasks delegate. Judgment does not. Accountability never moves.** The AI drafts, retrieves, organizes, and reminds. You decide. Everything the AI produces is a draft until you say otherwise.
2. **No patient data. Ever.** No names, charts, screenshots, room numbers, dates, or stories that could identify a patient — in any AI tool, at any level. If you're unsure whether something counts: it counts.
3. **If it isn't in the ledger, it didn't happen.** Significant work gets an entry. That record protects your patients, your license, and you.

## Honest limits (read this)

Level 1 governance is **behavioral**: the AI follows these rules because its instructions ask it to, and models follow instructions imperfectly. These files do not make a system tamper-proof, activate Florence-X, establish Directive conformance, or authorize PHI or clinical use. The public ceiling is D0/D1 data, Green/Yellow risk, and Observe/Draft/Recommend action; Recommend begins at Yellow. You perform every external, irreversible, installation, scheduling, publication, or file-changing action.

---
*Domondon Dominium™ © 2026 Robert Domondon · Free for nurses and nursing students during the founding year.*
