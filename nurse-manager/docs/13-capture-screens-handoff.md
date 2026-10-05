# Personal-workspace capture screens handoff

2026-10-04. Implemented locally on `codex/capture-screens`, based on
`9ebd2134bf0354d8cab8635d340e45f8f48b0699` plus the preserved, completed
people-fields implementation. Changes remain uncommitted; no upstream CI,
merge, publication, or release completion is claimed.

## What a manager can do

Open **Add work** in the local app to add a project, task, decision, or one
to three priorities for the current week. Projects link to their existing
dashboards. Tasks and decisions use the same record ids as the other views
and briefs. New owner, reviewer, and decision-maker fields use the existing
fixed role choices. They do not grant authority to execute an action.

**Change a task** supports moving, blocking, pausing, completing, reopening,
and withdrawing. Completion requires evidence; reopening and withdrawal
require a reason. The backend checks the reviewed status inside the write
transaction. Completed or withdrawn work must be reopened before other
changes. These checks compare status; they do not detect every concurrent
edit that leaves the status unchanged. Refresh before acting on potentially
outdated task details.

Priority replacement requires confirmation and a workspace/week-scoped hash
of the reviewed list, checked under the write lock. Refusal retains the
proposal. Explicit **Refresh records** preserves proposed priorities,
updates the current list/hash, and requires new confirmation. Saving an
unrelated form retains unsaved priority text and its earlier hash, so it
cannot silently approve an outdated replacement.

Privacy, role, invalid-input and stale-state refusals retain typed form text.
Busy saves disable capture controls. If a save succeeds but refresh fails,
only the saved form clears and the notice says it was saved. If the reply
is lost, the result is unknown: capture writes stay disabled across
navigation until a successful explicit refresh. Check whether it saved
before trying again. No automatic retry or idempotency guarantee is added.
Navigating away closes unsaved forms; ordinary refusal/redraw preserves them.

## Boundaries and implementation

The browser uses the existing launch token, Origin, POST, body and workspace
checks. Selected record roles use separate request fields; page-supplied
operational owner/actor/approver identities remain ignored. Shared domain
writers retain data screening, role enforcement, audit, and transition rules.
Oversize capture fields are refused rather than truncated. The development
host serves the new read view without capture forms or write admission.

The new `capture` read model assembles projects, tasks, decisions, priorities,
and the priority hash on one snapshot. The renderer is a thin module consuming
the generated IPC types. No dependency, database table, migration, cloud
service, telemetry, effect approval, or export capability was added.

## Verification

Evidence is retained locally in `.task-evidence/`, including earlier failures.

- Genuine RED: two authenticated project-capture probes returned 404 before
  write admission; GREEN: both passed after the backend change.
- Focused HTTP: five tests passed; independent reviewer also ran all five.
- Full Manager regression: **516 tests ran, four skipped**, passed, exit 0
  (`capture-manager-final-second.log/.exit`). The first full run found a
  missing date/week argument in the dev-host comparison fixture; corrected
  without removing the command-coverage assertion.
- IPC: **174 real envelopes** passed ajv and strict TypeScript checks,
  including the new read model and imported capture renderer.
- Existing local-app and renderer browser journeys passed, exit 0, with
  system Chromium. Read-only capture and 320px reflow were added to the
  renderer journey.
- New capture browser journey passed, exit 0
  (`capture-browser-durable.log/.exit`): empty workspace, keyboard capture,
  same task/project ids across views, decision cited in an explicitly accepted
  brief, all six task changes, stale task/priority refusals, forged role and
  identifier refusal, unsaved priorities/hash retained across an unrelated
  save, interrupted reply, unknown guard across navigation, failed refresh,
  busy save navigation recovery, narrow view, and actual process close/reopen
  with records preserved. Earlier test setup/cleanup failures remain logged.
- Generated types/people rules, Python compilation, syntax and whitespace
  checks passed. Independent ECC/Addy review has no remaining required findings.
- Parent preservation: exact tracked patch/status and 21 untracked file
  hashes remain unchanged. Earlier source checkouts were not edited.

The browser journey is wired into npm and the existing browser CI job;
remote/exact-head CI is NOT RUN. This task was tested from Python source,
not from a newly packaged binary.

## Next step and remaining gates

Next is packaging the combined implementation into a macOS download and
verifying that packaged app. A signed pilot candidate and an offline first
launch on actual pilot Macs still require the existing signing identities,
release evidence and real hardware checks. No download is represented as
ready for pilot distribution by these source checks.

WeKnora and Paperclip remain open requests. No installation or dispatch was
performed. Human approval, privacy boundaries, repository controls,
institutional authorization, clinical blockers and release gates remain.
