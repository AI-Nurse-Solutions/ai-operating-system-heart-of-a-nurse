# FUTURE Personalization Mapping Crosswalk

## 1. Scope and non-authority rule

This contract transforms supported, derived Discover Packet and Soul Profile adapters into a proposed `FUTURE Mission Profile` for `FUTURE Mission Control`.

The profile personalizes navigation, learning support, private planning, role-workspace separation, accessibility and an inactive recommendation queue. It never infers or grants enrollment, employment, title, scope, delegation, supervision, competence, clinical readiness, certification, licensure, authority, academic permission or authorization to use information.

Current law, emergency procedures, approved program/employer/clinical-site rules and authorized faculty, preceptor, supervising nurse, supervisor, privacy, security, compliance, accessibility, HR, labor, legal, clinical and IT owners govern. Unknown authority never becomes permission. Personal preference cannot lower an EDENA classification or hard stop.

## 2. Canonical-source versus build-layer identifiers

The canonical v1 source has these formal IDs:

- complete program: `NAIO-FUTURE-COMPLETE-1.0`;
- foundation: `NAIO-FUTURE-CORE-1.0`;
- optional expansion: `NAIO-FUTURE-SP-1.0`; and
- namespace: `future.*`.

It canonically numbers and names 18 **Powers**, lists 18 **Priority recipes**, and names five templates. It does **not** assign PWR/WF/TPL machine IDs. The build therefore registers the following implementation identifiers under pinned catalog version `FUTURE-CATALOG-1.0.0`:

- `FUT-PWR-01` through `FUT-PWR-18`;
- `FUT-WF-01` through `FUT-WF-18`; and
- `FUT-TPL-01` through `FUT-TPL-05`.

These are build-layer identifiers, not quotations of nonexistent legacy IDs. Each identifier is bound to an exact canonical number, name, source path, source-package hash and catalog hash. A later catalog may not silently change a binding. Missing, duplicate or hash-mismatched relations remain visible and blocked.

## 3. Deterministic transformation order

1. Enforce file-size, depth, unsafe-key, direct-identifier, credential and prohibited-content checks.
2. Validate against the exact closed adapter schema and supported version.
3. Normalize into a transient proposal; never persist raw quiz answers, interviews, school records or work records.
4. Map direct fields and display all conflicts. Do not silently choose Discover over Soul or Soul over Discover.
5. Ask the user to select Nursing Student, Nursing Assistant or Bridge, then choose exactly one Primary role workspace.
6. Confirm the active protected space—Learning, Work growth, Life, or Community and future—and one precise operational context: `academic_learning`, `clinical_placement_learning`, `employment_growth`, `personal_life`, or `public_community_future`.
7. Ask minimum first-run questions about local title, program/employer rules, supervision, scope/delegation sources, sources, capacity, accessibility and human routes. `Skip`, `Not now`, `Use this session only`, `Show an example`, and `Ask a human` remain available.
8. Resolve recommendations only through the exact pinned relations in sections 8–11.
9. Preview each proposed field group, provenance, uncertainty and effect. Permit edit, approve or reject.
10. Run JSON Schema and semantic validation, then save one version atomically.
11. Add approved recommendations only to an inactive review queue. An agent ID may be recommended by explicit task intent, but every agent remains `PERM-P0 Disabled` with no run, data, memory, model, tool or permission grant. Tool IDs remain empty; connectors, sharing, external actions and background automation remain off.

## 4. Field provenance

Each approval group records target JSON pointer, source type, bounded source reference, source JSON pointer, stable `MAP-*` rule, derivation, uncertainty, approval state and timestamps. A source reference identifies a derived adapter; it is never authority to retain raw material.

An approved profile requires a non-null `approved_at`. Proposed and rejected profiles require `approved_at=null`. Every approved user-visible value must have exact-pointer or documented parent-group provenance. Authority, academic integrity, memory, workspace, recommendation and governance values remain separately reviewable.

## 5. Discover Packet mapping

