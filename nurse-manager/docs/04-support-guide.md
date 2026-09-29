---
title: Nurse AI OS Manager Edition — support guide
date: 2026-09-29
authorship: Substantially AI-generated (Claude Code) with human review pending
status: Draft for steward review (build step 6.3)
---

# Support guide

This guide is for a pilot manager and the person who supports them. It
says what the app does today, not what it may do later. Where something
needs the command surface, it says so; managers never have to use it.

Two rules apply everywhere in this guide:

- **Keep patient information, colleagues' names, and staff performance
  out.** That includes questions, screenshots, feedback, and backups you
  hand to anyone.
- **The privacy screen does not detect names.** It refuses identifiers
  such as record numbers, dates of birth, room and bed numbers, phone
  numbers, and email addresses. Passing it never means text is free of
  patient information.

## 1. What the app is

Nurse AI OS Manager Edition keeps your projects, tasks, decisions, sources,
learning, contributions, and weekly brief in one workspace on your own
computer. It drafts from your records; you accept what you reviewed.

It does **not**:

- email, post, publish, or upload anything
- connect to your employer's systems
- run an AI model unless you connect one that runs on this computer; no
  cloud AI service is offered
- accept a draft for you, or complete a task without your evidence

## 2. Install and launch

**Status today: there is no build for managers yet.** The builds made by
`.github/workflows/nurse-manager-app.yml` for Windows, macOS, and Linux are
unsigned test builds. Do not give them to managers until they are signed
(build steps 0.9 and 1.9).

When a signed build exists, launching works like this, and it already
works this way in the test builds:

1. Double-click Nurse AI OS. Your browser opens at the app. Nothing is
   typed into a terminal, and no Python or API key is needed.
2. The first time, choose **Explore the sample workspace** or **Start your
   own workspace**. The first-run screen says what the app does and does
   not do before anything is created.
3. The page says the app is running on this computer and offers **Quit
   Nurse AI OS**. With no page open, it stops by itself after 15 minutes.

Things that can happen, and what to do:

| You see | Why | Do this |
|---|---|---|
| "This page is not connected to Nurse AI OS. Reopen the app." | The tab has no launch key, for example a bookmark or a copied address. Each launch makes a new key. | Double-click Nurse AI OS again. It opens a connected tab. |
| The tab was closed and the app is still running | Only one copy runs for each user. | Double-click Nurse AI OS again. It reopens the browser at the running copy. |
| "Nurse AI OS has stopped" | You pressed Quit, or no page was open for 15 minutes. | Your work is saved. Double-click Nurse AI OS to open it again. |

## 3. Where your records are

Records live in your user-data folder, never inside the app:

| System | Folder |
|---|---|
| Windows | `%LOCALAPPDATA%\Nurse AI OS` |
| macOS | `~/Library/Application Support/Nurse AI OS` |
| Linux | `~/.local/share/nurse-ai-os` (or `$XDG_DATA_HOME/nurse-ai-os`) |

Inside it, the `workspace` folder holds everything that is yours:

- `workspace.sqlite`, the records
- `exports/`, files the command surface exported
- `backups/`, safety copies taken before a restore

The other files in the data folder (`app.instance`, `app.lock.json`) only
keep a single copy running. Do not share them: `app.lock.json` holds the
current launch key.

## 4. Back up

**Anyone can do this.**

1. Press **Quit Nurse AI OS** and wait for "Nurse AI OS has stopped".
2. Copy the whole `workspace` folder somewhere your employer permits for
   your own files. Put the date in the copy's name.

Quit first. A copy taken while the app is writing may be incomplete.

**With the command surface** (a support person, from a copy of this
repository, Python 3.11 or later, `PYTHONPATH=nurse-manager/src`):

```bash
python3 -m nurse_manager backup "<data folder>/workspace" /path/to/backup-2026-09-30.sqlite
```

This makes a consistent copy even while the app is open. It refuses to
overwrite an existing file.

## 5. Restore

**Anyone can do this**, but nothing checks the copy for you:

1. Quit Nurse AI OS.
2. Rename the current `workspace` folder to `workspace-before-restore`.
   Do not delete it: anything you did after the backup is only there.
3. Copy the backed-up folder into the data folder and name it `workspace`.
4. Open Nurse AI OS.

**With the command surface**, the checks are done for you:

```bash
python3 -m nurse_manager restore "<data folder>/workspace" /path/to/backup-2026-09-30.sqlite
```

- It **refuses** when the current workspace holds changes the backup does
  not, and says how many. Nothing is lost by the refusal.
