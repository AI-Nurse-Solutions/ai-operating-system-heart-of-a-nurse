---
title: Weekly manager brief — journey, states, and failure states (NM-002)
date: 2026-09-28
authorship: Substantially AI-generated (Claude Code) with human review pending
---

# Weekly manager brief journey

The first useful workflow: *prepare and review my weekly manager brief.*
It runs entirely without a model, a network, or an API key.

## Journey

| Step | Manager does | System does | Backing call |
|---|---|---|---|
| 1 | Chooses Nurse Manager → Personal → "Try the sample brief" | Creates a workspace marked **sample**; every view and render says so | `load_sample` / `nurse-manager sample` |
| 2 | Opens Mission Control | Shows three priorities, Needs my judgment, projects in motion, follow-ups (overdue flagged), assistants (honestly "none connected"), and recent accepted outputs | `mission_control` |
| 3 | Captures priorities, tasks, decisions, and sources | Refuses identifiers at capture, and refuses D2+ material and non-permitted source kinds, with the reason | `ManagerWorkspace.*` |
| 4 | Asks for this week's brief | Composes a **draft** from records; every line cites a record id; the banner says no model was used | `BriefService.draft_weekly_brief` |
| 5 | Reads, edits | Each edit is a new draft revision; history is kept | `BriefService.revise` |
| 6 | Accepts | Acceptance binds to the text hash the manager saw; a stale view cannot be accepted | `BriefService.accept` |
| 7 | Closes the app, reopens it | The accepted revision renders byte-identically | `test_create_review_save_close_reopen` |
| 8 | Exports | Proposal (Yellow) → manager approves exact file and content → recheck → write → receipt | `ActionBoundary` |

## Distinct states

The UI must never merge these states:

| State | Meaning | Evidence |
|---|---|---|
| Draft ready | A revision exists with status `draft` | Draft banner in the render |
| Accepted | The manager accepted this exact text | `accepted_by`, `accepted_at`, sha256 in the render |
| Saved | Persisted in the workspace database (always true once shown) | Reopen test |
| Exported | A file was written after approval | Receipt with the file's sha256 |
| Sent | **Not possible in the Personal Manager profile** | `send_email` is blocked (Red) |

## Failure and edge states

| Situation | What the manager sees |
|---|---|
| Identifier typed into a task | "Not stored — the Personal Manager profile does not keep identifying details (title: PHONE_NUMBER)…" |
| Confidential employer material added as a source | Refused, with an explanation that it needs an administrator-provisioned organization workspace |
| Card dragged to Completed | Refused; completion asks for evidence |
| Brief edited after acceptance | New draft; the previous accepted version stays current until the new one is accepted |
| Export approved, then the brief re-accepted | The approval is **stale**; nothing is written |
| File already exists with different content | Export **failed**; earlier file untouched |
| Crash mid-export | On restart: **succeeded** only if the file's hash matches, else **effect unknown**, and never re-run automatically |
| Restore from an older backup | Refused if it would discard newer changes; explicit discard keeps a pre-restore copy |
| Empty workspace | Each Mission Control section states that it is empty, and why |

## Known limits

- The privacy screen does not detect personal names. Onboarding must say
  so, and must not call any content "PHI-free".
- Only one person exists in a Personal workspace. The approval gate
  therefore stops errors and stale approvals; it does not provide independent
  review. Effects that need independent review set
  `requires_independent_review`, and self-approval of those is refused.
