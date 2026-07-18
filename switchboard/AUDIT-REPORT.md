# Nurse AI OS Switchboard Preview Audit Report

**Audit date:** 2026-07-17

**Baseline:** `origin/main` at `ed41b5d3bcc72ac24f86df3990f2380764e294be`

**Release posture:** browser-local, non-installing, PHI-prohibited architecture preview

## Current decision

**Approved for publication as a non-executable architecture preview.** Independent architecture/EDENA, security/correctness, and UX/accessibility/release reviews found no unresolved P0–P2 implementation defect after the accepted corrections and regression evidence below.

This candidate does not authorize Hermes profile composition, installation, credential verification, organizational deployment, connectors, PHI, EHR access, external action, background agents, or clinical use.

## Independent review history

The first independent architecture, security, and UX/release review requested changes. A later review of the corrected candidate found one P1 architecture issue, one P1 import issue, and six P2 issues. Every accepted finding below has now been corrected and receives deterministic regression coverage.

| Finding | Severity | Current disposition |
|---|---:|---|
| Role/context/capability rules were declared but not enforced | P1 | Fixed: creation and import normalization reject incompatible composition; supporting roles are disabled. |
| Working Authority Card implied EDENA evaluation and granted autonomy | P1 | Fixed: renamed Dashboard Configuration Posture; always `EDENA: Not evaluated` and `A0 · no action`. |
| Registry schema allowed A1/A2 despite A0 preview posture | P1 | Fixed: registry schema now requires `autonomyCeiling: A0`; mutation regression test added. |
| Imported session assignments could be resurrected | P1 | Fixed: import now expires reload-bound sessions and elapsed fixed windows before replacement; browser import regression added. |
| Context isolation wording exceeded actual shared-state behavior | P1 | Fixed: disclosures say separation is navigational and metadata-level, not a secure sandbox. |
| Fixed-window and role composition invariants were incomplete | P1/P2 | Fixed in deterministic runtime normalization; structural schema explicitly identifies runtime-only invariants. |
| State schema could be mistaken for the complete import contract | P2 | Fixed: schema and architecture label it structural; tests prove runtime rejects noncanonical duration, dangling active references, and duplicate IDs. |
| Obvious `Patient Jane Doe` titles passed the heuristic | P2 | Fixed: generic local titles containing `patient` or identifier labels are rejected; disclosure still says checks are not exhaustive DLP. |
| Complete legacy objects with malformed timestamps migrated | P2 | Fixed: legacy `updatedAt` must be canonical ISO before migration. |
| Legacy migration could accept partial objects or discard local drafts | P2 | Fixed: exact legacy shape, canonical timestamp, normalized current-state merge, and persistent dismissal/completion marker. |
| DISCOVER/FUTURE draft taxonomy could imply stable-package equivalence | P2 | Fixed: draft capability paths are null and descriptions explicitly distinguish the proposed universal taxonomy from existing packages. |
| Absolute no-network wording ignored font requests | P2 | Fixed: claim narrowed to no application API/model calls; Google Fonts are disclosed and HTML URLs are tested. |
| Context-adapter/local-capability drafts had no application path | P2 | Fixed: local creation is limited to roles and functional assignments. |
| Active dashboard styling still targeted removed `aria-current` | P2 | Fixed: CSS now styles `aria-pressed="true"`; source and browser behavior are covered. |
| Dialog close controls could shrink below 44×44 px | P2 | Fixed: non-shrinking 44×44 CSS; 320 px browser measurements added for both dialogs. |
| Custom dialog fallback was incomplete or under-tested | P1/P2 | Fixed: fallback is viewport-fixed with explicit modal semantics and visual backdrop, all background siblings become inert, prior inert/ARIA state is preserved, focus is contained and restored, and every contract element is exercised in browser CI. |
| Corrupt local storage/reset could announce unverified success | P2 | Fixed: malformed data cleanup and verified removal failures are browser-tested. |
| Import replacement lacked direct backup guidance and size precheck | P2 | Fixed: pre-read 250 KB limit plus replacement confirmation directing users to Export JSON first. |
| Publication rollback procedure was missing | P2 | Fixed: `ROLLBACK.md` covers revert, Pages verification, integration cleanup, package integrity, evidence, and browser-state limits. |

## Machine-enforced governance posture

- Registry entries require `edenaStatus: not-evaluated` and `autonomyCeiling: A0`.
- Local roles and assignments remain `Local Draft · Not NAIO-reviewed` and create no authority.
- One primary role is permitted per preview dashboard.
- Supporting-role composition is unavailable until compatibility and authority-intersection rules are independently validated.
- Role/context and role/capability compatibility are enforced in both creation and import normalization.
- Assignment state is fail-closed across load, import, elapsed time, explicit end, and reload-bound sessions.
- Selection verifies no license, certification, employment, enrollment, appointment, assignment, mandate, or institutional authority.

## Validation evidence

Latest completed local validation before the final re-review:

- Full repository Python suite: **216 tests passed**.
- Switchboard Python suite: **26 tests passed**.
- Draft 2020-12 AJV validation: **23 current registry entries passed**; an A2 mutation was rejected.
- Browser test: route 200, malformed-storage cleanup, legacy dismissal/completion markers across reload, viewport-fixed fallback with role/ARIA/backdrop/all-sibling inertness/prior-state restoration/focus trap and return, native dialog containment and focus return, selected styling persistence, Cancel/close, context filtering, dashboard creation and switching, import replacement, imported-session expiry, 320 px touch targets, 390 px overflow, reset failure, and clean console.
- The final browser evidence suite passed **five consecutive runs** after asynchronous import assertions were changed to wait for the actual state transition.
- JavaScript syntax checks passed for model, UI, Setup Helper, schema test, and browser test.
- Workflow YAML parsed successfully.
- `git diff --check` passed.
- Protected role-package/download roots have no diff against `origin/main`.

## Structural schema boundary

`schema/switchboard.schema.json` is a portable structural schema, not the sole import validator. Portable JSON Schema cannot fully express exact timestamp arithmetic, property-level uniqueness across array objects, or active-ID referential integrity. Import success also requires `normalizeState()`, and CI explicitly demonstrates that malformed-but-structural examples are rejected by that runtime gate.

## Release gates

- [x] PHI and confidential records prohibited; heuristic limitations disclosed
- [x] No credential or institutional-authority claim
- [x] No installer, connector, cron, memory, agent, or external action
- [x] EDENA remains not evaluated and autonomy remains A0
- [x] Compatibility and assignment invariants fail closed
- [x] Browser interaction, fallback, responsive, and storage tests
- [x] Registry/schema/runtime drift tests
- [x] Package bytes and public package paths untouched
- [x] Rollback runbook present
- [x] Final post-fix independent findings closed with deterministic regression evidence
- [ ] Release commit, deployment, and live-domain verification

## Deferred executable-composer gates

A future executable release remains blocked until disposable-profile tests prove profile isolation, additive composition, task/data classification, EDENA evaluation, digest-bound approval, explicit artifact transfer, update, rollback, wrong-context handling, revocation, and independent security/governance review.
