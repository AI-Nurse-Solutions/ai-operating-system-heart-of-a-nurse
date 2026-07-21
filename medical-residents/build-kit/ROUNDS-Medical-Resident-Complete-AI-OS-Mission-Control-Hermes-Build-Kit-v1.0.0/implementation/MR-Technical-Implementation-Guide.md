
# Technical Implementation Guide

Inventory the supplied baseline before reuse. Preserve working UI/state-machine behavior only where it satisfies this contract. Final packaging requires locked dependencies, source, migrations, safe seed, `.env.example`, launchers, health diagnostics, tests, Guide, manifest, checksums, changelog, license/SBOM record, and recovery instructions. Claim an OS version only after a clean-machine test on that exact version.

Use transactional persistence with foreign keys, forward-only idempotent migrations, schema-version checks, atomic backup, and explicit tombstones. Seed only synthetic Starter content. Imports require schema/version/data-class/provenance validation and preview; incompatible Discover/Soul shapes, raw answers, cross-population records, and authority inflation fail closed.

Discover Hermes capabilities through authenticated endpoints. Support genuine health, models, sessions, incremental events, cancellation propagation, separated tool events, and truthful terminal states. Test doubles exist only inside automated tests. Without a live configured backend, production shows Setup required/unavailable and never simulates a response.

Execute unit, integration, end-to-end, security, no-PHI/no-real-case, evaluation/privacy, prompt-injection, accessibility, migration/restart, import/export, deletion, backup/restore, update/rollback, ROUNDS removal, uninstall, degraded-mode, source, routing, memory, streaming, cancellation, Kill, and clean-machine tests. Reconcile all 424 records with evidence paths and hashes.
