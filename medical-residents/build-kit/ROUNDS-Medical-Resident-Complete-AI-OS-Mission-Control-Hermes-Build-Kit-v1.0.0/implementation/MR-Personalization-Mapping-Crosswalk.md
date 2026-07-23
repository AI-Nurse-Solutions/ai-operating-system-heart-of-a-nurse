
# ROUNDS Personalization Mapping Crosswalk

| Approved derived input | Mission Profile field | Rule |
|---|---|---|
| Display name | `display_name` | Editable; no legal-identity claim |
| Resident stage and local label | `resident_status`, `local_title` | User-entered; never verified authority |
| Program, specialty, PGY, site, rotation | matching fields | Context only; source/expiry required for consequential use |
| Role adapters | `role_adapters`, `primary_role_adapter` | Routing only; chief clinical/admin remain separate |
| Complementary hats | `task_hats`, primary/secondary hats | Every gate applies; least privilege wins |
| Mission and values | `mission_statement`, `core_values` | Derived Soul fields only; raw answers excluded |
| Priorities and goals | `current_priorities`, `goals` | Preserve wording and uncertainty |
| AI boundaries | `ai_preferences` | P0 default, personal ceiling P2, actions Off |
| Memory choices | `memory_preferences` | Session-only default; category consent |
| Risk preference | `governance_preferences` | Cannot waive a stop or create authority |
| Recommended assets | inactive PWR/WF/TPL/AGT records | Recommendation never activates |

Derive in memory, show every proposed field with provenance and uncertainty, and allow edit/reject/approve/export/delete. The strict schema requires one provenance row for every persisted proposed field. Persist only the owner-approved minimum.

Reject raw Discover answers, raw quiz answers, raw `SOUL.md`, unknown fields, incompatible baseline adapter shapes, number-only legacy ID mappings, authority inflation, missing provenance, and invalid context/date combinations. The current Mission Profile cannot activate an institutional context or represent institution verification.
