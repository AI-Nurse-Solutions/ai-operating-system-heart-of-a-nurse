---
title: "ADR 0001: Where the manager core lives"
status: Proposed — needs steward decision (GOVERNANCE.md §3, architecture)
date: 2026-09-28
---

# ADR 0001: Where the manager core lives

## Context

The plan says to build on the "existing Florence-X professional core"
using its Pydantic contracts. There are two cores.

**`florence-x` (separate repository).**

- Pydantic v2, Python ≥ 3.12, `CandidateAction`/`EDENADecision`/`EvidenceBundle`.
- Designed for clinical signal → workflow → EDENA, with Postgres, Redis, and LangGraph.

**`naio-integrations` (this repository).**

- Stdlib dataclasses, Python 3.11.
- A working EDENA gateway on Directive v1.1 semantics (D0–D4, red-p/red-e, data zones, approval binding).
- The deliverable studio, privacy screen, and example workspace that Mission Control packets already ship.

The manager edition needs to run locally without Postgres or Redis. It
must not create "duplicate production records merely to fit upstream
APIs".

## Decision (proposed)

1. The manager records and services live in `nurse-manager/` in this
   repository. They **reuse** `naio-integrations` for policy, privacy, and
   banners. They are stdlib-only, so they run on 3.11, 3.12, and the 3.14
   interpreter Hermes Desktop bundles.
2. The manager core owns **manager records only**: projects, tasks,
   decisions, sources, priorities, artifacts, and local actions. It does not
   own mission lifecycle or clinical workflow state.
3. Florence-X alignment happens through an adapter (build step 2.11). It maps
   `actions` ↔ `CandidateAction`/`EDENADecision` and receipts and events ↔
   `EvidenceBundle`, with a round-trip test against the `florence-x`
   schemas. The adapter lives wherever the steward decides the
   integration point is. It must not fork either schema.
4. Storage is SQLite behind `Store`. A managed-database binding must
   implement the same service contracts.

## Consequences

- G2 is buildable now with no new infrastructure.
- There is a real risk of a third vocabulary. It is mitigated by the
  contract map, which the adapter must satisfy, and by reusing the
  Integration Contract enums rather than redefining them.
- If the steward prefers the manager core inside `florence-x`, it moves
  as a package. The core has no Pydantic dependency to reconcile, and its
  SQLite-specific SQL (`AUTOINCREMENT`, `BEGIN IMMEDIATE`, the backup API)
  is confined to `store.py` and the migration file.
