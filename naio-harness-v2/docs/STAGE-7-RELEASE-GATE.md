# Stage 7 — Release and Stewardship Gate

## Candidate status

Harness 2.0 is a tested, unsigned implementation candidate. It is not a clinical system, HIPAA certification, institutional approval, or production authorization.

## Evidence required

- Full stdlib unit-test suite passes.
- Versioned synthetic trajectory dataset passes.
- Plugin loads through Hermes's real plugin manager.
- Unknown tools and synthetic PHI patterns block.
- External side effects return an approval directive.
- Output budget transform is active.
- Source-tree hash and terminal provenance root are recorded.
- Public architecture statement links primary sources.
- Secret/PHI scan and internal-link checks pass.

## Human gates

| Gate | Status |
|---|---|
| Founder architecture approval | Approved July 13, 2026 |
| Nurse Steward Council review | Pending |
| Institutional CNO/CIO/CTO review | Not claimed |
| Matching legacy signing key | Not available in this build environment |
| Trust-anchor rotation | Not authorized and not performed |
| Default-profile activation | Not performed |

## Signing rule

Do not overwrite or silently rotate the existing trust anchor. A signed Harness 2.0 release requires an authorized human key ceremony, verification of the public fingerprint, signing of the source-tree hash plus evaluation dataset version and terminal provenance root, and independent verification before distribution.

## Rollback

The implementation is additive under `naio-harness-v2/`. The signed Phase 23 bundle remains unchanged. Rollback is removal/disablement of the canary plugin and selection of the prior signed release; no migration of PHI or clinical data exists because those categories are prohibited.
