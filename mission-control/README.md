# Mission Control (build in progress)

Working directory for the Focused Mission Control Dashboard described in
the build specification (v1.0, July 2026). The application itself — home
workspaces, ADPIE workbench UI, Deliverable Studio, role packets — is
built by Hermes on top of the Nurse AI OS Integration Contract
(`naio-integrations/`), which provides the EDENA policy gateway, privacy
screen, validation, observability, governed memory, governed retrieval,
and the ADPIE workflow runtime underneath the dashboard.

## What exists today

`packets/` holds the machine-readable **role packet manifests** required
by section 14 of the specification, one per role lane:

- `pre-licensure-student/`
- `staff-nurse/`
- `leader/`
- `educator/`
- `licensed-clinician/`

Each manifest declares the packet name and version, role modules
(shared core plus role-specific), required and optional dependencies,
default agents, default permissions, prohibited data classes, supported
exports, migration version, and an integrity checksum.

Safe-by-default invariants are enforced by
`naio_integrations.packets.verify_manifest` and fail closed:

- default permissions start empty; integrations are off by default;
- every starter agent ships tools-disabled, propose-only, at Green;
- D3 and D4 data are prohibited in the personal edition;
- every packet embeds the shared governance core;
- installation never implies employer, school, regulatory, IRB,
  privacy, or security approval.

`example-workspace/` holds the **synthetic example workspace** every
packet ships with (specification section 14): a completed sample ADPIE
project (a genuine workflow checkpoint), an evidence library using the
five evidence labels, a sample deliverable that went through the full
draft-review lifecycle, and the first-run pathway mapping each
onboarding choice (section 13, step 5) to a Deliverable Studio template
so one call produces a real, editable artifact — the
ten-minute-first-artifact acceptance criterion. Every record is labeled
synthetic, all content passes the privacy screen, and the workspace can
be reset or removed.

The Deliverable Studio itself lives in
`naio_integrations/deliverables.py` with templates in
`naio-integrations/config/deliverable-templates.json`. Every scaffold is
born a draft with a mandatory banner; only a named human review with an
explicit disposition and date changes that, and approved renders carry
the attestation. No output is presented as final merely because it was
generated (specification section 3.6).

Four packets (`pre-licensure-student/`, `staff-nurse/`, `educator/`
from Phase 2, and `leader/` unlocked by Phase 3) are **installable
bundles**, not just manifests: each ships a role README with the
section 19 recognitions, a `DATA-BOUNDARY.md` notice to read before
first use, and working starter templates rendered by the Deliverable
Studio — every one an editable draft with the mandatory banner. No
empty demo. The licensed-clinician packet remains manifest-only until
Phase 4.

`healthcare-sandbox/` holds the **Phase 3 healthcare sandbox**:
synthetic, FHIR-shaped case bundles generated from the reviewed case
catalog (synthetichealth/synthea and hapifhir/hapi-fhir patterns, no
vendored code). Every record is labeled synthetic, carries a
numeric-suffix name, and passes the privacy screen; the sandbox module
refuses unlabeled or identifier-bearing content at admission. See
`healthcare-sandbox/README.md` for the boundary invariants.

## Regenerating

```bash
python3 scripts/build-mission-control-manifests.py
python3 scripts/build-mission-control-packet-bundles.py
python3 scripts/build-mission-control-example-workspace.py
python3 scripts/build-mission-control-healthcare-sandbox.py
```

The bundle script runs after the manifests script and owns
`packets/CHECKSUMS.sha256`, which covers every committed file in the
packets tree.

Both builds are deterministic — CI rebuilds twice and fails on any diff —
so artifact changes are always deliberate, reviewed catalog changes in
`naio-integrations/config/`, never drift.