| Source pointer | Mission Profile target or disposition | Rule | Constraint |
|---|---|---|---|
| `/schema`, `/packet_schema_version` | Validate only | `MAP-FUTURE-DISCOVER-VERSION-1` | Only the exact supported version maps. |
| `/generated_at` | Provenance metadata | `MAP-FUTURE-DISCOVER-METADATA-1` | Never use as user approval time. |
| `/mission_statement` | `/mission_statement` | `MAP-FUTURE-MISSION-1` | Direct proposal; conflict requires user resolution. |
| `/core_values` | `/core_values` | `MAP-FUTURE-DISCOVER-DIRECT-1` | Self-described values, not personality facts. |
| `/current_priorities` | `/current_priorities` | `MAP-FUTURE-DISCOVER-DIRECT-1` | Workspace allocation requires review. |
| goals `short_term/medium_term/long_term` | goals `near_term/medium_term/long_term` | `MAP-FUTURE-GOAL-HORIZON-1` | Exact horizon-name translation. |
| `/working_preferences/*` | matching target fields | `MAP-FUTURE-WORKSTYLE-1` | Cadence and constraints are first-run questions. |
| `/role_goals[]/role_id` | workspace candidates | `MAP-FUTURE-ROLE-CANDIDATE-1` | Apply section 7; role label proves nothing. |
| role goal and success measure | workspace goal and starter preview | `MAP-FUTURE-ROLE-GOAL-1` | A measure is not a result or competency claim. |
| role priority | workspace priority | `MAP-FUTURE-ROLE-PRIORITY-1` | Does not create academic, clinical or employment urgency. |
| role `default_edena` | starter candidate only | `MAP-FUTURE-EDENA-CANDIDATE-1` | Actual content and context must be classified. |
| `/ai_boundaries/default_autonomy` | `/ai_preferences/default_support` | `MAP-FUTURE-AI-1` | Cannot override attempt-before-answer or human gates. |
| AI may-support/confirmation/never-delegate | matching target lists | `MAP-FUTURE-AI-1` | Union never-delegate with immutable FUTURE prohibitions. |
| governance risk/default EDENA/retention | matching target fields | `MAP-FUTURE-GOVERNANCE-1` | Preferences are not risk or permission determinations. |
| `/recommended_workflow_ids[]` | source recommendation provenance | `MAP-FUTURE-CATALOG-RESOLUTION-1` | Resolve only the explicit cross-lane table in section 11. |
| `/recommended_capability_ids[]` | `/recommended_assets/capability_ids[]` | `MAP-FUTURE-CAPABILITY-1` | Recommendation awards no badge or credential. |
| uncertainties/source/demo | matching target/provenance behavior | `MAP-FUTURE-DISCOVER-DIRECT-1` | Preserve uncertainty; demo evidence is excluded. |

`default_retention=local_non_sensitive` translates to `local_nonsensitive`; `session_only` maps directly. First run supplies edition and data boundary. Default is Personal, synthetic/public/owner-nonsensitive and memory Off.

## 6. Soul Profile mapping

