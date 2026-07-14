# Govern the Project in the Open

**File:** `GOVERNANCE.md`

This document states who decides what in the Nurse AI OS project, and what happens to ownership and authority as the project's institutional structure matures. Governance of the code is deliberately separate from governance of the brand and separate from governance of certification; the three are stated separately below so no one has to infer the boundaries.

---

## 1. Stewardship

The project is currently founder-stewarded. Robert Domondon holds final decision authority over project direction, releases, maintainer appointments, and the contents of the policy files at the repository root (`TRADEMARKS.md`, `SAFETY.md`, `CONTRIBUTING.md`, this file).

Maintainers are appointed by the steward and hold merge authority within their component areas. Maintainer status is earned through sustained, high-quality contribution and can be relinquished or revoked. Until a separate `MAINTAINERS.md` is published, Robert Domondon is the sole maintainer of record.

## 2. What the Open License Governs

Apache License 2.0 (code) and CC BY 4.0 (documentation) govern everyone's rights in the software and docs. Those rights do not depend on this governance structure and are not revocable by it. Anyone may fork this project at any time under the license terms; the fork simply may not carry the project's name or marks (`TRADEMARKS.md`).

## 3. Decision Process

- Routine changes: maintainer review and merge, per `CONTRIBUTING.md`.
- Substantial changes (architecture, public interfaces, data boundaries, anything touching `SAFETY.md` posture): proposal issue, open comment period, steward decision recorded in the issue.
- Safety boundaries in `SAFETY.md` Sections 2 and 3 — human accountability, no autonomous clinical action, no raw PHI in agent memory or telemetry — are load-bearing. Changes that would weaken them are out of scope for routine governance and require the steward's explicit written decision with published rationale. The default answer is no.
- Gates fail closed. Where automated checks (license audit, safety checks, CI) are unavailable or inconclusive, the change waits.

## 4. Brand and Certification Are Governed Separately

- The Nurse AI OS name, logo, and visual identity are governed by `TRADEMARKS.md`, not by code-contribution status. Maintainership grants no trademark rights.
- Official certification and badge issuance operate as a controlled program under trademark license. Certification authority is designated to reside with the project's nonprofit governance steward (Section 5) so that the body that certifies is not the body that sells, keeping certification credible and commercially neutral.

## 5. Succession and Entity Transfer

Copyright in the project's original components and the Nurse AI OS trademark are currently held by Robert Domondon as an individual. The project's institutional plan is:

1. Upon formation of the designated successor entities, ownership transfers by written intellectual-property assignment — commercial operations assets to the commercial entity, and certification-mark custody to the nonprofit governance steward.
2. The transfer changes the holder, not the terms. The open licenses, the CLA commitments in `CONTRIBUTING.md` Section 1.2, and the permitted uses in `TRADEMARKS.md` Section 2 survive unchanged.
3. Each transfer is announced in the repository changelog and reflected in `NOTICE` and `TRADEMARKS.md` within the same release.

## 6. Transparency

Decisions of record — substantial-change outcomes, maintainer changes, policy-file revisions, ownership transfers — are documented in the repository, in public, at the time they are made. Enforcement actions under `TRADEMARKS.md` that reach the formal stage are disclosed in summary form.

---

To propose a governance change, open a proposal issue labeled `governance` describing the change and its rationale.

