# FUTURE Starter Workspace Crosswalk

## Starter contract

Starters are optional, synthetic and reviewable shells for Nursing Students, Nursing Assistants/CNAs/PCTs/PCAs/UAPs/care aides, and Bridge learners. They create no enrollment, employment, course submission, patient record, clinical assignment, delegation, scope, competency, certification, licensure, academic approval, employer approval or external action.

The user must choose Nursing Student, Nursing Assistant or Bridge and exactly one **Primary** workspace. Other workspaces may be Supporting, Emerging or Contextual. Each workspace belongs to one protected context: Learning, Work growth, Life, or Community and future. Bridge learning and work-growth partitions do not exchange content automatically.

The user may preview, edit, adopt or decline each starter independently. Adoption creates local draft cards only. All recommended workflows and powers remain inactive. A starter may show a bounded agent candidate by task intent, but every agent remains `PERM-P0 Disabled` with no run or permission; tools remain Disabled with empty IDs. Connectors, sharing, external actions and background automation remain off.

The IDs below are build-layer catalog identifiers bound to the exact canonical names in `FUTURE-Personalization-Mapping-Crosswalk.md`; the canonical v1 source did not contain PWR/WF/TPL machine IDs.

## Role-workspace starters

| Workspace type | Starter and initial modules | Inactive candidate relation | Questions required before adoption | Hard stop |
|---|---|---|---|---|
| `nursing_student_academic_learning` | Learning Studio: targets, retrieval schedule, teach-back, source status, human-question queue, integrity receipts | `FUT-WF-03→FUT-PWR-04→FUT-TPL-03`; `FUT-WF-07→FUT-PWR-09→FUT-TPL-03`; `FUT-WF-10→FUT-PWR-07→FUT-TPL-02` | What type of learner context is declared? Which current course and AI-use rules apply? Is the task practice, permitted support or restricted assessment? Who is the authorized faculty route? | No live exam, restricted assessment, answer key, deceptive completion, ghost authorship, fabricated source/reflection or claim of academic permission. |
| `nursing_student_skills_clinical_rehearsal` | Supervised Readiness Rehearsal: approved-source list, fictional scenario, checklist questions, prebrief/debrief, faculty/preceptor route | `FUT-WF-04→FUT-PWR-05→FUT-TPL-03`; `FUT-WF-05→FUT-PWR-05→FUT-TPL-03` | Is this general knowledge, fictional simulation or approved skills-lab preparation? Which source version and human supervisor govern? What must remain outside the system? | No live patient, clinical direction, diagnosis/treatment, medication/device advice, documentation, performance sign-off or competency determination. |
| `nursing_assistant_role_learning` | Role Learning Compass: exact local title, rule status, general concepts, delegation questions, supervisor route | `FUT-WF-04→FUT-PWR-05→FUT-TPL-03`; `FUT-WF-05→FUT-PWR-05→FUT-TPL-03`; `FUT-WF-08→FUT-PWR-08→FUT-TPL-03` | What exact local title does the user declare? Which employer policy, scope source, delegation pathway and supervisor are current? What is unknown? | A generic CNA/PCT/PCA/UAP/care-aide title never determines scope. No patient question, task authorization, assignment, delegation, care advice or competence claim. |
| `nursing_assistant_work_growth` | Work-Growth Lane: professional questions, communication rehearsal, truthful portfolio, next learning step | `FUT-WF-15→FUT-PWR-14→FUT-TPL-03`; `FUT-WF-14→FUT-PWR-13→FUT-TPL-05`; `FUT-WF-01→FUT-PWR-01→FUT-TPL-01` | Which goal is private professional growth? What employer rules apply? Which supervisor or educator can verify claims? What information must not enter? | No patient, worker, investigation, grievance, accommodation, discipline or employer-confidential data; no employment recommendation or external message without review. |
| `bridge_academic_learning` | Bridge Learning Studio: 90-day learning map, prerequisites, study sprints, school-rule queue, application evidence | `FUT-WF-13→FUT-PWR-15→FUT-TPL-05`; `FUT-WF-03→FUT-PWR-04→FUT-TPL-03`; `FUT-WF-07→FUT-PWR-09→FUT-TPL-03` | Is this exploration or a declared current program? Which requirements are from current official sources? Which school content may be used? Which work experiences may be truthfully described without confidential details? | No enrollment/eligibility/admission inference, no application submission, no fabricated experience or credential, and no transfer from work partition without deliberate deidentification and review. |
| `bridge_work_growth` | Bridge Work-Growth Lane: current-role boundaries, work-school logistics, supervisor conversation, truthful transferable-skills inventory | `FUT-WF-02→FUT-PWR-02→FUT-TPL-01`; `FUT-WF-15→FUT-PWR-14→FUT-TPL-03`; `FUT-WF-13→FUT-PWR-15→FUT-TPL-05` | What is the current local role? Which schedule facts are owner-private and non-sensitive? Which skills are self-described versus human-validated? What supervisor route exists? | No person/patient/employer record, scope widening, delegation assumption, schedule action, performance claim or automatic transfer into school materials. |
| `certification_licensure_preparation` | Knowledge-Gap Studio: official blueprint/source status, retrieval map, practice errors, human questions | `FUT-WF-06→FUT-PWR-06→FUT-TPL-03`; `FUT-WF-08→FUT-PWR-08→FUT-TPL-03`; `FUT-WF-10→FUT-PWR-07→FUT-TPL-02` | Which exam/certification/licensure goal is declared? What current official blueprint and eligibility source apply? Are practice materials permitted? | No live/restricted exam content, leaked questions, pass/eligibility guarantee, credential claim, competence determination or unauthorized content reproduction. |
| `career_portfolio_opportunity` | Opportunity Studio: verified requirements, truthful evidence cards, résumé/interview/application drafts, disclosure and reviewer queue | `FUT-WF-13→FUT-PWR-15→FUT-TPL-05`; `FUT-WF-14→FUT-PWR-13→FUT-TPL-05`; `FUT-WF-15→FUT-PWR-14→FUT-TPL-03` | Which opportunity and official source? What did the learner actually do? What evidence is self-authored, AI-assisted, human-reviewed or institution-validated? | No invented role, hours, skills, competency, certification, licensure, reference, signature, award or submission. |
| `private_life_capacity` | Private Capacity and Recovery: current season, capacity mode, Top Three, minimum/re-entry plan, money/logistics questions | `FUT-WF-02→FUT-PWR-02→FUT-TPL-01`; `FUT-WF-18→FUT-PWR-03→FUT-TPL-01`; `FUT-WF-01→FUT-PWR-01→FUT-TPL-01` | What is owner-private? What may be retained, for how long, and what must never enter school/work? Which issue needs a qualified human rather than AI? | No school/employer visibility by default, no diagnosis or crisis substitution, no financial transaction, schedule change or hidden retention. |
| `community_leadership_future` | Service Project Studio: public need, consent and stakeholder questions, accessible draft, burden/fairness review, human approval route | `FUT-WF-16→FUT-PWR-17→FUT-TPL-04`; `FUT-WF-15→FUT-PWR-16→FUT-TPL-03`; `FUT-WF-08→FUT-PWR-08→FUT-TPL-03` | Who invited or owns the project? What public/consent-based information is allowed? Who reviews content, accessibility, claims and outreach? | No person targeting, surveillance, patient advice, community representation claim, public posting, outreach, event commitment or health-education release without authorized review. |
| `personal_technology_innovation_sandbox` | Synthetic Technology Lab: SAFE prompt, workflow canvas, accessible prototype, red-team findings, rollback plan | `FUT-WF-11→FUT-PWR-10→FUT-TPL-04`; `FUT-WF-12→FUT-PWR-11→FUT-TPL-04`; `FUT-WF-09→FUT-PWR-09→FUT-TPL-03`; `FUT-WF-17→FUT-PWR-18→FUT-TPL-05` | Is the problem personal and low-risk? Are all inputs synthetic/public? What human factor, accessibility, bias, privacy, failure and rollback tests apply? | No production/school/employer system connection, no PHI/person data, no autonomous agent, no deployment, monitoring or claim that a prototype is validated. |