| Source pointer | Mission Profile target or disposition | Rule | Constraint |
|---|---|---|---|
| schema/version/scoring metadata | Validate and provenance only | `MAP-FUTURE-SOUL-VERSION-1` | Scores confer no identity, authority or ability. |
| `/completed_at`, `/user_confirmed_at` | provenance metadata | `MAP-FUTURE-SOUL-METADATA-1` | Null confirmation keeps all values proposed. |
| `/role_constellation[]` | workspace candidates | `MAP-FUTURE-WORKSPACE-CANDIDATE-1` | Exactly one approved Mission Profile workspace must be Primary. |
| `unverified` or `external_unverified` authorization | workspace `unknown` | `MAP-FUTURE-AUTH-ENUM-1` | Neither is external verification. |
| `user_asserted` authorization | workspace `user_asserted` | `MAP-FUTURE-AUTH-ENUM-1` | Still grants no permission. |
| core values and mission | matching target | `MAP-FUTURE-MISSION-1` | Conflicts with Discover require explicit resolution. |
| populations | situation-note candidate | `MAP-FUTURE-POPULATION-1` | Never create a real patient, class, cohort, employee or community roster. |
| learner/developmental stage | strength/growth review | `MAP-FUTURE-DEVELOPMENT-1` | Self-description, not competency evidence. |
| advanced studies | goal and learning workspace candidate | `MAP-FUTURE-STUDY-1` | Do not infer enrollment, completion, eligibility or credential. |
| working/learning preferences | matching target fields | `MAP-FUTURE-WORKSTYLE-1` | User reviews before save. |
| theme and tone | presentation fields | `MAP-FUTURE-PRESENTATION-1` | Cannot soften warnings or hide controls. |
| role synergies/tensions | situation notes | `MAP-FUTURE-ROLE-DYNAMICS-1` | Do not diagnose or transfer data across contexts. |
| wellness limits | time constraints and capacity candidate | `MAP-FUTURE-WELLNESS-1` | Private by default; not an academic or employment record. |
| AI relationship preferences | AI support candidates | `MAP-FUTURE-AI-RELATIONSHIP-1` | Never activates an agent, tool or automation. |
| governance boundaries | AI, integrity and safeguard candidates | `MAP-FUTURE-SOUL-GOVERNANCE-1` | Preserve the most restrictive interpretation. |
| memory allowed/denied | memory proposal | `MAP-FUTURE-MEMORY-1` | Memory remains Off until separate consent; denials win. |
| escalation rules | safeguard display | `MAP-FUTURE-ESCALATION-1` | Does not invent a real human route. |
| dashboard recommendations | workspace/module candidates | `MAP-FUTURE-DASHBOARD-1` | Unsupported roles require a lane decision. |
| uncertainties/source/demo | matching target/provenance behavior | `MAP-FUTURE-SOUL-DIRECT-1` | Preserve uncertainty; demo earns no evidence. |

## 7. Role-to-workspace candidates

Exactly one approved workspace is Primary. Bridge mode maintains distinct school and work partitions and requires a visible context switch.

| Adapter role or declared pathway | Candidate workspace | Required review |
|---|---|---|
| `prelicensure-support` + Nursing Student | `nursing_student_academic_learning` | Exact program/level if the user wishes, current AI-use and assessment rules, authorized faculty route; no enrollment inference. |
| Nursing Student + supervised preparation | `nursing_student_skills_clinical_rehearsal` | Approved checklist/source, fictional or lab context, faculty/preceptor supervision; never live care. |
| `prelicensure-support` + Nursing Assistant/CNA/PCT/PCA/UAP/care-aide declaration | `nursing_assistant_role_learning` | Exact local title, employer policy, verified scope, delegation and supervision. Generic title never determines scope. |
| Nursing Assistant work-growth declaration | `nursing_assistant_work_growth` | Keep person/patient/employer-confidential data out; ask authorized supervisor route. |
| `prelicensure-support` + Bridge | `bridge_academic_learning` and optional `bridge_work_growth` | User chooses one Primary; no automatic cross-partition transfer. |
| `advanced-studies` | `certification_licensure_preparation` or `career_portfolio_opportunity` | Ask exact goal and source; no pass, eligibility, credential or competence claim. |
| `community` | `community_leadership_future` | Require public/consent-based information and human review before outreach. |
| `digital-ai` | `personal_technology_innovation_sandbox` | Synthetic non-production prototype only; no school/employer connection. |
| `shared-identity` | `private_life_capacity` | Private goals only; no school/employer visibility by default. |
| staff nurse, advanced practice, educator, resident, manager, administrator, wellness, research or other professional role | No automatic FUTURE workspace | Offer the appropriate separate lane or keep as contextual identity. Never widen FUTURE learner authority. |
| unknown role | No workspace | Preserve source wording and ask; do not force a fit. |

`authorization_status=externally_verified` cannot be derived from either adapter. It requires separate current evidence, scope, verifier and expiry. Even then, the Mission Profile does not itself grant authority.

## 8. Exact power registry

