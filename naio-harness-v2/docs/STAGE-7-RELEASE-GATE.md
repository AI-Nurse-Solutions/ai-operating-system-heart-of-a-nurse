# Stage 7 — Release and Stewardship Gate

## Candidate status

Harness 2.0 is a tested, existing-trust-anchor signed implementation candidate. It is not a clinical system, HIPAA certification, institutional approval, or production authorization.

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
| Matching legacy signing key | Restored at its original protected path; fingerprint verified |
| Detached release-evidence signature | Required to verify against the existing RSA-SHA256 public key before release |
| Trust-anchor rotation | Not required and not performed |
| Default-profile activation | Not performed |

## Signing rule

Do not overwrite or silently rotate the existing trust anchor. The Harness 2.0 release signs the exact machine-evidence JSON, which binds the source-tree hash, evaluation dataset identity/version/hash, terminal provenance root, test results, clinical/data boundaries, and human-governance status. The signing script refuses changed bytes, unsafe private-key permissions, or a key whose derived public fingerprint differs from the trusted RSA public key. Independent verification is required before distribution.

Verification command from the repository root:

```bash
openssl dgst -sha256 \
  -verify naio-os/config/naio-os-release-public.pem \
  -signature naio-harness-v2/evidence/release-evidence.sig \
  naio-harness-v2/evidence/release-evidence.json
```

## Rollback

The implementation is additive under `naio-harness-v2/`. The signed Phase 23 bundle remains unchanged. Rollback is removal/disablement of the canary plugin and selection of the prior signed release; no migration of PHI or clinical data exists because those categories are prohibited.