The human-readable relation `workflow→power→template` is stored as distinct full IDs plus pinned catalog version and hash. It must be resolved from the catalog, never reconstructed from the numbers.

## Pathway selection logic

| Declared pathway | Required candidate behavior | Non-inference rule |
|---|---|---|
| Nursing Student | Offer academic learning first; skills rehearsal only as a separate optional workspace. | Declared pathway does not prove enrollment, standing, course permission or clinical placement. |
| Nursing Assistant | Ask the exact local title before offering role-learning/work-growth starters. | Title does not determine scope, delegation, competency, certification or employer permission. |
| Bridge | Offer separate academic-learning and work-growth candidates; user chooses one Primary. | Never move work information into school or school information into work automatically. |
| Unresolved | Offer only `private_life_capacity` in synthetic preview, then ask. | Do not force a learner or employment identity. |

## Situation overlays

Situation overlays add questions and inactive launcher candidates to one selected workspace. They do not create authority, permission or a real-world record.

| Situation | Inactive workflow candidate | Review prompts | Mandatory stop or escalation |
|---|---|---|---|
| `new_term_or_course` | `FUT-WF-01`, `FUT-WF-03`, `FUT-WF-07` | What current syllabus/AI-use rule and human contact govern? What is learner-authored? | Unknown assessment rules block AI help beyond general coaching. |
| `upcoming_skills_lab` | `FUT-WF-05` | Which approved current checklist and supervisor govern? Is the scenario fictional/lab-only? | Live care, patient content or sign-off request stops the workflow. |
| `certification_exam_preparation` | `FUT-WF-06`, `FUT-WF-08` | Which official blueprint and permitted practice source apply? | Live/restricted content, leaked items or pass/eligibility claim is blocked. |
| `work_school_balance` | `FUT-WF-02`, `FUT-WF-18` | What non-sensitive commitments, capacity mode and recovery protections matter? | No employer/school record import or schedule action. |
| `bridge_transition` | `FUT-WF-13`, `FUT-WF-14` | Which requirements are current and official? What evidence is truthful and reviewable? | No admission, credit-transfer, eligibility or credential conclusion. |
| `employment_transition` | `FUT-WF-13`, `FUT-WF-14`, `FUT-WF-15` | Which posting/source is current? What may be claimed? Who reviews? | No application submission, reference contact or fabricated qualification. |
| `faculty_or_supervisor_conversation` | `FUT-WF-15` | What question, authority gap, desired tone and human route apply? | No sending, impersonation, retaliation prediction or policy conclusion. |
| `graded_work_integrity_question` | `FUT-WF-07` | What exact rule is verified? What has the learner already attempted? | Unknown/prohibitive rule limits support to clarification and routing. |
| `learning_gap` | `FUT-WF-03`, `FUT-WF-06` | What evidence shows a gap? Which source and independent task fit? | No competency, diagnosis or pass-probability claim. |
| `source_conflict` | `FUT-WF-08` | Which authority, edition/date and conflict apply? Who resolves local use? | No fabricated citation or silent conflict resolution. |
| `overload_reentry` | `FUT-WF-18` | What can be paused? What is the smallest safe next step and human support? | Urgent safety, crisis or health concern routes to appropriate humans/emergency process; AI does not diagnose. |
| `community_project` | `FUT-WF-16` | Who invited/owns it? What consent, accessibility and review apply? | No outreach, public content or person-level data. |
| `future_technology_exploration` | `FUT-WF-11`, `FUT-WF-12`, `FUT-WF-17` | What synthetic sandbox, intended learning and rollback exist? | No real-system connection, deployment or autonomous agent. |
| `other_reviewed` | None until reviewed | Preserve user wording and uncertainty; ask which protected context applies. | Unknown context keeps dependent recommendations blocked. |

## Goal and evidence isolation

Global near-, medium- and long-term goals live once. Each workspace contains only its own goals, rules, sources and artifacts. Moving content between workspaces is a visible user-confirmed edit with new provenance and a data/authority check.

Learning artifacts can show attempt, reasoning, corrections, sources and reflection. They do not prove clinical competence. Portfolio status must remain one of: Self-authored, AI-assisted, Human-reviewed, or Institution-validated. Only the responsible institution can apply its validation, and FUTURE must not infer it.

## Adoption, clearing and restoration

- **Preview:** show a synthetic shell and mapping reason without saving.
- **Adopt draft:** require confirmation and create local draft structure only.
- **Decline:** create no negative inference or penalty.
- **Clear:** remove starter cards without deleting user-authored missions.
- **Restore:** validate schema/catalog/version and never restore expired authority as current.
- **Export:** label demo and AI-assisted content; exclude it from credential, competency, academic, employment and outcome claims.

Changing the Primary workspace or active context requires confirmation. A changed role, context, data class, source, audience, destination, permission, memory, connector, sharing or automation state cancels prior approval.
