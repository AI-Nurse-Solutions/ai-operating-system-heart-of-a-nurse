# Healthcare Sandbox (Phase 3)

A safe place to practice on patient-shaped data with **no patients in
it**. Every record here is synthetic teaching material generated from
the reviewed case catalog in
`naio-integrations/config/healthcare-sandbox-cases.json` by
`naio_integrations/sandbox.py`.

Two open-source patterns, no vendored code (per the Integration
Contract):

- **synthetichealth/synthea** — synthetic patient generation. Records
  are produced from configuration, never collected, and every generated
  person carries a numeric-suffix name (for example `Amara701
  Kestrel842`) so a synthetic record can never be mistaken for a real
  one.
- **hapifhir/hapi-fhir** — FHIR-shaped resources and a read/search
  access surface. Bundles hold Patient, Encounter, Condition,
  MedicationRequest, and Observation resources so work practiced here
  transfers to real FHIR systems later.

## Boundary invariants

- Every resource carries the sandbox synthetic security label
  (`urn:naio:healthcare-sandbox` / `SYNTHETIC`); unlabeled content is
  refused at admission.
- Every string in every resource must pass the privacy screen before
  admission, so real-looking identifiers cannot be smuggled in under a
  synthetic label. Detection reduces risk — it **never proves** content
  is de-identified, which is why screening still runs on data that is
  synthetic by construction.
- Reads and searches are tenant-scoped; another tenant's request reads
  as "unknown resource".
- Sandbox content is D0 (synthetic) by construction, and governance
  does not relax because data is synthetic: role gates and the ADPIE
  human-authorization gate apply unchanged.

## Contents

`cases/<case-id>/bundle.json` — the FHIR-shaped collection bundle.
`cases/<case-id>/case-summary.md` — the human-readable summary, banner
first.

## Regenerating

```bash
python3 scripts/build-mission-control-healthcare-sandbox.py
```

Deterministic — CI rebuilds twice and fails on any diff. This README is
authored and is not overwritten by the build.
