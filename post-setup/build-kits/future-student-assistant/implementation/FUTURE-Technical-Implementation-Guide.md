# FUTURE Mission Control — Technical Implementation Guide

## Status and audience

This guide tells Hermes how to turn the verified build kit into the target application. It is not evidence that those steps have run. Record actual commands, versions, hashes, test output, and failures in phase receipts and the final handoff.

## 1. Verify and inventory before editing

1. Run `python3 tools/verify-build-kit.py --package .`.
2. Compare `RELEASE-MANIFEST.json`, `SHA256SUMS.txt`, and `SOURCE-INVENTORY.json`.
3. Treat `source/` as read-only; confirm no symlinks or write target can mutate it.
4. Inspect the baseline instead of assuming a framework. The supplied v2 baseline is a static HTML/CSS/JavaScript application with a loopback read-only server and browser storage; that is useful UI/state-machine source, not the target security or persistence architecture.
5. Discover actual Hermes health, model, capability, session, stream, cancellation, and tool-event surfaces. Do not invent endpoints.
6. Present the Activation Card and wait before copying, installing, migrating, probing, or starting services.

## 2. Copy-on-write target

Create a versioned work tree outside this package. Record its absolute path, source hashes, version-control state, runtime versions, dependency lockfile, and backup location. Never edit `source/baseline-application/`, `source/future-domain-pack/`, source archives, or canonical references.

Retain the baseline's useful accessible UI and offline mission semantics, but replace browser-only persistence and manual AI handoff with a local authenticated server, transactional durable store, real capability-driven adapters, and server-side secrets. Preserve an offline path when no model is available.

## 3. Required boundaries

- Bind only to `127.0.0.1`/`::1`; fail startup on wildcard or public binding unless a separate institutional product and threat model exists.
- Generate a unique install secret and use authenticated, `HttpOnly`, `SameSite=Strict` sessions; implement origin and CSRF protection for state changes.
- Keep secrets, provider headers, raw profile content, and database access server-side.
- Reject prohibited or unclassified input before persistence and without echoing it.
- Use parameterized statements, forward-only migrations, transactions, foreign keys, and durable event/audit IDs.
- Enforce pathway/context/space/mission ownership in repository/service queries, not only UI filters.
- Deny by default: connectors, schedules, background jobs, file execution, shell, public sharing, external sends/writes, agent recursion, permission widening, and raw Soul access.
- Production code must not import a test double or fall back to sample/canned AI output.

## 4. Durable domains

Implement the data model in `FUTURE-Architecture-and-Data-Model.md` and the normative schemas. At minimum persist accounts/sessions; approved derived profile revisions; workspace/pathway/context partitions; institutional-rule references; missions and loop stages; projects/tasks/milestones/notes/decisions/measures/reviews; artifacts and state transitions; evidence/references/claim links; approvals; EDENA decisions; power/workflow runs; agent sessions/events; consented structured memory; capability evidence/reviews/awards; audit events; backup/import/export jobs; and migration metadata.

Use immutable IDs and timestamps. Store current state plus append-only events. Recalculate dependent approvals, progress, and badges after edits/deletes. Soft-delete only when the UI says archive; complete deletion must remove primary, derived, indexed, cached, exported-staging, memory, and eligible audit payloads while retaining only the minimum non-content tombstone required for integrity.

## 5. First-run transaction

1. Create/authenticate the sole local owner.
2. Select Student, Assistant, or Bridge—never infer it.
3. Select protected spaces and explicit academic, clinical-placement, employment, personal, and community/public contexts.
4. Screen imports against strict schemas and prohibited-data rules.
5. Derive a Mission Profile in memory with field-level source, confidence, conflict, and approval group.
6. Show the whole proposed profile and deterministic Starter plan; allow edit, reject, skip, session-only, export, or approve.
7. Persist only approved derived fields. Never persist raw quiz answers or raw `SOUL.md`.
8. In one transaction create isolated workspaces, synthetic Starter missions, core launcher state, empty fifth slot, 18 inactive powers, 18 preview workflows, and P0 agents.
9. If any step fails, roll back and return to resumable onboarding without duplicate work.

