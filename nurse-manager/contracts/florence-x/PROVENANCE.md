# Florence-X contract schemas (pinned copies)

These files are unmodified copies of Florence-X's published JSON Schemas.
They are pinned so the manager core can prove, offline and in CI, that
its adapter output satisfies the Florence-X contract.

| File | Upstream path | SHA-256 |
|---|---|---|
| `candidate_action.schema.json` | `schemas/candidate_action.schema.json` | `97c728a00fe0917dd985ce2e2412bdf9499dea8246448f82db4887f494c46699` |
| `edena_decision.schema.json` | `schemas/edena_decision.schema.json` | `1d68ae7b790231bb551c9bc202aba540c2d04625f86b5522d1407c5b6d2bc8b2` |

- Source: `AI-Nurse-Solutions/florence-x` at commit `09675bf61062534e21e1e4aded2f6a14e48f6b8e` (2026-06-18).
- License: Apache License 2.0, the same as this repository. Copyright remains with the Florence-X authors.
- Do not edit these files. To update them, copy the new upstream versions, update the commit and hashes above, and let the tests show what changed.
- The CI job `florence-x-contract` checks the copies byte-for-byte against the pinned upstream commit, and validates adapter output against Florence-X's own Pydantic models.