| Build ID | Canonical numbered name |
|---|---|
| `FUT-PWR-01` | Power 1 — Future North Star & 90-Day Map |
| `FUT-PWR-02` | Power 2 — Capacity, Money & Life Logistics Navigator |
| `FUT-PWR-03` | Power 3 — Confidence, Recovery & Help-Seeking Coach |
| `FUT-PWR-04` | Power 4 — Active Learning & Study Sprint Engine |
| `FUT-PWR-05` | Power 5 — Skills Lab & Clinical Readiness Rehearsal |
| `FUT-PWR-06` | Power 6 — NCLEX, Certification & Knowledge-Gap Studio |
| `FUT-PWR-07` | Power 7 — SAFE Prompt & AI Literacy Lab |
| `FUT-PWR-08` | Power 8 — Evidence, Source & Misinformation Detective |
| `FUT-PWR-09` | Power 9 — Privacy, Bias, Integrity & Governance Red Team |
| `FUT-PWR-10` | Power 10 — Digital Workflow & Automation Sandbox |
| `FUT-PWR-11` | Power 11 — UI/UX & Accessible Dashboard Builder |
| `FUT-PWR-12` | Power 12 — Data, Informatics & Responsible Innovation Lab |
| `FUT-PWR-13` | Power 13 — Career Portfolio, Résumé & Interview Studio |
| `FUT-PWR-14` | Power 14 — Professional Communication, Mentorship & Network Builder |
| `FUT-PWR-15` | Power 15 — Opportunity, Scholarship & Ethical Side-Project Navigator |
| `FUT-PWR-16` | Power 16 — Speaking Up, Teamwork & Emerging Leadership Lab |
| `FUT-PWR-17` | Power 17 — Community Health & Service Project Studio |
| `FUT-PWR-18` | Power 18 — Future-of-Nursing Explorer |

Every power begins **Available Inactive**. A recommendation, preview, role selection, badge or prior run does not activate it. The first week permits at most one separately previewed and approved power.

## 9. Exact workflow and primary asset registry

These workflow labels are bound to the canonical numbered **Priority recipes** in `workflows/Seven-Day-and-Ninety-Day-Launch.md`.

| Build workflow | Canonical priority recipe | Primary power | Supporting power | Primary template |
|---|---|---|---|---|
| `FUT-WF-01` | 1. Daily ten-minute Next Move | `FUT-PWR-01` | — | `FUT-TPL-01` |
| `FUT-WF-02` | 2. Weekly whole-life and capacity plan | `FUT-PWR-02` | `FUT-PWR-03` | `FUT-TPL-01` |
| `FUT-WF-03` | 3. Study sprint and teach-back | `FUT-PWR-04` | `FUT-PWR-07` | `FUT-TPL-03` |
| `FUT-WF-04` | 4. Fictional clinical-reasoning or communication rehearsal | `FUT-PWR-05` | `FUT-PWR-14` | `FUT-TPL-03` |
| `FUT-WF-05` | 5. Skills-lab or certification preparation from approved sources | `FUT-PWR-05` | `FUT-PWR-06` | `FUT-TPL-03` |
| `FUT-WF-06` | 6. NCLEX or role-knowledge gap review | `FUT-PWR-06` | `FUT-PWR-08` | `FUT-TPL-03` |
| `FUT-WF-07` | 7. Graded-work integrity route | `FUT-PWR-09` | `FUT-PWR-07` | `FUT-TPL-03` |
| `FUT-WF-08` | 8. Claim and citation verification | `FUT-PWR-08` | — | `FUT-TPL-03` |
| `FUT-WF-09` | 9. Bias, privacy, deepfake, or prompt-injection red team | `FUT-PWR-09` | `FUT-PWR-08` | `FUT-TPL-03` |
| `FUT-WF-10` | 10. SAFE prompt studio | `FUT-PWR-07` | — | `FUT-TPL-02` |
| `FUT-WF-11` | 11. Synthetic workflow and automation sandbox | `FUT-PWR-10` | `FUT-PWR-12` | `FUT-TPL-04` |
| `FUT-WF-12` | 12. Accessible dashboard or app prototype | `FUT-PWR-11` | `FUT-PWR-12` | `FUT-TPL-04` |
| `FUT-WF-13` | 13. Career pathway and bridge-to-nursing map | `FUT-PWR-15` | `FUT-PWR-01` | `FUT-TPL-05` |
| `FUT-WF-14` | 14. Résumé, interview, scholarship, or application preparation | `FUT-PWR-13` | `FUT-PWR-15` | `FUT-TPL-05` |
| `FUT-WF-15` | 15. Mentorship, feedback, boundary, or speaking-up rehearsal | `FUT-PWR-14` | `FUT-PWR-16` | `FUT-TPL-03` |
| `FUT-WF-16` | 16. Community health or service project canvas | `FUT-PWR-17` | `FUT-PWR-09` | `FUT-TPL-04` |
| `FUT-WF-17` | 17. Future-of-nursing exploration sprint | `FUT-PWR-18` | `FUT-PWR-12` | `FUT-TPL-05` |
| `FUT-WF-18` | 18. Overload recovery and re-entry mode | `FUT-PWR-03` | `FUT-PWR-02` | `FUT-TPL-01` |