## 6. Offline mission engine

Implement full CRUD and the five-stage transition table on the server. A stage transition checks ownership, active context, current revision, required fields, open blockers, EDENA/authority state, and optimistic concurrency token. Earlier-stage edits mark dependent approvals and artifacts stale. Evaluate can close, continue, modify, escalate, stop, or create a new linked cycle. Pause/kill stops future and running AI work but never destroys saved records.

Starter content has `synthetic=true`, visible provenance, and `achievement_eligible=false`. Adoption creates a user-owned revision but does not make prior synthetic events eligible.

## 7. Hermes adapter

Define a provider-neutral server interface for authenticated health, capability discovery, model list, session create/resume, incremental stream, cancellation, and structured tool events. Then implement only endpoints verified in the installed Hermes environment. Keep connection state time-bound and derived from recent authenticated checks.

Build the final instruction envelope in this order: platform/system boundaries; FUTURE governance; active pathway/context/authority/data ceiling; selected agent profile; mission-stage task; minimal user-approved derived preferences. Retrieved content stays untrusted. Agent selection must alter the actual server envelope and session metadata.

Store no model output until it has passed streaming completion/cancellation handling, data screening, and explicit save. Preserve raw provider errors only in redacted diagnostics. Tool events render separately from assistant text.

## 8. Evidence and memory

Evidence retrieval must store source identity, working locator, authority, publication/update/access dates, status, jurisdiction/scope, claim mapping, conflicts/corrections, relevance, uncertainty, reviewer, and expiry. Do not render a citation from model-provided text alone.

Memory is structured, consented, inspectable, editable, exportable, forgettable, deletable, purpose-bound, and expiring. Session-only is default. Prohibited/restricted content and raw Soul/quiz material never enter memory. Bridge school and employment memory remains partitioned.

## 9. Agents and permissions

Compile the frozen build-layer registry from `FUTURE-Agent-Team-and-Routing.md`. All agents install P0 Disabled. A permitted run is time-, mission-, context-, data-, tool-, token/cost-, retry-, and destination-bound; has a responsible user, human gate, stop condition, expiry, and receipt. No self-activation, delegation, recursion, hidden retry, background continuation, or external action. Stop and Kill must cancel a live stream and queued work.

## 10. Capability computation

Compile `config/FUTURE-Capability-Mastery-Criteria.v1.json`; reject unknown event, domain, criterion, evidence, review, and revocation types. A badge service evaluates eligible saved evidence—never clicks or AI confidence. Synthetic, deleted, expired, conflicted, self-asserted where review is required, or out-of-context evidence cannot satisfy a criterion. Retain the canonical Passport as a separate developmental view.

## 11. Testing and truthful readiness

Keep three distinct ledgers:

- full-stack functional/control tests defined by this kit;
- cross-cutting security, accessibility, recovery, and end-to-end scenarios; and
- all 136 canonical FUTURE compatibility checks.

Each execution record uses only `Not Run`, `Running`, `Passed`, `Failed`, `Blocked`, `Unsupported`, or justified `Not Applicable`, with timestamp, build hash, environment, command, expected/actual result, evidence locator, and reviewer. Specified, implemented, or documented is not Passed.

Use mocks only in automated test builds. Run production-mode tests, restart persistence, migration, backup/restore, deletion, offline, prompt-injection, secret, partition, accessibility/keyboard/mobile, cancellation, and clean-machine installation. Operational requires a genuine streamed Hermes response through the packaged UI.

## 12. Release contents

The final application must ship source; locked dependencies; migrations; production build; platform launchers; tests; `.env.example`; diagnostics; Guide; user/technical/security/privacy/backup/update/rollback/overlay-removal/uninstall docs; changelog; dependency/license record or SBOM; release manifest; full checksums; supported/tested OS versions; and known limitations. Verify a fresh extraction, install, launch, restart, backup, restore, update, rollback, overlay removal, and uninstall before handoff.
