# My DISCOVER Mission Control

**Canonical Markdown source of truth:** `/healthcare-research-innovation-leaders/dashboard`<br>
**Only alias:** `/healthcare-research-innovation-leaders/mission-control`<br>
**Persistent boundary:** Planning and preview—not live clinical, research, regulatory, financial or safety control.

## Identity and safety bar

Product/version; active hat and authority expiry; data ceiling; all-agent state; Pause All/Kill state; last verified receipt; Markdown fallback. Optional self-contained local HTML renders the same state with no remote scripts, trackers or second store.

The parent Nurse AI OS card receives only coarse status and the lane deep-link; it must never receive underlying data, memory, schemas, permissions, agents, agent state, private plans or research content.

## Deterministic attention queue

Show at most seven attention items. Order blocked/expired first, then due timestamp ascending, then immutable attention-item ID ascending. Deterministic attention-item ordering must survive Markdown/rich rendering, resume and reinstall.

## Four bounded Preview launchers

### Frame a Research or Innovation Question

- **Mode:** Preview only; opens `DSC-WF-04` and never executes an external action.
- **Allowed input / schema:** DATA-D0/D1 metadata; validate against `opportunity_boundary_intake`.
- **Human gate:** HRPP/IRB/QI/clinical/regulatory owner reviews the exact object/version/hash.
- **Receipt and expiry:** emit `control_audit_receipt`; stale authority/source/approval blocks and re-routes.
- **Rollback/discard:** discard unapproved preview; remove staged refs; preserve a minimal tamper-evident control receipt when policy requires.
### Build an Evidence and Source Brief

- **Mode:** Preview only; opens `DSC-WF-19` and never executes an external action.
- **Allowed input / schema:** public authoritative sources; validate against `evidence_provenance`.
- **Human gate:** qualified evidence/applicability reviewer reviews the exact object/version/hash.
- **Receipt and expiry:** emit `control_audit_receipt`; stale authority/source/approval blocks and re-routes.
- **Rollback/discard:** discard unapproved preview; remove staged refs; preserve a minimal tamper-evident control receipt when policy requires.
### Review Portfolio, Authority, and Decision Readiness

- **Mode:** Preview only; opens `DSC-WF-03` and never executes an external action.
- **Allowed input / schema:** approved aggregate/process metadata; validate against `portfolio_decision_orchestration`.
- **Human gate:** named portfolio authority reviews the exact object/version/hash.
- **Receipt and expiry:** emit `control_audit_receipt`; stale authority/source/approval blocks and re-routes.
- **Rollback/discard:** discard unapproved preview; remove staged refs; preserve a minimal tamper-evident control receipt when policy requires.
### Design a Translation or Adoption Experiment

- **Mode:** Preview only; opens `DSC-WF-16` and never executes an external action.
- **Allowed input / schema:** synthetic/non-production inputs; validate against `innovation_validation_experiment`.
- **Human gate:** innovation, safety, privacy and operations owners reviews the exact object/version/hash.
- **Receipt and expiry:** emit `control_audit_receipt`; stale authority/source/approval blocks and re-routes.
- **Rollback/discard:** discard unapproved preview; remove staged refs; preserve a minimal tamper-evident control receipt when policy requires.


## Six launcher groups

1. Direction & Portfolio — DSC-WF-01, 02, 03, 13.
2. Boundaries & Governance — DSC-WF-04, 05, 06, 14.
3. Study & Operational Readiness — DSC-WF-07, 08, 09, 15.
4. People, Partners & Resources — DSC-WF-10, 11, 12, 23.
5. Innovation, Value & Translation — DSC-WF-16, 17, 18, 20.
6. Evidence, Dissemination & Renewal — DSC-WF-19, 21, 22, 24.

## Views and controls

Portfolio/decision, unresolved FRAME/governance, evidence/corrections/learning, agent controls and an owner-only private-plan deep link. Permanent controls: Privacy/Data Boundary, Pause All, Kill, Correct, Export Preview, Delete, Reset View, Resume from receipt, Rollback and DISCOVER-only Uninstall. Delete is scoped, previewed and human-confirmed; Reset changes presentation only. Keyboard access, visible focus, reflow/zoom, reduced motion, no color-only meaning, alt text, labeled tables and no timed safety-message dismissal are mandatory.
