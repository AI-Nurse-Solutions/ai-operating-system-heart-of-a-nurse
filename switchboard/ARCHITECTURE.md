# Nurse AI OS Switchboard Architecture Decision Record

**Decision:** One Nurse Core, many context-specific Role Dashboards, additive Capability Packs, and a governed extension registry.

## Canonical distinction

> Person ≠ credential ≠ role ≠ assignment ≠ authority.

- **Nurse Core:** portable no-PHI preferences and governance doctrine.
- **Context:** facility, school, clinic, committee, community, or personal boundary.
- **Role Dashboard:** one role or assignment in one context.
- **Capability Pack:** an additive contribution mode such as DISCOVER, FUTURE, BUILD, GOVERN, ORGANIZE, or ORCHESTRATE.
- **Future Authority Envelope:** a task-level intersection of context, assignment, role, data, EDENA disposition, and autonomy ceiling. The browser preview does not calculate or display one.
- **Bridge:** an explicit reviewed copy between dashboards. Navigation never transfers data.

## Monotonic authority

Every additional layer may narrow authority. No capability, self-declaration, or download may restore authority denied by a more restrictive layer. Supporting-role composition is disabled in this preview until compatibility and authority-intersection rules are independently validated.

The browser preview never grants authority and performs no EDENA task assessment. Its Dashboard Configuration Posture displays `EDENA: Not evaluated` and `A0 · no action`; future task-level Green/Yellow/Orange/Red and A0–A2 decisions require evidence and a separate governed runtime.

## Extensible registry

Registry entries are classified as:

1. professional or community role;
2. functional assignment;
3. capability;
4. future context adapter, documented in the registry architecture but not locally creatable or executable in this preview.

Public lifecycle:

`proposed → classified → source/claim audit → EDENA review → synthetic tests → independent review → published inactive → contextually selected → revalidated/revised/retired`.

Local custom roles remain `Local Draft · Not NAIO-reviewed`.

## First preview boundaries

The preview:

- stores normalized dashboard configuration in browser local storage;
- supports export/import of configuration JSON;
- reads no files except a user-selected Switchboard JSON import;
- makes no application API or model calls and does not transmit Switchboard configuration; ordinary page assets, including Google Fonts, still make web requests as disclosed in the privacy policy;
- does not install or reconfigure Hermes;
- does not activate skills, profiles, memory, connectors, cron, or external actions;
- prohibits PHI, patient narrative, learner records, workforce records, credentials, and operational data, while acknowledging that a short free-text title and imported JSON cannot be exhaustively screened by browser heuristics;
- provides navigation links only between dashboards;
- treats cross-dashboard transfer as future governed work, not current functionality.

The preview's separation is navigational and metadata-level. All dashboard configuration is stored under one browser-local Switchboard key. It is not a secure sandbox, employer-grade tenant boundary, proof of Hermes profile isolation, or reliable PHI-loss-prevention control. Users must enter generic labels only.

`schema/switchboard.schema.json` documents the portable structural shape only. Import acceptance additionally requires the deterministic `normalizeState()` invariants for exact fixed-window duration, role/context/capability compatibility, unique identifiers, collision protection, and active-dashboard referential integrity. Schema validity alone is never authority evidence or an import-success guarantee.

## Default future Hermes mapping to test separately

Use one Hermes profile per meaningful organization, academic, community, or personal boundary. Allow several Role Dashboards inside that context only after synthetic isolation, update, rollback, and wrong-context tests. This is a recommendation, not implemented behavior.
