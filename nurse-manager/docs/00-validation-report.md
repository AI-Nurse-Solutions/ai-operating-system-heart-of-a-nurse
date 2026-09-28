---
title: Validation of the Unified Build Path v0.2 (NM-001 baseline)
date: 2026-09-28
authorship: Substantially AI-generated (Claude Code) with human review pending
status: Draft for steward review
---

# Validation of the Unified Build Path v0.2

This report checks the *Nurse AI OS Manager Edition Unified Build Path*
(v0.2, 27 Sept 2026) against what exists today: this repository, the
separate `AI-Nurse-Solutions/florence-x` repository, and the upstream
sources the plan cites. It is the G0 baseline report (ticket NM-001).

**Verdict: the plan is sound and buildable, with nine corrections.** Its
sequencing works: the no-model weekly brief comes first, then the
installer spike, and AI is added only after the core works. Its safety
model (EDENA decides, JEV suggests, humans accept) matches the code
that already exists. Most corrections concern facts the plan assumed
rather than checked. Section 3 lists them.

## 1. What was checked, and how

| Item | Method | Result |
|---|---|---|
| This repo at `0390753` (main) | Read `naio-integrations/`, `naio-harness-v2/`, `naio-os/`, starter-kit Leader OS; ran test suites | 301/301 Integration Contract tests pass; repo suite 721 run, 15 fail + 1 error, **all from the missing optional `jsonschema` module in this container** (environmental, not code) |
| `AI-Nurse-Solutions/florence-x` at `09675bf` (main, read-only shallow clone) | Read `CLAUDE.md`, `BUILD_PLAN.md`, `packages/florence-core/…/schemas/` | Pydantic v2 core with `CandidateAction`, `EDENADecision`, `EvidenceBundle`; Python ≥ 3.12; Postgres/Redis/LangGraph/OPA targets |
| Hermes Desktop (W1, W2) | Fetched README, BUILDING.md, desktop guide, LICENSE on 2026-09-28 | Details in §2 |
| TypeSafe / JEV (W3, W4) | Fetched intro, quickstart, launch blog, privacy, terms on 2026-09-28 | Details in §2 |
| PR #25, issue #16 | GitHub API, this repo | Both closed and unrelated to this build; see correction 8 |
| `CODEX_START.md` (S2) | Searched both repos | Not found in either |
| Proposed design tokens | WCAG 2.x contrast computed | Orange fails as body text; see correction 7 |

## 2. Upstream claims

**Hermes Desktop.** Latest tag `v2026.9.24`; main at `9a0a162` on 2026-09-28.

- **Confirmed:** Electron with a React renderer and a Python backend. `hermes serve` exposes the `tui_gateway` JSON-RPC/WebSocket API.
- **Confirmed:** "Bundled" builds ship pinned CPython 3.14 and `uv`, so no Python install is needed. "Light" builds are remote-only.
- **Confirmed:** managed local backend, remote gateways, and Hermes Cloud.
- **Confirmed:** data lives in `HERMES_HOME` (default `~/.hermes`), outside the app bundle. That makes an isolated Nurse AI OS data home feasible.
- **Confirmed:** MIT license. No trademark clause was found in the files read, which does not prove there are none elsewhere.
- **Confirmed:** "Linux desktop legs are disabled." Windows ships as **MSIX, Windows 11 22H2 or later**. macOS ships as signed DMG/ZIP for arm64 and x64.
- **Confirmed, with a caveat:** desktop plugins exist, as single ESM files in `$HERMES_HOME/desktop-plugins/<id>/`. But upstream states **"A desktop plugin is not sandboxed: it runs inside the app with the app's own authority."** Whether plugins can register whole routes was not confirmed.
- **Update mechanism differs by OS:** `electron-updater` on macOS only; Windows uses App Installer or the Microsoft Store. The feed-details document returned 404.

**TypeSafe / JEV.**

- **Confirmed:** Choice and Score return probabilities and confidence. Noul returns a single 0–1 probability, with no separate confidence field documented.
- **Confirmed:** Bearer-key REST API (`POST /v1/systemone`) and a Python SDK.
- Access is **early access via a waitlist**. Pricing appears only in the blog post; the `/pricing` page returned 404.
- The privacy policy says prompts are not used for training, but **retention has no fixed period**.
- The terms say **"Do not submit any information … that you consider confidential or proprietary."** No HIPAA or BAA statement was found.

## 3. Corrections to the plan

1. **"Use the existing Python/Pydantic contracts" describes only one of two cores.** `florence-x` is Pydantic v2 (Python ≥ 3.12). This repository's working EDENA gateway, deliverable studio, privacy screen, and ADPIE workflow (`naio-integrations/`) use stdlib dataclasses on Python 3.11. Both are real, tested, and in use. NM-003 must reconcile **across repositories**, not only across type names. See `02-contract-map.md`.
2. **The duplicate-type pairs are cross-repo and wider than listed.** `CandidateAction`/`EDENADecision`/`EvidenceBundle` live in `florence-x`. `GatewayRequest`/`PolicyDecision` live here. The plan's `ActionIntent` was not found in either repo. There are **three risk-tier vocabularies**:
   - Florence-X: green, yellow, orange, red, red_blocked
   - Directive v1.1 here: green, yellow, orange, red-p, red-e
   - The plan's presentation labels: Green, Yellow, Red

   There are also **two data-class vocabularies**: `public`/`internal`/`phi_*` in Florence-X and `D0`–`D4` here.
