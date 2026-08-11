# Role presets

Eight presets, shipped as JSON. A role is not a hat: a hat is flimsy and blows away in the wind, a role speaks to the core — it carries standing, accountability, and credentials, and that is exactly what these files configure.

Personalization is **configuration, not code**. Adding a role is adding a file here.

| File | Role | Licensure class |
|---|---|---|
| `bedside.json` | Bedside / staff nurse | licensed |
| `charge.json` | Charge / coordinator | licensed |
| `student.json` | Nursing student | pre_licensure |
| `educator.json` | Educator / faculty | licensed |
| `leader.json` | Nurse manager / leader | licensed |
| `np.json` | Nurse practitioner | advanced_practice |
| `resident.json` | MD resident | physician_trainee |
| `entrepreneur.json` | Nurse entrepreneur | licensed |

## The contract

| Key | Meaning |
|---|---|
| `role_id` | Stable identifier. Never renamed once shipped. |
| `label` | Human-facing name. |
| `licensure` | `pre_licensure` · `licensed` · `advanced_practice` · `physician_trainee`. Informational only — see the hard rule below. |
| `tabs` | Which Mission Control tabs load. |
| `overview_cards` | Which Stewardship Home panels render, in order. |
| `starter_agents` | Agents rendered at install. Each still gets its own SOUL, workspace, and memory. |
| `task_lanes` | Kanban lanes on the Tasks tab. |
| `library_filters` | Default filters on the Library tab. |
| `ritual_pack` | Which cron ritual templates render. Templates only — nothing is scheduled automatically. |
| `domain_emphasis` | Which of the eight attention domains lead the balance grid. |
| `standing_rows` | Credential rows the License & standing panel keeps current for this role. |
| `privacy_regimes` | Which boundaries this role's risk briefing surfaces: `phi` always, plus `ferpa`, `personnel`, `academic_integrity`, or `employer_ip`. |
| `risk_briefing` | Three risks, in order. The third is always the one the system cannot catch. |
| `scope_note` / `standing_note` | Optional standing text rendered in the License & standing panel. |
| `tier_note` | The boundary reminder shown with this role. |

## The hard rule

**A preset may not raise a tier ceiling, and `tier_ceilings` is not a valid key. A loader encountering it must reject the file.**

Scope of practice and agent autonomy are orthogonal axes, and the second never inherits from the first. An NP preset and a student preset differ in what they *display* and *track* — never in how much the agent may do unreviewed. `licensure` exists so the standing panel knows which credential rows to render; it is not an input to any autonomy decision.

Ceilings move only through a logged decision in `governance-kit/GOVERNANCE.yaml`, per sphere, on demonstrated evidence. See Rail 3 in `../DOCTRINE.md` and §5.4 of `../MISSION-CONTROL-ARCHITECTURE.md`.

## Why the clinical roles carry a scope note

`np.json` and `resident.json` render standing text because the earlier doctrine did not address them and they would otherwise read Rail 2 as a claim about their scope. It is not. Diagnosing and prescribing are plainly within an NP's or a physician's license. The refusal exists because *this tool* has no regulatory clearance, no clinical validation, and no institutional governance — the rail is about the tool, not the profession.

`leader.json` carries the same rule aimed at positional rather than clinical authority. `entrepreneur.json` carries it aimed at the founder's temptation to ship fast.

## Validation

A preset is valid when:

1. `role_id` is unique and matches the filename.
2. `tier_ceilings` is absent.
3. `privacy_regimes` contains `phi`.
4. `risk_briefing` has exactly three entries.
5. Every `standing_rows` entry resolves to a known credential type.

---

*Agents propose. Humans judge. Nurses steward.*