- It always takes a safety copy first, in `workspace/backups/`.
- `--discard-newer` restores anyway. Use it only after saving anything you
  need from the current workspace.
- A backup made by a newer release cannot be restored by an older one. A
  backup from an older release is brought up to date as it is restored.

## 6. Setting the sample aside

This computer keeps one workspace. If you explored the sample and now want
your own:

1. Quit Nurse AI OS.
2. Rename the `workspace` folder to `workspace-sample`.
3. Open Nurse AI OS. The first-run screen appears, and you can start your
   own workspace.

## 7. After a crash

If the app, the browser, or the computer stops unexpectedly, open Nurse AI
OS again. What to expect:

- **It starts.** The single-copy lock belongs to the running program, so
  the operating system releases it when the program ends. A crash never
  blocks the next launch.
- **Saved work is intact.** Every change is one database transaction.
  A change that was half done is rolled back, never half kept.
- **An AI request that was on its way is abandoned.** Its reply is never
  saved or shown, and it stops being listed as working. Ask again if you
  still need it.
- **The recurring weekly brief catches up.** A run interrupted part way
  leaves nothing half done. It runs at the next launch that week.

**Exports need one extra step, and only with the command surface.** The
app's screens never write export files. If a support person was running
`export`, `approve`, and `run` and the export was interrupted, run:

```bash
python3 -m nurse_manager reconcile "<data folder>/workspace"
```

`reconcile` checks each interrupted export against the file on disk. It
never runs one again:

- If the file matches exactly what was approved, it is recorded as
  succeeded.
- Otherwise, it is recorded as `effect_unknown`, and the action cannot run
  again. Propose a new export if you still need one.
- It prints every action it settled. An empty list means nothing was
  interrupted.

## 8. Stopping assistants

- **Stop everything.** On Mission Control, **Assistants at work** lists
  every request waiting for a model and the recurring brief. **Stop all
  assistants** stops them all at once. While stopped:
  - nothing is sent to a model;
  - a request already waiting returns within about a second, and its
    reply is discarded;
  - the recurring brief waits.
- **Stop one piece of work.** A **Stop assistants** button appears wherever
  a model is working.
- **Nothing restarts by itself.** Only you can press **Let assistants work
  again**.
- **Disconnect the model.** On **AI assistance**, **Disconnect the AI
  model** goes back to no model. Everything still works without one.
- **Quit** stops the app and everything in it.

A model that runs on this computer may finish its own work after a stop.
Nothing it returns is used.

## 9. How packs are reviewed

Packs are reviewed sets of document templates: education, committee, and
communication. The full rules are in [`../packs/README.md`](../packs/README.md).

- Each pack names its maintainer, the date it was reviewed, and the date
  its next review is due.
- Each template is pinned by hash to the shared deliverable catalog. A
  changed template fails the tests until someone reviews it again.
- A pack past its review date starts no new documents, and the app names
  who to ask. A pack that fails a check is shown as unavailable and never
  used.
- A document started from a pack is a draft. You write it and accept the
  exact text you reviewed, as with the weekly brief. Documents already
  started keep the pack version they started from.

## 10. Pilot feedback

On **Help and feedback**, write what worked, a problem, an idea, or a
question about the app. It is kept on this computer only.

- The privacy screen checks each item when you save it, and the whole
  export again before it is made.
- **Preview what will be shared** shows the exact file. It contains:
  - the app version;
  - whether this is the sample;
  - the date;
  - your items.

  It never contains the workspace's name, your name, or any other record.
- **Save as a file** saves exactly that text through your browser. The app
  sends nothing. You give the file to your pilot team the way they asked.
- If anything changed after you previewed, nothing is exported. Preview
  again.
- Every export holds all your feedback. Delete what you no longer want to
  share first. Deleted feedback is gone for good.

From the command surface, the same steps are `pilot-feedback-add`,
`pilot-feedback-preview`, and `pilot-feedback-export --reviewed-sha <sha256
from the preview> --by "<the workspace's manager>"`.

## 11. Where to get help

- **Your pilot team.** They tell you how to reach them. Describe what you
  did and what you saw. Do not include patient information, colleagues'
  names, or screenshots that show either.
- **Safety events and data-boundary problems** are reported as
  [`SAFETY.md`](../../SAFETY.md) says: to your organization's incident
  process, and privately to this project. Never include PHI.
- **The documents behind this guide:** [`../README.md`](../README.md),
  [`01-build-steps.md`](01-build-steps.md), and the decisions in
  [`adr/`](adr/).