3. **The plan says "no Orange tier is introduced"; both existing policies already have one.** The plan correctly defers to existing policy, so Orange stays. Presentation must map it (§4 of the contract map). **Orange is never shown as Green.**
4. **Under the authoritative gateway policy, a personal workspace cannot run any side-effecting action.** Yellow's ceiling is `recommend`, and Orange requires an authenticated org context. That is right for assistants, which may only draft or recommend in the Personal profile. But the plan's G2 "save → export" needs a stated rule for *human-initiated* local effects. ADR 0002 proposes one; it needs a steward decision under `GOVERNANCE.md` §3.
5. **Windows 10 is excluded by upstream packaging.** Windows ships MSIX for Windows 11 22H2+ only. If the manager cohort includes Windows 10 hospital-image laptops, the "Windows x64 first" default fails at G1. The G0 OS-inventory step must check this explicitly.
6. **"Thin customization via extension points" has a security cost.** Upstream plugins run with the app's full authority, so a Nurse AI OS page delivered as a plugin is not a containment boundary. The plan's rule already covers this ("backend policy must enforce the restriction"). The consequence to add: **the renderer and plugins must be treated as untrusted, and every effect must be decided in the Python backend.** That is how this build's action boundary works.
7. **The proposed orange `#C65B21` fails WCAG AA as text:**
   - 3.92:1 on the ivory canvas
   - 3.30:1 on sage
   - 4.27:1 for white text on it

   It stays as a non-text accent. A text-safe `#9E4617` is added (5.76:1 on ivory, 4.86:1 on sage). The other proposed pairs pass comfortably (9.2–11.9:1). `design/tokens.json` enforces this in tests.
8. **PR #25 and issue #16 cannot be the ones the plan means, at least in this repository.**
   - PR #25 here was an NP post-setup lane, merged 2026-07-15.
   - Issue #16 here was a link fix, closed 2026-07-13.

   If the plan meant `florence-x` numbers, verifying them needs that repo attached with API access, which this session did not have. The plan's own instruction applies: *do not assume their status*.
9. **The privacy screen does not detect personal names.** The plan's Personal profile relies on this screen plus the user's own restraint. The screen catches the following: MRN, SSN, DOB, room/bed, encounter dates, employee IDs, phone, email, and credentials. It will not stop a manager typing a colleague's name next to a performance concern. The product must say this plainly at onboarding, and never label content "PHI-free".

## 4. Other risks to carry into the plan

- **Eight weeks is optimistic.** Code-signing certificates (EV for Windows, Apple Developer ID and notarization) take calendar time and should be requested during G0, not G6. The two-core reconciliation (correction 1) is new work the envelope does not include.
- **Python version split.** Hermes bundles CPython 3.14, Florence-X needs ≥ 3.12, and this repo's CI runs 3.11. The manager core is written stdlib-only and tested on 3.11, so it runs on all three. Pick one bundled interpreter at G1.
- **JEV is not usable for anything beyond public or synthetic data.** The plan already restricts it, and the vendor's own terms reinforce that. Treat JEV as G4-optional with no schedule dependency.
- **Florence-X defaults to Postgres and Redis; the plan wants local SQLite.** Florence-X has a `Repository` protocol and in-memory store, so a SQLite binding fits its design, but nobody has written one yet.

## 5. What already exists that the plan can reuse

| Plan need | Existing asset |
|---|---|
| EDENA action boundary | `naio-integrations` `EdenaPolicyEngine` + `EdenaPolicyGateway` (fail-closed, tenant boundary, approval binding, hash-chained audit) |
| Draft-never-final rule | `DeliverableStudio` (draft banner, named-human review) |
| Capture-time data check | `PrivacyScreen` (recognizer-based, metadata-only findings) |
| Manager templates | `executive-brief`, `meeting-pack`, `project-charter`, `communication-plan` in `deliverable-templates.json`; `starter-kit/…/17-Leader-OS/Weekly-Brief.SKILL.md` (yellow tier, human gate) |
| Mission Control data zones | `DataZone` + private-reflection rule (`EDENA-PRIVATE-REFLECTION`) |
| Durable workflow | Florence-X LangGraph runtime + `EvidenceBundle` builder |

## 6. Recommendation

Proceed with the plan as sequenced, with corrections 3–7 folded in and
correction 1 resolved by ADR 0001. This PR starts G2 on the no-model
path, because G2 needs no upstream access, signing, or provider. G1 (the
installer spike) needs a Windows 11 and a macOS machine plus signing
identities, and should begin as soon as the OS-inventory question is
answered.
