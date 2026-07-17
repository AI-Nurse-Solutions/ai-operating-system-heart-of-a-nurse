# THRIVE Installation Manifest

**Program:** `WELLMKT-AIOS-THRIVE-COMPLETE-1.0`<br>
**Foundation:** `WELLMKT-AIOS-LIFE-OPERATIONS-1.0`<br>
**Overlay:** `WELLMKT-AIOS-THRIVE-1.0`<br>
**Canonical components:** 17<br>
**Release criteria owned:** 160<br>
**Review date:** 2026-07-16

| # | Relative component path | Version | Checkpoint | Criteria ownership | Required |
|---:|---|---|---|---:|---|
| 01 | `foundation/00-Wellness-Life-and-Operations-Foundation.md` | 1.0.0 | S1 | 8 | required |
| 02 | `core/00-Standalone-Wellness-Marketing-Management-Lane.md` | 1.0.0 | S1 | 8 | required |
| 03 | `core/01-Trust-Privacy-Safety-and-Authority-Shield.md` | 1.0.0 | S1 | 8 | required |
| 04 | `core/02-THRIVE-Operating-Core.md` | 1.0.0 | S1 | 8 | required |
| 05 | `core/03-Nurse-AI-OS-Mission-Control-and-Dashboard-Integration.md` | 1.0.0 | S1 | 8 | required |
| 06 | `thrive/01-T-Truth-Trust.md` | 1.0.0 | S2 | 8 | required |
| 07 | `thrive/02-H-Human-Centered-Experience.md` | 1.0.0 | S2 | 8 | required |
| 08 | `thrive/03-R-Reach-Relationships.md` | 1.0.0 | S2 | 8 | required |
| 09 | `thrive/04-I-Integrated-Campaigns-Operations.md` | 1.0.0 | S2 | 8 | required |
| 10 | `thrive/05-V-Value-Viability.md` | 1.0.0 | S2 | 8 | required |
| 11 | `thrive/06-E-Ethics-Evidence-Agents.md` | 1.0.0 | S2 | 8 | required |
| 12 | `workflows/01-THRIVE-Runnable-Workflows.md` | 1.0.0 | S2 | 8 | required |
| 13 | `workflows/02-THRIVE-Setting-and-Role-Recipes.md` | 1.0.0 | S2 | 8 | required |
| 14 | `workflows/03-THRIVE-Schemas-and-Agents.md` | 1.0.0 | S2 | 16 | required |
| 15 | `templates/01-THRIVE-Functional-Templates.md` | 1.0.0 | S2 | 8 | required |
| 16 | `tests/01-THRIVE-Release-and-Runtime-Tests.md` | 1.0.0 | S2 | 24 | required |
| 17 | `manifest/01-THRIVE-Installation-Manifest.md` | 1.0.0 | S2 | 8 | required |

## Inventory invariants

- 17/17 component paths, no substitute names and no extra source component.
- 24 powers `PWR-01`–`PWR-24`, all Available Inactive.
- 24 workflows `WF-01`–`WF-24`, each linked to a functional template and closed schema.
- 30 templates `TPL-01`–`TPL-30` with required fields, synthetic example, validation, human gate, boundary and safe finish.
- 18 schemas created once and 10 agents `AGT-01`–`AGT-10`, all PERM-P0 Disabled.
- 160 runtime criteria: `RA-A01`–`RA-R08` and `RA-INT01`–`RA-INT16`.
- One canonical `My THRIVE Mission Control` dashboard at `/wellness-services-marketing-managers/dashboard`, with `/wellness-services-marketing-managers/mission-control` as its lane-scoped alias and Markdown fallback.
