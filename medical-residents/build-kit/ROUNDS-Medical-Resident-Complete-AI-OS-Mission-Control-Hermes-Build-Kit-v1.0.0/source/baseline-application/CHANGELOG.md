# Changelog

## 2.0.0 — 2026-07-20

### Added

- Unified Nurse AI OS Mission Control for multiple healthcare, learning, leadership, research, business, and community roles.
- Role Constellation with primary, supporting, emerging, and contextual relationships.
- Versioned `NAIO-DISCOVER-PACKET-ADAPTER-1` import, preview, apply, clear, strict schema, and deidentified example for derived goals, priorities, working preferences, role goals, workflows, capabilities, AI boundaries, and governance defaults.
- Versioned `NAIO-SOUL-PROFILE-ADAPTER-1` import, preview, apply, restore, and clear flow.
- Neutral personalization state while the redesigned Soul Quiz is finalized.
- Five-stage Assess → Define/Diagnose → Plan → Implement → Evaluate Mission Loop.
- Mission pause, revision, iteration, status, retention, and artifact-state controls.
- Explicit sandbox lifecycle from exploration through evaluated outcome.
- Synthetic sample mission demonstrating the complete loop.
- EDENA Green, Yellow, Orange, Red, and Unclassified advisories.
- Personal Edition advisory behavior and clearly labeled Institutional policy preview.
- Evidence-based Capabilities & Mastery page with four noncredential development levels.
- Manual mission-stage Hermes handoff with review acknowledgment.
- Expanded first-run onboarding and embedded Guide.
- Dedicated Hermes integration program and capability-state contract.
- Privacy, security, backup, update, rollback, uninstall, version, and license documentation.

### Changed from 1.0

- Expanded from a Healthcare Research & Innovation Leader companion into a unified multi-role Nurse AI OS workspace.
- The earlier DISCOVER research pack is preserved under `base-pack/` as an optional specialization, not the universal core or a required dependency.
- Replaced the earlier quiz-first personalization model with a versioned derived Soul Profile adapter; the 12-question experience is now explicitly provisional.
- Expanded safe profile backup to support roles, derived Discover and Soul settings, locally retained non-sensitive missions, and capability evidence.
- Reframed Hermes integration as generic Nurse AI OS registration with manual reviewed handoff, rather than requiring a research-only lane.

### Security and governance notes

- Browser `localStorage` and exported backups are unencrypted.
- PHI, confidential institutional or research information, sensitive personal data, credentials, and secrets remain prohibited.
- No background work, automatic prompt transmission, result retrieval, official-system write, or external execution is added.
- Role selections, Discover/Soul results, artifact labels, and badges do not verify authority or competence.
- Institutional policy preview is not tamper-resistant enforcement.

### Migration

Version 2.0.0 uses storage key `discover.nurse-ai-os.mission-control.v2` and backup schema `DISCOVER-MISSION-CONTROL-PROFILE-2`. Keep a version 1 export and folder for rollback. Do not force-import an unsupported version 1 profile; recreate or migrate only through a reviewed, schema-aware process.

### Known limitations

- Static local application; no Hermes API or live synchronization.
- Manual copy/download/paste handoff only.
- Local pattern checks cannot detect every identifier, secret, or unsafe instruction.
- Soul Quiz philosophy and derived adapter contract may evolve in a future version.
- Institutional identity, authorization, audit, encryption, retention, and policy enforcement are outside this package.
- Capability evidence is user-maintained and not independently credentialed.
