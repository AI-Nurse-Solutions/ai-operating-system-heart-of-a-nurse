
# Respiratory Care Professional Personalization Mapping Crosswalk

| Approved input | Proposed Mission Profile field | Review rule |
|---|---|---|
| Display name | `display_name` | User edits or rejects |
| Mission and values | `mission_statement`, `core_values` | Never infer from raw quiz answers |
| Current season and goals | `current_priorities`, `goals` | Preserve user wording and uncertainty |
| Role interests | `task_hats` | Task routing only; no authority |
| Capacity | planning mode and burden budget | Never diagnose burnout or fitness |
| Working preferences | communication, decision, learning and cadence | User controlled |
| AI boundaries | `ai_preferences` | Narrower rule wins |
| Memory choices | `memory_preferences` | Session-only default |
| Risk preference | governance preference | Cannot waive an absolute stop |
| Recommended BREATHE | inactive recommendation records | Recommendation is not activation |

Derive the proposal in memory. Show field-level provenance and uncertainty. Let the user edit, reject, approve, export or delete it. Persist only approved minimum fields. Never infer license, certification, competence, scope, privilege, prescribing authority, payer status, employment or institutional authority.