The relation is not authorization to run. Every workflow starts inactive/preview-only and must re-check active context, data, academic rule, authority, EDENA tier, human route and stop conditions per mission.

## 10. Exact template registry

| Build ID | Canonical template name | Intended use |
|---|---|---|
| `FUT-TPL-01` | FUTURE Power Activation Card | Preview purpose, context, inputs, rules, EDENA, human review, workload, stop and removal plan. |
| `FUT-TPL-02` | SAFE Prompt Card | Situation, Aim, verified non-sensitive Facts, Expectations and required human review. |
| `FUT-TPL-03` | AI Use & Integrity Receipt | Record learner attempt/authorship, AI help, sources, edits, human review, disclosure and retention. |
| `FUT-TPL-04` | Synthetic Workflow Canvas | Prototype a low-risk workflow with synthetic inputs, gates, failures, fallback and rollback. |
| `FUT-TPL-05` | Portfolio Evidence Card | Truthfully describe capability, context, learner contribution, AI assistance and validation state. |

## 11. Baseline Discover recommendation translation

The baseline adapter accepts `DSC-WF-*` inventory IDs. Those are source recommendations, not FUTURE workflows, and numeric similarity is meaningless. For the baseline `prelicensure-support` starter only, catalog `FUTURE-CROSSLANE-1.0.0` permits these exact translations:

| Source inventory ID | Source intent used by the baseline role starter | FUTURE workflow | Power | Template |
|---|---|---|---|---|
| `DSC-WF-01` | mission and near-horizon focus | `FUT-WF-01` | `FUT-PWR-01` | `FUT-TPL-01` |
| `DSC-WF-02` | define a current need without premature solution lock-in | `FUT-WF-02` | `FUT-PWR-02` | `FUT-TPL-01` |
| `DSC-WF-08` | feasibility, burden and preparation questions | `FUT-WF-05` | `FUT-PWR-05` | `FUT-TPL-03` |
| `DSC-WF-23` | capability and future-development planning | `FUT-WF-13` | `FUT-PWR-15` | `FUT-TPL-05` |

Any other `DSC-WF-*` remains unresolved unless a reviewed catalog version explicitly maps it. Implementations must preserve the source ID, source catalog version/hash and resolved FUTURE relation in provenance. They must never strip a prefix, match numbers, infer a relation from a title, or silently fall back.

## 12. Capability translation

| Mission Profile recommendation | Criteria-model domain |
|---|---|
| `ai-literacy` | `ai_literacy` |
| `prompt-design` | `prompt_design` |
| `evidence-research` | `evidence_informed_research` |
| `critical-thinking` | `critical_thinking` |
| `structured-problem-solving` | `structured_problem_solving` |
| `workflow-design` | `workflow_design` |
| `project-management` | `project_management` |
| `privacy-stewardship` | `data_privacy_stewardship` |
| `ethical-ai` | `ethical_ai_practice` |
| `edena-governance` | `edena_governance` |
| `agent-supervision` | `agent_supervision` |
| `multi-agent` | `multi_agent_orchestration` |
| `knowledge-base` | `knowledge_base_development` |
| `automation-design` | `automation_design` |
| `artifact-creation` | `artifact_creation` |
| `evaluation-qi` | `evaluation_quality_improvement` |
| `role-development` | `role_specific_professional_development` |

A recommendation awards nothing. AI Literacy Passport stages and Mission Control badges require learner-produced, reviewed evidence. They are not school credentials, employer certifications, clinical competency determinations, licensure evidence, authorization to practice or examination guarantees.

## 13. Inactive agent recommendation mapping

