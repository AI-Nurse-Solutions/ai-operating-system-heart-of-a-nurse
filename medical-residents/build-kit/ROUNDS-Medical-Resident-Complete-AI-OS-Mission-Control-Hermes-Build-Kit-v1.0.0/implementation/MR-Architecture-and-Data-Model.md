
# Architecture and Data Model

## Required runtime

1. Accessible local UI bound only to loopback.
2. Authenticated server layer owning sessions, CSRF/Origin/Host checks, state transitions, imports, exports, and diagnostics.
3. Transactional local database with foreign keys, idempotent migrations, version checks, tombstones, and atomic backup.
4. Data-admission service before echo, persistence, logging, indexing, memory, model, agent, tool, backup, or export.
5. Provider-neutral Hermes/AI adapter with real health, capabilities, models, sessions, streaming, cancellation, and terminal-state truth.
6. Locked dependencies, license/SBOM record, launchers, updater, rollback, ROUNDS removal, and uninstall.

## Local at-rest protection

Place the application data root, database, permitted attachments, logs, exports, temporary files, and backup staging under an owner-only directory. On POSIX, directories must be mode `0700` and files `0600` (subject to a stricter platform policy); on Windows, apply a current-owner/System-only ACL and remove broad inherited access. Verify effective permissions after install, restore, update, rollback, and restart on every claimed platform. Do not claim application-layer database encryption unless it is actually implemented and tested.

Backups must be encrypted either by a verified platform-encrypted destination or a tested encrypted archive whose key is stored separately from the backup. Secrets, raw profile identity, rejected payloads, session material, provider credentials, and encryption keys never enter a backup. If encrypted backup cannot be provided, the backup action is visibly unavailable—not silently downgraded. Clean-machine tests must prove owner-only paths, separate-key handling, restore into an isolated owner-only path, and zero prohibited canary residue.

## Isolation keys

Every durable row is scoped by owner, `medical_resident`, partition, record scope, mission, primary/secondary hats, and deployment context. Queries fail closed when a key is missing. Switching program, specialty, site, rotation, task, hats, scope, partition, source, model, agent, content, recipient, or destination invalidates affected cached context and approvals.

The five record scopes are logical filters inside one home. Institution-declared partitions remain disabled and have no route, model, connector, or store in the personal target. Whole-life material is technically unavailable to program, employer, evaluation, badge, QI/research, analytics, and institutional exports.

## State machines

- Mission: Draft → Active → Paused → Completed → Reopened → Archived/Deleted.
- Loop: Assess → Define → Plan → Implement preparation → Evaluate; backward revision preserves history and invalidates downstream approvals.
- Power: Available Inactive → Previewed → Approved Inactive → Active Bounded → Paused → Removed.
- Agent: P0 → requested/scoped/previewed/synthetic-tested → one approved P1/P2 run → human review → accepted/rejected → archived/expired/revoked → P0.
- External action vocabulary: Off → Drafted → Previewed → Human-Approved-One-Run → Staged → Human-Released → Confirmed-or-Failed → Closed. It is reference-only: no transition beyond Off, executor, connector, destination, imported attestation, or institution activation is shipped.

## No authority by data model

`resident_status`, PGY, title, source links, user-entered attending names, and supervision fields are claims with provenance—not official attestations. The personal profile cannot represent `institution_verified` or activate an institution-approved context.
