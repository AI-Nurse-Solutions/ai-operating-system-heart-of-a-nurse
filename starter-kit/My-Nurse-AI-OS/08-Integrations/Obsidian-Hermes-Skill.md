---
name: obsidian-hermes-second-brain
version: 1.0.0
description: Sync an Obsidian vault with Hermes so skills, notes, SOPs, and memory become visible, editable, nurse-stewarded living files.
author: NAIO Institute
tags: [obsidian, hermes, second-brain, sync, skills, memory, vault]
edena_tier: Yellow
---

# Obsidian + Hermes Second-Brain Skill

> Carry the lamp. Keep the ledger. Make the ledger **visible**.

This skill turns your nurse-centered AI OS folder into a synced Obsidian vault that Hermes can read, update, and reason over. The goal is not to replace your judgment — it is to make the system’s memory and skills **transparent, editable, and stewarded by you**.

## What this skill does

- Connects an Obsidian vault to a Hermes host (MacBook, VPS, or both) so files stay in sync.
- Converts your prompts, checklists, SOUL.md files, and governance docs into **living files**.
- Lets you edit Hermes behavior by editing markdown notes — no terminal required.
- Makes skills, references, and memory visible in Obsidian’s graph view.

## When to invoke this skill

Use this skill when:

- You want Hermes to remember patterns across sessions without duplicating prompts.
- You want to see, organize, and edit your skills and memory in one visual place.
- You are ready to move from ad-hoc chat files to a structured second brain.
- You want backups: notes on MacBook + phone + VPS, encrypted, under your control.

## Core concept: living files vs. dead files

A **dead file** is one Hermes cannot easily access or update: a PDF, a locked Google Doc, a screenshot, or a note buried in a folder it never sees.

A **living file** is a markdown file in a synced vault that Hermes can:

- read as context,
- use as a skill,
- edit when asked,
- link to other living files,
- search and summarize.

Your vault is the bridge between human judgment and agent memory.

## Prerequisites

1. **Obsidian** installed on your primary device (macOS/Windows/Linux).
2. An **Obsidian account** if using Obsidian Sync.
3. A **Hermes host** where the vault will also live:
   - Option A: your MacBook / local machine.
   - Option B: a VPS (e.g., Hostinger) for 24/7 agent access.
4. **Sync method**:
   - **Obsidian Sync** — official, $4–5/month, encrypted, easiest setup.
   - **Syncthing** — open-source, free, more setup, fully self-hosted.

## Recommended nurse AI OS vault structure

```text
My-Nurse-AI-OS/
├── 00-Start-Here/
│   ├── WELCOME-Carry-the-Lamp.md
│   ├── MY-AI-VALUES.md
│   ├── NO-PHI-BOUNDARY.md
│   └── HUMAN-AGENCY-RULES.md
├── 01-SOUL/
│   ├── Personal-SOUL.md
│   ├── Professional-SOUL.md
│   └── Community-SOUL.md
├── 02-Skills/
│   ├── research/
│   ├── writing/
│   └── governance/
├── 03-Memory/
│   ├── yearly-goals.md
│   ├── quarterly-reviews/
│   └── decisions/
├── 04-Projects/
│   ├── community/
│   └── career/
├── 05-Learning/
│   ├── knowledge-inbox.md
│   └── weekly-review.md
└── 99-Archive/
```

## Setup prompts

Give these prompts to Hermes or your setup agent (e.g., Pi or Codex CLI).

### 1. Create the vault

```text
Create a new Obsidian vault called "My-Nurse-AI-OS" at ~/Documents/My-Nurse-AI-OS.
Inside it create the folder structure from the nurse AI OS starter kit.
```

### 2. Install Obsidian headless sync on the VPS

```text
On the VPS, install Obsidian headless (obsidian-headless) and log into the account.
Connect it to the remote vault named "My-Nurse-AI-OS".
Ensure the local sync directory is /root/My-Nurse-AI-OS or /home/hermes/My-Nurse-AI-OS.
Do not proceed until a test file created on the VPS appears in Obsidian on the MacBook.
```

### 3. Point Hermes at the vault

```text
Configure Hermes to load skills from /root/My-Nurse-AI-OS/02-Skills/
and use /root/My-Nurse-AI-OS/01-SOUL/ as part of its system memory.
Only load these files when relevant to keep the context window clean.
```

### 4. Test the loop

```text
Create a markdown note in Obsidian on the MacBook titled "VPS-Test".
Ask Hermes on the VPS to read it, append a line, and save it.
Confirm within 30 seconds that the change appears back in Obsidian on the MacBook.
```

## Example workflows

### Update a skill without the terminal

> "Please edit my Research skill to always include an EDENA-AS evidence-quality check before citing any source."

Hermes opens `02-Skills/research/Research-Skill-Prompts.md`, adds the instruction, and saves. Because the vault syncs, you see the change instantly in Obsidian.

### Run a `/go` research task into your vault

> `/go Find the 10 most-cited papers on nurse-led AI governance from 2024–2026, summarize each, and save the results to 05-Learning/nurse-ai-governance-research.md.`

Hermes works until the task is complete. The result is a **living file** you can reference, expand, or share — not a chat that scrolls away.

### Build a weekly review from your notes

> "Read my knowledge-inbox.md, weekly-review.md, and 03-Memory/decisions/ from the last 7 days. Summarize what I learned, what I decided, and what I should focus on next week. Save the review to 03-Memory/weekly-reviews/2026-W25.md."

## Safety and governance boundaries

- **No PHI in the vault unless your vault is in a HIPAA-covered, BAA-backed environment.** The public course vault stays PHI-free.
- **Keep human agency.** Hermes edits files; you review, approve, or revert. Use Git history or Obsidian Sync version history for rollbacks.
- **Encrypt the vault** if using Obsidian Sync. Set a strong encryption password and store it in a password manager.
- **Audit skills regularly.** A skill you have not reviewed in 90 days is suspect. Ask Hermes: "Which skills have I not used in the last 90 days?"
- **Separate personal/professional/community memory.** Use different SOUL files or vault folders so Hermes loads only relevant context.

## Troubleshooting checklist

| Symptom | Likely fix |
|---|---|
| Changes not syncing | Check Obsidian Sync status on both devices. Ensure both point to the same remote vault and encryption password. |
| Hermes cannot read vault files | Confirm Hermes is pointed at the correct path and has file permissions. |
| Vault too large / slow context loading | Archive old notes to `99-Archive/`. Ask Hermes to load only relevant folders. |
| Duplicate files after sync conflict | Review the conflict file, choose the better version, delete the duplicate, and document the decision. |
| Skill changes cause Hermes to behave oddly | Roll back using Obsidian Sync history or git. Then edit the skill incrementally. |

## Closing rule

> The lamp is yours. The ledger is yours. Hermes may write in it — but nurses steward.
