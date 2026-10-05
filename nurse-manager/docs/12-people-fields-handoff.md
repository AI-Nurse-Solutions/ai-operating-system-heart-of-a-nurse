# I-3: shared people-field rules

Implemented locally on 2026-10-04, uncommitted and not released.

## What changed

New workspaces use **me** as their owner label and no longer request a name.
New project/task owners, reviewers, decision makers, feedback sources, and
shared credit must use a fixed role or group label. Feedback and shared
credit forms offer choices. The backend also rejects custom labels if a
modified browser or terminal caller submits them.

Older labels remain unchanged. Mission Control counts stored people fields
outside the current choices and says they have not been automatically
verified or renamed. This count does not prove when a value was entered.
An existing workspace owner remains the owner for operational approval and
assistant controls. The new self label does not replace that identity.

Every view heading and the common onboarding/Help facts state the approved
rule, also recorded in the support guide:

> Use public or synthetic information and nonconfidential personal planning only. Do not enter patient details, names of other people, or confidential workplace information. Names are not automatically detected.

## Architecture and limits

`config/people-fields.json` defines `personal-people@1`, the fixed choices,
and the visible instruction. `people.py` validates shared domain captures;
services retain their existing privacy screen and transactional audit.
Case and surrounding space normalize to the canonical label. Empty reviewer
is permitted. Backend shared credit accepts at most six distinct labels,
separated by semicolons; the current form chooses one role or group.
Names, invalid types, markup, unknown choices, empty list items, duplicates,
and overlong lists are refused before writes.

`tools/gen_people_rules.py` generates the browser's choices and data rule.
Its `--check` runs in the focused tests, so changing only the generated
browser file fails validation. Config and renderer directories are already
included in the packaging spec; no additional dependency or packaging path
is introduced.

Mission Control's IPC response adds `people_fields`, containing the policy
version and an integer count of fields outside current choices. Generated
types and real envelope checks cover that response. The count scopes reads
to the current workspace and does not return the unrecognized values.
It scans the relevant capture fields on read; production-scale performance
has not been benchmarked. No telemetry or instrumentation is added.

No database migration, historical-label rewrite, or SQL role constraint is
introduced. Enforcement applies to supported domain writers. Direct database
editing is outside that boundary. Role labels do not authenticate people,
authorize effects, detect names in free text, or certify data as safe. Older
records may still contain names; review the exact AI preview or export
yourself. These limits do not expand the allowed personal data boundary.

## Workspace and preservation

Task branch: `codex/people-fields`.
Path: `/workspace/ai-operating-system-heart-of-a-nurse.codex-people-fields`.
Reviewed base/HEAD: `9ebd2134bf0354d8cab8635d340e45f8f48b0699`, checked
against current remote main. The completed integration changes are inherited
from their retained snapshot; HEAD does not identify the uncommitted code.
Worktrunk created the isolated branch with existing verified v0.80.0 tooling.
ECC/Addy scope, test evidence, fresh review, preservation, and release
boundaries were retained.

The preceding integration checkout remains preserved at
`/workspace/ai-operating-system-heart-of-a-nurse.codex-integrated-manager`.
Its tracked patch, status, and untracked implementation file hashes are
retained in `/workspace/scratch/nm-integrated-before-people`. Earlier original
and audit worktrees remain separate and intact. Temporary dependencies were
reused from the existing checkout; no package was installed by this step.

## Verification and review

Full commands, logs, exit receipts, task contract, and failures are retained
in `.task-evidence/` in the task worktree.

- Genuine RED evidence showed new custom names being accepted and recorded.
  GREEN focused people checks: eight tests, exit 0.
- Full Manager regression: 511 tests in 132.748 seconds, passed with four
  skipped, exit 0 (`manager-second.log` and `manager-second.exit`).
- Updated legacy upgrade probes: seven task-transition tests and 23 pilot
  tests, passed, exit 0. Named workspace/task/reviewer fields survive upgrade.
- Legacy reopen, backup, restore, audit preservation, and operational owner
  binding passed in the people tests.
- IPC: 173 real envelopes plus ajv and strict renderer typechecks passed,
  exit 0.
- Renderer browser journey: passed, exit 0, system Chromium; keyboard,
  names, record ids, sample states, narrow reflow, and themes retained.
- Local-app browser journey: passed, exit 0, system Chromium. Onboarding
  requests no name; a synthetic older owner produces the honest notice;
  a custom contribution option injected into the DOM is refused by the
  backend, and form text is preserved. Existing review, stop, and synthetic
  stand-in provider journeys continue to pass.
- Support-guide checks: 12 tests, passed, exit 0. Python compilation,
  generated rule/type checks, and diff whitespace checks passed.

Fresh-workspace fixtures now use allowed labels. Disclosure probes retain
distinct synthetic named legacy owners rather than treating the substring
`me` as a private name. Old-schema fixtures explicitly seed named legacy
fields and compare them after upgrade. Feedback malformed-input probes use
an allowed group so they continue to exercise their intended checks.

Independent review found two weakened fixture patterns and verified their
corrections. Final disposition: no Critical, Required, or Optional findings.
The first full regression and browser failures remain in the evidence
directory. One added browser probe initially read a previous refusal notice;
it now waits for the specific new response before checking it. No failed
test was skipped or its privacy requirement removed.

## Remaining gates and next feature

Shared project/task/decision/priority capture screens are next. Their
backend commands already exist and will reuse this validation. Richer
people labels or a changed data category require their existing behavior
and governance review; a role choice is not institutional authorization.

WeKnora and Paperclip remain open requests. No real provider, cloud account,
agent dispatch, new telemetry, or external data flow was enabled. Existing
human approvals, repository controls, clinical blockers, signing, and pilot
release gates remain. Exact-head CI for this uncommitted change, signed
packaging, real-laptop checks, and release are NOT RUN. Nothing was pushed,
merged, published, or deployed.
