
# Respiratory Care Professional BREATHE Architecture and Data Model

## Local trust boundary

Bind only to `127.0.0.1` or `::1`; authenticate the owner; keep secrets server-side; use server-owned sessions, CSRF protection and Origin/Host validation. Store durable state in a local transactional database with forward-only migrations. Keep attachments outside the web root and scan/admit them before persistence. Never place patient information, raw `SOUL.md`, raw quiz answers, credentials, tokens or rejected payloads in logs.

## Logical layers

1. Accessible UI: My BREATHE, Missions, five workspaces, Evidence, Equipment Learning, CIRCLE Coordination, Capabilities, Agent Console, Guide and Recovery.
2. Server services: authentication, data admission, context isolation, mission state machine, artifact lifecycle, source registry, consent memory, capability evaluation, export/import and recovery.
3. Provider adapter: capability-driven Hermes integration and optional OpenAI-compatible adapter; health, models, sessions, streaming, cancellation and tool-event separation.
4. Persistence: profile, workspace, mission, cycle, task, note, measure, source, artifact, decision, approval, external reference, memory, evidence, badge, agent charter/run/event/receipt, migration and backup records.

## Invariants

- Foundation records live under `resp_breathe.*` and BREATHE overlay records under `resp_breathe.*`; overlay records reference but never duplicate base records.
- Each mission binds one task hat, workspace and operational context.
- Data classification occurs before persistence and before provider/agent use.
- Downstream stages and approvals are invalidated by material upstream/context/authority/data/source changes.
- All 24 powers remain inactive after installation.
- Agent state is P0 unless one exact, expiring P1/P2 charter is active.
- The app has no clinical or general external-action executor.

## Core entities

`MissionProfile`, `Workspace`, `Mission`, `MissionCycle`, `StageRevision`, `Task`, `Measure`, `SourceRecord`, `Artifact`, `ArtifactRevision`, `Decision`, `Review`, `ExternalReference`, `MemoryItem`, `CapabilityEvidence`, `BadgeAward`, `AgentCharter`, `AgentRun`, `AgentEvent`, `RunReceipt`, `CheckpointReceipt`, `BackupSet` and `Migration`.

Every durable record carries stable ID, version, owner, context, data class, created/updated time, provenance, lifecycle state, review/expiry and deletion behavior. Professional fields separately represent user-entered, source-linked, last-verified and verification-needed states.

## Backup and deletion

Backups are atomic, versioned, encrypted when supported and never broaden the admitted data class. Restore is tested into an isolated path. Deletion removes database rows, attachments, indexes, memory, exports and pending agent state according to a visible receipt. Rejected payloads never require later deletion because they were never retained.
