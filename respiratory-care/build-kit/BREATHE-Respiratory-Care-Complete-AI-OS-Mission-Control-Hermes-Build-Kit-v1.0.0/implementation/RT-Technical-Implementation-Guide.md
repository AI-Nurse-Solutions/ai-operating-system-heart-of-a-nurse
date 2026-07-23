
# Technical Implementation Guide

## Required stack characteristics

Use the supplied baseline only after inventorying it. Preserve the working UI and state machine where safe. The final package must include locked dependencies, source, migrations, safe seed, `.env.example`, launchers, health diagnostics, tests, Guide, manifest, checksums, changelog, SBOM/dependency record and recovery instructions. Claim operating-system support only after a clean install on that exact version.

## Persistence and migrations

Use a transactional local database with foreign keys, forward-only idempotent migrations, schema-version checks and atomic backup. Seed only approved synthetic Starter content. Imports require schema/version/data-class validation and a preview. Upgrades must preserve unrelated and user-created work.

## Hermes adapter

Discover capabilities through authenticated endpoints. Support real health, models, sessions, incremental streaming, cancellation propagation, terminal states and separated tool events. Keep provider secrets on the server. Test doubles are permitted only in automated tests; production must show Setup required or unavailable when the backend is absent.

## State machines

- Mission: Draft → Active → Paused → Completed → Reopened → Archived/Deleted.
- Loop: Assess → Diagnose/Define → Plan → Implement preparation → Evaluate, with explicit revisions and invalidation.
- Artifact: exact eight-state lifecycle in the governance contract.
- Power: Available Inactive → Previewed → Approved inactive → Active bounded → Paused → Removed; one run returns to inactive.
- Agent: P0 → one approved P1/P2 run → terminal receipt → P0.

## Verification

Execute unit, integration, end-to-end, security, no-PHI/no-real-case/no-device, prompt-injection, accessibility, migration, restart, import/export, deletion, backup/restore, update/rollback, BREATHE removal, uninstall, degraded-mode, source, routing, memory, streaming and cancellation tests. Reconcile all 424 rows with evidence paths and hashes.
