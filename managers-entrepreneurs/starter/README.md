# Nurse AI OS — Mission Control package for nurse managers and entrepreneurs

Version 1.0.0 · for Hermes Agent · https://nurse-ai-os.org/managers-entrepreneurs/

This package is the same for everyone. It does **not** contain your quiz answers.
Take the SOUL quiz on the page above, download `SOUL.md` (and optionally
`naio-soul.json`), and keep them in the same folder as this package.

## What is inside

| Path | What it is |
|---|---|
| `README.md` | This file. |
| `HANDOFF-PROMPT.txt` | Paste into Hermes on first run. Hermes reads, summarizes, and proposes. It changes nothing without your approval. |
| `SETUP-CHEATSHEET.md` | Install Hermes, place your SOUL, run your first week. |
| `mission-control.html` | Offline weekly board with Lead and Build lanes. Open it in a browser. Exports Markdown. |
| `mission-control-packet/leader/` | The Nurse AI OS leader Mission Control packet: `manifest.json`, `DATA-BOUNDARY.md`, and templates for an executive brief, meeting pack, communication plan, and dashboard summary. |
| `venture/` | The nurse venture kit: offer canvas, 30-day validation sprint, prompt pack, content calendar, outreach script, landing page copy, and no-PHI guardrails. |
| `CHECKSUMS.sha256` | SHA-256 of every file in this package. Run `shasum -a 256 -c CHECKSUMS.sha256` to confirm nothing changed. This is a checksum, not a signature. |

## Use it in four steps

1. Unzip this package into a project folder, for example `~/Nurse-AI-OS/manager-entrepreneur`.
2. Put your `SOUL.md` and `naio-soul.json` in that folder.
3. Open Hermes in that folder and paste `HANDOFF-PROMPT.txt`.
4. Open `mission-control.html`, set this week's priorities, export, and ask Hermes for a draft weekly brief.

## Plain limits

- The HTML board is a manual template. It does not save, sync, call a model, or run tasks. Export before closing.
- Templates are drafts. Nothing here sends, posts, schedules, or connects accounts.
- A SOUL file guides behavior. It is not a technical safeguard.
- Use public sources and synthetic examples. No patient information, personnel records, employee performance details, client confidential data, passwords, or API keys.
- Roles are self-described and not verified. No employer, regulatory, or legal approval is implied.
- EDENA: not evaluated for this package.

Agents propose. Humans judge. Nurses steward.
