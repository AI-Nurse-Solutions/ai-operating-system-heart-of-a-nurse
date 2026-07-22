# FUTURE Mission Control — User Installation and Recovery Guide

## What you have

This download is a **build kit for Hermes**. It contains a working dashboard baseline and complete FUTURE build contracts, but it is not yet your finished learner application. Hermes must build and test a separate local release. The process may take many minutes and several visible turns.

FUTURE can support learning, life planning, career growth, technology practice, evidence checking, professional communication, and community projects. It cannot provide care directions, complete prohibited schoolwork, verify competence, authorize work, or act in an external system.

## Before you begin

- Use a private local folder and an isolated Hermes build workspace.
- Make a copy of the downloaded ZIP and keep the original unchanged.
- Decide whether you are using Nursing Student, Nursing Assistant, or Bridge. Bridge keeps school and work separate.
- Do not prepare or upload patient details, clinical stories, screenshots, charts, exams, restricted assignments, school/employer records, passwords, tokens, financial credentials, or confidential information.
- Know that Soul Quiz results are still represented only by a reviewed derived profile. Never give Hermes raw quiz answers or ask it to display raw `SOUL.md`.

## Verify the kit

Extract the ZIP and open a terminal in its root. On macOS/Linux, use Finder/Archive Utility or `unzip`; Python's `zipfile.extractall()` does not preserve executable mode bits and the strict package check will fail. If that occurs, discard that extraction and extract the unchanged ZIP again with a mode-preserving tool rather than changing modes blindly. Run:

```text
python3 tools/verify-build-kit.py --package .
```

Windows may use `py tools\verify-build-kit.py --package .`. Windows cannot express the bundled POSIX mode contract, so the verifier reports a mode warning; `--zip` still validates the outer archive's recorded modes. Verification checks this package's contents and provenance; it does not say the future app has been built.

## Start the Hermes build

Give Hermes the complete ZIP and the instruction shown in `README-FIRST.md`. Hermes should first show a read-only preflight report and one Implementation Activation Card. Review:

- the exact source copy and output folder;
- new dependencies and licenses;
- local URL, database, backup, and log locations;
- selected pathway and separated contexts;
- safe data ceiling and prohibited information;
- Hermes capabilities actually detected;
- agents, all P0 Disabled;
- tests, rollback, removal, and clean-install plan;
- blockers and unsupported features.

Choose `APPROVE`, `REVISE`, or `CANCEL`. Approval covers only the card. It does not approve live-care use, patient data, graded-work completion, profile changes, external actions, or agent activation.

## Follow the phases

Save S0 through S4 receipts. Each receipt should list actual changes, tests, evidence, running processes, blockers, rollback point, and next step. If interrupted, paste the exact resume command from `GIVE-THIS-PACKAGE-TO-HERMES.md`. Hermes must reverify state and must not duplicate dashboards or records.

Do not accept a screenshot, preview, source tree, “tests specified,” or a development server as final proof. The final report must say exactly Operational, Core operational; AI setup pending, or Not operational according to the evidence.

## First run of the finished app

1. Confirm the local URL is loopback-only and matches the final handoff.
2. Create the local owner and keep recovery material private.
3. Choose Student, Assistant, or Bridge yourself.
4. Choose protected spaces and contexts; use `Unknown`, `Skip`, `Not now`, or session-only where needed.
5. Preview the derived Mission Profile and Starter workspaces. Edit or reject anything wrong.
6. Confirm all 18 SuperPowers are Inactive, workflows are Preview Only, agents are P0 Disabled, external actions are Off, and the fifth launcher is empty.
7. Start one low-risk mission with no patient, restricted, or live assessed content. Make your own first attempt.
8. Finish with a source check, human authority, AI-use receipt, and the next step you can do independently.

## A safe first mission

Try: “Build a realistic seven-day study and recovery plan for a fictional pharmacology topic using only my non-sensitive schedule constraints. I will attempt the plan first. Help me check feasibility and identify what I should confirm with faculty.”

Do not use this app for a real patient, a live exam, a prohibited assignment, clinical documentation, medication administration, scope/delegation decisions, or a confidential school/employer matter.

## Daily controls

- **Pause All:** cancel running/queued AI work and prevent new runs; keep saved records.
- **Stop/Kill:** end the selected stream/run and record an honest receipt.
- **Safe Reset:** preview return to synthetic, session-only, disconnected, no sharing/external action, Core Four, empty fifth slot, inactive powers, and P0 agents.
- **Correct:** revise facts or sources and mark dependent outputs stale.
- **Export/Backup:** preview included data, exclude secrets/prohibited data, encrypt or protect the file, and verify restore.
- **Delete:** show scope and consequences; remove eligible primary and derived content.
- **Overlay removal:** remove FUTURE specialization records while preserving compatible foundation and unrelated user work.
- **Rollback:** restore the last compatible app/database backup after preview.
- **Uninstall:** stop services, back up or delete by choice, remove app files/launchers, and report anything retained.

## Backup, update, and rollback

Before any update, stop the app; create a versioned database and configuration backup; export permitted learner records; record current app/schema versions and checksums; and test the backup. Update only from a verified package. Run migrations once and verify counts/critical records. If validation fails, stop, preserve diagnostics, restore the matched app and database backup, and record the rollback. Never open a newer database with an older binary unless the final release explicitly proves compatibility.

## Sensitive-data event

Stop immediately. Do not ask AI to repeat, redact, summarize, or classify the content. Cancel the run; prevent more persistence/export where possible; use Activity History and deletion controls; preserve only non-content incident facts; and follow the authorized school, employer, clinical-site, privacy, security, or incident route. The app is not an incident-response authority.

## How FUTURE helps—and what remains yours

Use FUTURE to practice thinking, verify sources, organize humane plans, rehearse communication, prototype safely, build truthful evidence, and ask better questions. Your learning, authorship, verification, decisions, relationships, and accountability remain yours. Passport stages and badges are developmental records, not grades, licenses, certifications, credentials, or proof of clinical competence.