Agent identifiers are build-layer records, not legacy-source identifiers. Personalization may recommend at most five by explicit declared task intent. Every recommendation object must also store `agent_permission_state=PERM-P0 Disabled`, `tool_state=disabled`, and `tool_ids=[]`. A recommendation does not activate an agent or grant a model, source, data class, memory category, tool, destination, schedule, connector, external action or permission.

| Declared support intent | Inactive agent candidate | Boundary |
|---|---|---|
| Direction, capacity, minimum mode or re-entry | `FUT-AGT-01` — Direction, Capacity & Re-entry Coach | Private low-sensitivity planning; no health diagnosis, financial transaction or schedule write. |
| Retrieval practice, study sprint or teach-back | `FUT-AGT-02` — Active Learning & Teach-Back Coach | Attempt before answer; source/rule check; no assessed-work completion or competence claim. |
| Fictional skills, role knowledge or certification rehearsal | `FUT-AGT-03` — Fictional Skills & Role-Knowledge Rehearsal | Fictional/approved generic content only; no live care, scope, delegation or sign-off. |
| Claim, citation or source verification | `FUT-AGT-04` — Evidence & Source Verification Scout | Public or explicitly approved sources; local applicability remains a human question. |
| SAFE prompting, privacy, integrity, bias or authority review | `FUT-AGT-05` — SAFE Prompt, Integrity & Boundary Sentinel | May block/route; cannot approve, declare compliance or infer authority. |
| Synthetic workflow, dashboard, accessibility or data prototype | `FUT-AGT-06` — Synthetic Workflow, UI & Data Sandbox Builder | Synthetic local non-production only; no connection, deployment or automation activation. |
| Career, portfolio, scholarship, job or bridge opportunity | `FUT-AGT-07` — Career, Portfolio & Opportunity Coach | Truthful public-source preparation; no eligibility decision, guarantee, purchase or submission. |
| Communication, mentorship, speaking-up or community rehearsal | `FUT-AGT-08` — Communication, Mentorship & Community Rehearsal | Private preparation in user voice; no send, contact or representation claim. |
| Future-of-nursing and responsible innovation exploration | `FUT-AGT-09` — Future-of-Nursing & Responsible Innovation Explorer | Public-source exploration distinct from clinical or production use. |
| Independent frozen-agent test, kill and reconciliation evidence | `FUT-AGT-10` — Independent Agent Auditor & Kill Sentinel | Separate control plane; never a friendly self-audit or a reason to activate another agent. |

An actual agent run is a separate future event: capability discovery, route preview, exact one-run charter, source/data/tool allowlist, EDENA decision, human checkpoints, time/output limits, stop/kill control and explicit approval. Personalization supplies none of these.

## 14. Semantic validation before persistence

The server must prove:

1. product, lane, namespace and route are exact;
2. exactly one workspace is Primary;
3. the active protected space and precise operational context resolve to exactly one partition and form a valid pair;
4. Bridge learning and work-growth content never transfer automatically;
5. every build-layer ID resolves uniquely to the pinned canonical name and content hash;
6. any source `DSC-WF-*` resolves only through the explicit cross-lane catalog;
7. all recommendations use `recommendations_only_inactive`;
8. each agent recommendation resolves to one pinned `FUT-AGT-*` record, all agent permissions remain `PERM-P0 Disabled`, `tool_ids=[]`, tool state is Disabled, and automation/external action remain manual-preview/off;
9. no identity, enrollment, employment, scope, delegation, supervision, competence, credential, policy compliance or result is inferred;
10. attempt-before-answer, learner authorship, applicable disclosure and source verification remain visible;
11. no PHI, person-level school/employer data, restricted assessment, secret or prohibited material is durable;
12. demo content is labeled and excluded from badges, credentials, analytics, institutional records and outcome claims;
13. memory remains Off/session-only until separate explicit consent; and
14. every approved user-visible field has complete provenance.

Test Discover-only, Soul-only, both consistent, both conflicting, neither, granular/unknown role labels, multiple/no Primary, context-transfer attempts, unsupported versions, invalid enums, catalog missing/duplicate/hash mismatch, prohibited content, demo exclusion, approve/edit/reject/delete/export and provenance completeness.
