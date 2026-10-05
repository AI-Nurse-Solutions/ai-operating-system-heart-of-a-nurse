# Completed Manager work: integration handoff

Date: 2026-10-04. State: local implementation; uncommitted, not released.

## Result in common language

Earlier task, capture, approval, and policy safeguards now work together
with the completed audit-history protection in one branch. Previously,
these changes lived in two separate checkouts. Combining them prevents the
next feature from accidentally omitting one set of protections.

Existing task databases and backups can still open. Withdrawn tasks,
reasons, earlier evidence, and audit entries survive upgrade and restore.
Audit history from before hashing remains explicitly unchained.

## Exact workspace and scope

Branch: `codex/integrated-manager`.
Path: `/workspace/ai-operating-system-heart-of-a-nurse.codex-integrated-manager`.
Reviewed base/HEAD: `9ebd2134bf0354d8cab8635d340e45f8f48b0699`.
Remote `origin/main` was checked and still names that commit.
All implementation changes are uncommitted; this HEAD does not represent
the changed code for exact-head CI purposes.

The steward authorized continued implementation. Worktrunk v0.80.0 created
the isolated worktree after configuration/hook inspection using the
verified binary retained from the audit step. ECC's task contract,
test evidence, fresh-context review, and Addy's quality/control checks were
applied without installing another runtime or hook stack. Reference workflow
repository: `AI-Nurse-Solutions/nurse-ai-os-integration-reference` at
`83efb9d031ecdb7de76fc4989e98bf9f12e0eb86`.

The earlier dirty checkout and completed audit checkout remain untouched:

- `/workspace/ai-operating-system-heart-of-a-nurse`
- `/workspace/ai-operating-system-heart-of-a-nurse.codex-audit-chain`

Tracked diffs, status receipts, and inherited untracked implementation files
were compared against retained snapshots. Evidence:
`.task-evidence/preservation.log`. Existing dependencies were reused through
a task-owned temporary symlink; no packages or browser binaries were
installed by this task.

## Reconciliation decisions

The shared HTTP transport now retains upstream classifier read routes and
their argument validation. Production still owns token, origin, method,
write allowlist, and owner binding; the development host remains read-only.
IPC commands, schema, real envelope fixtures, and generated types cover
both classifier and capture/task commands. No new browser capture capability
is implied by adding terminal commands.

The combined action boundary retains upstream classifier holds plus the
earlier transactional approval, execution, and settlement checks. The
record-writer register covers all migrated tables. EDENA policy version
1.0.1 retains named held approval checks from the earlier authorized work.
The reviewed audit Store implementation is unchanged except for a comment.

Migration identities are their full stems. Both historical names survive:
`0014_classifier` and `0014_task_transitions`. The latter migration is
byte-identical to the original implementation. `0016_event_chain` remains
unchanged; `0015` is unused. An initially attempted task migration rename
to `0015` was rejected after independent review proved it prevented opening
original task databases. Keeping the historical identifier fixes that
without an alias, a history rewrite, or weaker unknown-schema checks.

Upgrade tests exercise upstream, the audit branch, and the original task
database. Restore tests exercise a genuine original-schema backup. They
compare retained records and withdrawal history, check foreign keys and
anchors, and verify later audit appends. Adding an earlier missing migration
to a database already at audit version `0016` preserves its existing chain
and anchor.

Regression fixture fixes preserve the tested controls: browser boundary
probes now include all upstream classifier writes and test that a synthetic
key stays out of arguments; legacy event comparisons check every old field
and explicitly require new hashes to be NULL. The pre-classifier sample
fixture includes task transitions needed by its current writer and asserts
that classifier tables are absent before upgrade. Separate fixtures cover
upstream databases without task history.

## Evidence and review

Task contract and logs/exits are in `.task-evidence/` in the task worktree.
Initial RED checks detected the missing task migration. That provisional
identifier was subsequently corrected as described above. The first full
Manager run exposed omitted classifier boundary fixtures and old-schema
fixture assumptions; all failure output remains in `manager-first.log`.
The fixture corrections do not remove assertions or skip failed checks.

- Four integration upgrade/restore checks: PASS, exit 0.
- Seven task-transition checks: PASS, exit 0.
- 32 app/HTTP boundary checks: PASS, exit 0.
- Integration suite: 308 tests, PASS, exit 0.
- IPC schema and strict renderer types: 173 real envelopes, PASS, exit 0.
- Renderer browser journey: PASS, exit 0, system Chromium.
- Local-app browser journey: PASS, exit 0, system Chromium; all synthetic
  providers are stand-ins, not live accounts.
- Python compilation, generated IPC type check, and full diff whitespace
  check: PASS.
- Final full Manager regression: `python3 -m unittest discover -s
  nurse-manager/tests` ran 503 tests in 131.729 seconds, PASS with four
  skipped, exit 0 (`manager-final.log` and `manager-final.exit`).

Independent review found the original-schema compatibility issue, verified
the corrected migration identity and four upgrade/restore tests, and cleared
it. Final disposition: no remaining Critical, Required, or Optional findings.
Parent verification independently ran the applicable checks above.

## Boundaries and next step

WeKnora and Paperclip remain open requests. No real provider was connected,
no new data category admitted, and no telemetry or external operation added.
Human approval, privacy rules, clinical P0 blockers, institutional authority,
repository review, and release gates remain intact. The local checkpoint
limitations and human recovery requirements in the audit/support documents
still apply.

Signed packaging, notarization, real-laptop/offline checks, exact-head CI
for this uncommitted change, pilot adoption, and release are NOT RUN.
Unrelated root/static-site tests were not rerun; prior root failures remain
documented in the steward decision record. No push, merge, publication,
installation on pilot hardware, or release was performed.

Next authorized feature: controlled role labels in shared backend writers
for new personal-pilot people fields, preserving existing records and
stating their legacy status honestly. Capture screens follow the shared
backend rule. No approval is requested again for that already-approved work.
