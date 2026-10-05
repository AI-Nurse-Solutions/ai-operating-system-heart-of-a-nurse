# P2.3: verifiable local audit history

Implemented locally on 2026-10-04; not merged or released.

Subsequent integration: this implementation and the earlier local work now
coexist on `codex/integrated-manager`. The original audit worktree described
below remains preserved. The tentative reservation of `0015` was not used:
integration retained `0014_task_transitions` to preserve existing database
identities alongside `0014_classifier`. See
[`11-manager-integration-handoff.md`](11-manager-integration-handoff.md).

## What this means

New audit entries link to the entry before them. Changing an entry breaks
the link. The app also keeps its latest checkpoint outside the database,
so replacing only the database with an older copy is detected. A failed
audit insert rolls back the associated record change.

This is evidence of a consistent history, not a promise that records are
immutable. Someone able to replace both the database and its checkpoint
can defeat the local comparison. Keep a checkpoint on a separate disk or
under separate control for stronger comparison. Record contents are not
hashed into this chain: events use existing metadata fields only.

Older events remain unchanged and explicitly unchained. This implementation
does not claim to prove their past integrity.

## Scope and architecture

The implementation extends Store's existing transactions, event logging,
backup, and restore. It adds no service, telemetry, provider connection,
CLI command, or IPC operation. Human approval and privacy controls remain.
WeKnora and Paperclip remain open requests, not installed systems or
dispatched tasks. JEV's existing upstream integration is not activated.

Migration `0016_event_chain` adds event hashes, head state, and SQL guards
that refuse event edits, deletion, or an invalid append. Hash input is
canonical sorted UTF-8 JSON with format `nurse-manager-event-v1`, sequence,
timestamp, actor, event kind, record type, record ID, and previous hash.
Verification checks the chain, legacy boundary, head, and required guards.

`workspace.sqlite.audit-head.json` holds the latest separate checkpoint.
Transactions prepare a pending checkpoint before database commit and
finalize it afterward. Checkpoint files are replaced atomically after file
flush/fsync; POSIX parent directories are also fsynced. Missing, altered,
or pending checkpoints stop gated writes. A finalization error can happen
after a successful database commit: do not blindly retry the operation.
Preserve all files for human recovery review. No automatic repair command
is supplied. Physical power-loss behavior and platform-specific filesystem
durability have not been tested on real pilot laptops.

Backup verifies the copied snapshot against its checkpoint. If a concurrent
write makes the comparison uncertain, backup refuses and can be retried
when writes settle. Chained backups require their matching `.audit.json`
file on restore. Restore retains a source snapshot and excludes competing
live writers through its safety copy and replacement. Existing safeguards
against discarding newer records continue to apply. Legacy backups remain
usable without fabricating historical hashes.

Full-history verification runs during guarded writes. Its work grows with
history size, and cumulative append cost can grow quadratically. This
implementation prioritizes integrity; production-scale performance is not
established. Synthetic local timing evidence is retained with task logs.
One cloud Linux run averaged 1.27 ms per append with no prior events,
4.11 ms with 100, and 22.49 ms with 500 (ten appends per measurement).
These observations do not predict performance on pilot laptops.

## Workflow and preservation

Authority: the steward's approval of the Go recommendations and instruction
to continue the original plan, with Worktrunk/ECC/Addy controls preserved.
Reference workflow repository:
`AI-Nurse-Solutions/nurse-ai-os-integration-reference`, reviewed at
`83efb9d031ecdb7de76fc4989e98bf9f12e0eb86`.

Product base: `9ebd2134bf0354d8cab8635d340e45f8f48b0699`.
Task branch: `codex/audit-chain`.
Task worktree: `/workspace/ai-operating-system-heart-of-a-nurse.codex-audit-chain`.
Changes remain uncommitted. Official Worktrunk v0.80.0 created the isolated
worktree after inspection of hook/config sources. The release archive
SHA-256 was verified against both GitHub's asset digest and `sha256.sum`:
`532ce3ed5eecb1be274c925b5887f61671e2434a4ca2561b9a8ac9379dbba199`.
No global shell configuration or installer was run.

The earlier dirty checkout remains at
`/workspace/ai-operating-system-heart-of-a-nurse`. Its tracked diff, status,
and ten preserved untracked files were checked unchanged against the
preservation receipt in `/workspace/scratch/nm-before-audit`. Earlier
architecture, task, and approval work has not been combined into this
branch. Upstream now uses `0014_classifier`; this branch reserves `0015`
for reconciliation of the earlier local task-transition migration.

## Validation and review

Task contract, RED evidence, command output, and captured exit codes live in
`.task-evidence/` in the task worktree. Initial tests failed on the intended
missing audit protections. The initial RED shell wrapper did not retain
the unittest exit code; its failure output is preserved. Subsequent suite
failures and their logs are retained rather than represented as successes.

Independent security review found and verified fixes for malformed
checkpoints, missing audit guards, invalid state, restore races, database
rollback across the legacy boundary, and concurrent checkpoint changes
during backup. Its final disposition has no Critical or Required findings.
All 21 focused audit tests passed, including multiprocess append, tamper,
rollback, checkpoint failure, and concurrent backup/restore cases.

Regression fixtures now construct a genuine older database and simulate
concurrent upgrades using the actual transaction/checkpoint protocol. The
assistant-stop test waits for the committed state rather than racing the
provider-start signal; production stop behavior is unchanged. Targeted
control tests (16) and upgrade tests (46) passed. IPC validation passed:
159 envelopes checked by ajv plus strict TypeScript renderer checks.

Final full-manager regression: `python3 -m unittest discover -s
nurse-manager/tests` ran 471 tests in 125.175 seconds, passed with four
skipped, exit 0. Evidence: `.task-evidence/manager-final.log` and
`.task-evidence/manager-final.exit`. `git diff --check` also passed.

Exact-head CI for these uncommitted changes, signed packaging, notarization,
real-laptop/offline installation, release candidate, and pilot release are
NOT RUN. Existing repository and release gates remain in force. Nothing
has been pushed, merged, published, or deployed by this step.
