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

## Regenerating

```bash
python3 scripts/build-mission-control-manifests.py
```

The build is deterministic — CI rebuilds twice and fails on any diff —
so manifest changes are always deliberate, reviewed catalog changes in
`naio-integrations/config/mission-control-packets.json`, never drift.
