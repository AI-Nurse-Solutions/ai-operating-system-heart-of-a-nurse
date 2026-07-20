# Nurse AI OS SOUL Quiz v2 — Role Constellation Design

**Status:** implementation specification

**Version:** 2.0.0

**Doctrine:** *Agents propose. Humans judge. Nurses steward.*

## 1. Design philosophy

The quiz discovers **one integrated professional soul expressed through multiple roles**. It never reduces a person to one job title, one archetype, or one permanent lane.

Five rules govern the design:

1. **One Core SOUL, many coordinated views.** Stable values, mission, approved memory, goals, preferences, and governance boundaries belong to one shared foundation. Mission Controls are context-specific views of that foundation—not separate personalities.
2. **Roles are congruent unless evidence shows tension.** A bedside nurse may also be a preceptor, quality contributor, graduate student, entrepreneur, family caregiver, and wellness advocate. The model identifies synergy and overload instead of forcing a choice.
3. **Declaration is not verification.** Role selection, confidence, interest, experience narratives, and aspirations do not verify employment, assignment, competence, credentials, licensure, privileges, or authority.
4. **Concise core, conditional depth.** Everyone completes a short core. Only modules linked to selected roles appear. Deep dives may be completed now or later, except required safety distinctions in the Student/Assistant lane.
5. **Capability-first, safety-bounded.** AI recommendations should expand learning, agency, creativity, and coordination while preserving academic integrity, authorized scope, supervision, privacy, and accountable human judgment.

The browser does not submit responses to a server. Draft state is held in `sessionStorage` for resilience during the open tab and can be cleared at any time. Durable continuity comes from locally downloaded SOUL artifacts, not silent cloud collection.

## 2. Role, identity, and developmental framework

The model separates dimensions that are commonly—and dangerously—collapsed:

| Dimension | Meaning | Interpretation rule |
|---|---|---|
| Primary role | Current center of attention, responsibility, or identity | Exactly one is declared for navigation; it is not a “winning archetype” |
| Supporting role | Regularly shapes work, learning, leadership, or decisions | Retained as a complementary identity |
| Emerging role | Intentionally developing toward | Never represented as current authority |
| Contextual role | Activates only in a setting, project, season, or assignment | Dashboard activation requires the relevant context and human authority |
| Developmental stage | Current learner/formation mode | Multiple stages may coexist |
| Advanced Studies | Credential, degree, specialization, renewal, or transition pathway | Cross-role overlay; never a separate identity |
| Current authorization | Self-reported scope, assignment, license, delegation, or supervision posture | Not independently verified by the quiz |
| Demonstrated competence | Evidence of supervised or formal demonstration | Stored separately from confidence; quiz does not verify it |
| Confidence | Self-reported comfort or readiness | May guide coaching; never grants authority |
| Formal credential | Self-reported credential status | Remains “not verified” unless a separate authorized process verifies it |
| Aspiration | Desired future role or capability | Drives learning pathways, not current permissions |

Supported developmental stages are: prelicensure student; nursing assistant/PCT; combined student and assistant; newly licensed clinician; experienced clinician; certification candidate; graduate/doctoral student; medical resident/fellow; emerging leader; entrepreneur/innovator; and lifelong learner.

The shared foundation also records which **Personal**, **Professional**, and **Community–Entrepreneurial** Mission Control environments—and the **Side Gig** and **Interest** sub-spheres—should coordinate around the same identity. These are context scopes, not separate personalities. Personal, Side Gig, and Interest are conservatively capped Green; Professional and Community–Entrepreneurial are capped Yellow during onboarding. A ceiling does not activate tools, permissions, connectors, memory, or agents.

## 3. Professional role taxonomy

The taxonomy is extensible and grouped into fourteen domains:

1. **Learning and professional formation:** prelicensure student, medical resident/fellow, certification candidate, graduate learner.
2. **Direct clinical care:** nursing assistant/PCT, newly licensed clinician, bedside nurse, allied health clinician.
3. **Advanced clinical practice:** advanced practice clinician, nurse practitioner, clinical nurse specialist, physician.
4. **Education and mentorship:** clinical preceptor, nurse educator, faculty/clinical instructor, simulation facilitator.
5. **Leadership and management:** charge nurse/team lead, nurse manager, healthcare leader.
6. **Administration and operations:** hospital administrator, clinic manager, healthcare operations/program manager.
7. **Quality, safety, and governance:** quality-improvement specialist, patient-safety/governance specialist.
8. **Research and evidence-based practice:** nurse researcher, evidence-based-practice specialist.
9. **Informatics, technology, and AI:** nurse informaticist, healthcare AI innovator/orchestrator, health-technology specialist.
10. **Innovation and product development:** clinical product/workflow developer.
11. **Entrepreneurship and business:** nurse entrepreneur, healthcare/wellness business owner.
12. **Community and population health:** community/population-health professional, organizer/program developer.
13. **Wellness and personal sustainability:** wellness manager, wellness coach/advocate, family caregiver.
14. **Advocacy and professional stewardship:** professional advocate/steward.

A respondent may add a generic local role title. Custom titles are local drafts, not NAIO-reviewed roles. The browser rejects obvious record identifiers and asks for a role title rather than a person, organization, or narrative.

## 4. Core quiz

The core is seven compact stages. Each question contributes directly to an output.

| Stage | Questions | Purpose and downstream use |
|---|---|---|
| 1. Stewardship gate | No PHI; human judgment; academic integrity; no credential inference | Hard gate for governance and AI behavior |
| 2. Role constellation | Select all roles; add optional local role; assign primary/supporting/emerging/contextual; rate attention, responsibility, identity salience, confidence; declare authorization, competence-evidence, and credential posture separately | Role scoring, branching, Soul Document, dashboards |
| 3. Development | Select active developmental stages; activate Advanced Studies when applicable | Learning pathways, conditional module, dashboard overlay |
| 4. Shared Core SOUL | Environments/spheres, values, mission, populations/systems served, shared goals, scheduling and commitment boundaries, motivations, strengths, working/learning styles, communication preferences | Stable identity and cross-dashboard coordination |
| 5. Decisions and capacity | Ten decision-style scales; pressures; load; protected wellness limit | AI interaction, tensions, overload alerts, wellness dashboard |
| 6. AI relationship and boundaries | AI modes; delegation matrix; approved/forbidden memory; escalation triggers | Agent recommendations, workflow posture, governance controls |
| 7. Role deep dives and results | Conditional modules; review; downloads | Role-specific context, coordinated dashboards, governed artifacts |

Core completion is meaningful with broad strokes. More complete answers improve personalization, but respondents may deepen optional modules after trust is established.

## 5. Conditional role modules

Modules are triggered by selected roles and deduplicated when several roles share a domain:

| Module | Trigger examples | Main outputs |
|---|---|---|
| Student and Assistant | Student and/or nursing assistant/PCT | Scope/supervision distinction, study and transition plan, learning dashboards |
| Direct Clinical Care | Bedside or newly licensed clinician | No-PHI professional-learning workflows, capacity support |
| Advanced Practice / Medical Training | APC, NP, CNS, resident/fellow, physician | Credential/supervision boundaries, development plan |
| Education and Mentorship | Educator, preceptor, faculty, simulation facilitator | Education dashboard, learner-impact review gates |
| Leadership and Management | Charge, manager, healthcare leader | Unit leadership dashboard, personnel/authority boundaries |
| Administration and Operations | Hospital administrator, clinic manager, operations leader | Administrative dashboard, institutional human gates |
| Quality, Safety, Research, and Evidence | QI, safety, governance, research, EBP | Research/QI uncertainty, data and oversight boundaries |
| Technology and Innovation | Informatics, AI, product/workflow development | Synthetic prototyping, EDENA review, deployment boundaries |
| Entrepreneurship and Business | Entrepreneur or business owner | Evidence-vs-aspiration, claims, conflict, transaction gates |
| Community and Advocacy | Population health, organizing, advocacy | Mandate/consent distinction, community safeguards |
| Wellness and Sustainability | Wellness role, caregiver, or high load | Capacity limits, recovery, escalation to human support |
| Advanced Studies | Any active credential, degree, specialization, renewal, or transition | Cross-role learning overlay |

Generic modules ask only about current context, responsibilities, authority source, priorities, pressures, evidence, intended outcomes, appropriate AI support, and human-review boundaries. They do not request patient, learner, employee, participant, or other protected records.

## 6. Prelicensure Nursing Student and Nursing Assistant module

This is one coordinated lane with two distinct role records. A respondent identifies whether they are a student, nursing assistant/PCT, or both.

Grouped questions assess:

1. Program type and current stage, when applicable.
2. Training, certification, employment, and clinical-placement status.
3. Care environment and current assigned responsibilities.
4. Authorized scope and how it is defined in each setting.
5. Delegated duties and the accountable delegating role.
6. Required supervision, escalation, and chain of command.
7. Clinical-placement, simulation, and frontline-care experience without identifiable details.
8. Foundational caregiving, communication, teamwork, infection-prevention, safety, handoff, and documentation learning.
9. Clinical-reasoning development, self-reported confidence, and evidence of supervised competence as separate fields.
10. Study habits, strengths, gaps, preferred learning methods, entrance/progression needs, skills milestones, graduation, and NCLEX preparation.
11. Work-school-family-scheduling pressures, stress, wellness, burnout risk, and faculty/preceptor/supervisor/mentor needs.
12. Career interests, specialty preferences, and transition goals.
13. AI boundaries across academic, employment, simulation, and supervised clinical settings.

Transitions may include admission, program progression, assistant certification, clinical requirements, graduation, NCLEX, initial licensure, specialty preparation, and longer-term movement toward advanced practice, leadership, education, research, innovation, or entrepreneurship.

The output recognizes current contribution to patient care while labeling developing capabilities as developing. It never turns simulation, confidence, study, or employment experience into verified professional competence.

## 7. Advanced Studies cross-role module

Advanced Studies activates as an overlay whenever a person is pursuing a certification, credential, degree, specialization, renewal, residency/fellowship, continuing education, structured development, or career transition.

For each pathway, the quiz records:

- pathway type and target;
- motivation and intended professional outcome;
- preparation stage;
- required competencies and milestone dates;
- evidence of progress, knowledge gaps, and competency gaps;
- learning priorities and preferred formats;
- available time and scheduling constraints;
- accountability, coaching, and mentorship needs;
- relationship to other roles;
- financial, workload, family, institutional, and wellness barriers;
- opportunities for safe application;
- continuing-education or renewal requirements;
- academic-integrity and responsible-AI boundaries.

A person may add more than one pathway. Each remains self-reported and unverified. Advanced Studies coordinates with role dashboards but never replaces them.

## 8. Answer formats and response scales

- **Role selection:** multi-select grouped by domain.
- **Role status:** one status per selected role; exactly one primary role.
- **Role intensity:** four independent 1–5 scales for attention, responsibility, identity salience, and confidence.
- **Authorization/evidence:** controlled choices that explicitly include “self-reported/not verified” and “not assessed.”
- **Values/motivations/styles/pressures/AI modes:** multi-select with optional short generic additions.
- **Decision style:** ten 1–5 scales. Labels describe preference—not quality or competence.
- **Delegation:** bounded governance-level choices; unsafe requests are clamped to the minimum human-oversight floor.
- **Forced priorities:** one primary role and one primary AI mode.
- **Short reflections:** mission, strengths, protected wellness limit, module-specific context.
- **Dates:** optional milestone date only; no date of birth or personal identifiers.
- **Optional deep dives:** conditional modules may be deferred, except required student/assistant scope and safety distinctions.

Scale anchors:

- **1:** rarely / low / strongly prefers the left-hand posture.
- **3:** situational / balanced / depends on context.
- **5:** consistently / high / strongly prefers the right-hand posture.

No scale is interpreted as licensure, competence, fitness, performance, readiness, or authority.

## 9. Multidimensional scoring methodology

No single archetype is calculated.

For each selected role:

`role intensity = status base + (attention × 4) + (responsibility × 5) + (identity salience × 3)`

Status bases:

- primary: 100;
- supporting: 70;
- emerging: 50;
- contextual: 35.

The declared status remains authoritative; intensity orders roles only within their declared status. Confidence is displayed but excluded from the role-intensity calculation so high confidence cannot be converted into professional authority.

Separate dimensions are retained for:

- current authorization posture;
- competence evidence posture;
- confidence;
- credential posture;
- developmental stage;
- Advanced Studies status;
- motivations and values;
- work and learning styles;
- decision preferences;
- pressures and wellness load;
- AI operating modes;
- governance requirements.

Rule-based interpretation adds **synergies** when domains complement each other and **tensions** when workload, role boundaries, commercial conflicts, academic duties, or capacity constraints may collide. These are prompts for human reflection, not diagnoses.

## 10. Role-constellation interpretation rules

1. Respect the respondent’s declared role status; do not silently reclassify it.
2. Require exactly one primary role for current navigation, while preserving all other roles.
3. Treat supporting roles as current complementary responsibilities.
4. Treat emerging roles as developing or aspirational; never grant their authority.
5. Treat contextual roles as inactive until their stated context and human authority are current.
6. Show current authorization, competence evidence, confidence, credential posture, and aspiration separately.
7. Label all quiz claims “self-reported, not independently verified.”
8. Never infer scope from profession alone; jurisdiction, institution, policy, delegation, privileges, and supervision remain controlling.
9. Detect role synergy without romanticizing overload.
10. If information is missing or contradictory, label uncertainty and request clarification.
11. Add Advanced Studies beside—not above—the person’s roles.
12. Recommend dashboards as A0 configuration drafts; no tools, connectors, memory writes, schedules, messages, publications, or automations are activated.

## 11. Soul Document output template

```text
Core SOUL
├── Identity and mission
├── Core values
├── People, populations, and systems served
├── Mission Control environments and sub-spheres
├── Shared near-term goals
├── Scheduling and commitment boundaries
├── Motivations and strengths
├── Working, learning, collaboration, and communication preferences
├── Primary roles
├── Supporting roles
├── Emerging roles
├── Contextual roles
├── Developmental stages
├── Advanced Studies pathways
├── Role synergies
├── Potential tensions and overload
├── Responsibilities and pressures
├── Wellness and sustainability limits
├── AI relationship
├── What AI may do privately and reversibly
├── What requires confirmation
├── What requires supervision or accountable judgment
├── What AI must never do
├── Approved memory
├── Forbidden memory
└── Escalation triggers
```

Generated files:

- `Core-SOUL.md` — stable shared foundation;
- `Role-Constellation.md` — multidimensional role interpretation;
- `Role-Context-Deep-Dives.md` — self-reported role-module answers kept separate from verification;
- `Advanced-Studies-SOUL.md` — generated only when active;
- `Mission-Control-Recommendations.md` — coordinated dashboard specifications;
- `AI-Governance-Profile.md` — delegation, memory, review, and escalation boundaries;
- `SOUL-Profile-Metadata.md` — version, review triggers, and update process;
- `naio-soul.json` — machine-readable v2 export with a v1 compatibility bridge.

The v2 JSON keeps the legacy identity-role field for existing import workflows but makes `role_constellation` authoritative for multidimensional identity.

Import is fail-closed. `import-soul.py` requires the pinned non-GPL JSON Schema validator dependencies in `naio-os/requirements-import-soul.txt`, checks the Draft-07 schema itself, enables RFC-3339 date-time format validation, and refuses when the validator or schema is unavailable. Duplicate JSON keys, unknown schema versions, v1/v2 hybrids, mismatched v2 sphere and tier-ceiling keys, and duplicate constellation role IDs are refused before any write; dry-run remains the only supported mode.

## 12. Mission Control dashboard recommendation logic

Role-to-dashboard mappings are many-to-many. Recommendations are deduplicated and coordinated through `sharedFoundation: one-core-soul`.

Dashboard recommendation signals:

- selected role and declared status;
- role domain;
- developmental stage;
- active Advanced Studies pathway;
- high workload or wellness pressure;
- preferred AI relationship;
- conditional-module priorities.

Each dashboard recommendation contains:

- dashboard name and purpose;
- roles supported;
- primary objectives and current priorities;
- information requirements;
- recommended agents and workflows;
- learning/competency goals and milestones;
- performance indicators;
- permissions and data boundaries;
- human-review requirements and safeguards;
- relationship to other dashboards.

Every recommendation is **A0 recommendation-only** and **EDENA not evaluated** until a separate governance process establishes the context, accountable owner, permissions, data posture, and human gates.

Advanced Studies is always an overlay. For example, a nurse manager pursuing a doctorate may receive Unit Leadership and Operations, Advanced Studies and Certification, Graduate Degree and Research, Quality/Safety/Governance, and Wellness/Sustainability views—all sharing one identity and wellness limit.

## 13. AI-agent and workflow recommendation logic

Available operating modes are teacher, tutor, coach, mentor, research assistant, thought partner, creative collaborator, administrative assistant, project manager, workflow coordinator, analyst, simulation facilitator, strategic advisor, governance monitor, and automation agent.

Recommendations combine:

1. modes explicitly selected by the respondent;
2. safe defaults associated with recommended dashboards;
3. Advanced Studies supports such as tutor, coach, and project manager;
4. governance-monitor support for high-boundary domains.

Each recommendation includes a purpose, sample workflows, a human gate, and `activation: not-authorized`. Automation remains off unless a separate task-level review defines the exact action, data, authority, risk tier, autonomy level, confirmation step, monitoring, and rollback.

Governance floors prevent the user interface from weakening mandatory safeguards:

- public no-PHI summaries and private reversible plans may be performed locally;
- external actions require explicit confirmation;
- learner/personnel/evaluative work requires professional supervision or accountable judgment;
- institutional changes require accountable human authority;
- patient-specific clinical decisions and fabricated credential/competence claims are never delegated.

## 14. Example result

### Multi-hat professional pursuing an advanced credential

**Declared constellation**

- Primary: Bedside Nurse.
- Supporting: Clinical Preceptor; Quality Improvement Specialist.
- Emerging: Nurse Entrepreneur.
- Contextual: Family Caregiver and Wellness Advocate.
- Development: Experienced Clinician; Certification Candidate; Entrepreneur/Innovator.
- Advanced Studies: CCRN preparation.

**Shared values:** dignity, evidence, family, growth, stewardship.

**Mission:** serve critically ill adults indirectly through safe practice preparation, strengthen newer clinicians, and improve unit learning.

**Synergies:** bedside experience strengthens teaching; quality work disciplines evidence; CCRN study can support both bedside learning and preceptor preparation.

**Tensions:** night shifts, family caregiving, study, quality responsibilities, and venture development compete for recovery time; clinical/employer information must remain separate from commercial work.

**Coordinated Mission Controls**

1. Bedside Clinical Command — no-PHI learning and professional preparation.
2. Education and Mentorship — synthetic teaching plans and feedback preparation.
3. Quality, Safety, and Governance — public/synthetic evidence and human-reviewed improvement preparation.
4. Advanced Studies and Certification — CCRN milestones, practice, accountability, and protected study time.
5. Entrepreneurship and Business — evidence, offer, and product planning with claim and conflict gates.
6. Wellness and Personal Sustainability — sleep, caregiving, workload, and recovery limits.

**AI modes:** tutor, research assistant, project manager, governance monitor.

**Human gates:** no patient-specific work; no employer-confidential data; no QI/research determination; no commercial clinical claims; no external action without confirmation; no credential claim until awarded and separately verified where necessary.

## 15. Example result

### Prelicensure student who also works as a nursing assistant

**Declared constellation**

- Primary: Prelicensure Nursing Student.
- Supporting: Nursing Assistant/PCT.
- Emerging: Bedside Nurse.
- Contextual: Family Caregiver.
- Development: Combined Student and Nursing Assistant; NCLEX pathway not yet active until the appropriate program stage.

**Current contribution:** performs assigned nursing-support duties in an employment context under the applicable delegation and supervision rules.

**Developing capability:** clinical reasoning, nursing knowledge, simulation performance, and professional nursing responsibilities are developing within the education program.

**Authority distinction:** nursing-assistant employment does not create student-nurse or licensed-nurse authority; student clinical experiences do not independently expand employment scope.

**Coordinated Mission Controls**

1. Student and Nursing Assistant Bridge Mission Control — appears only when both roles are selected and keeps education and employment responsibilities distinct.
2. Clinical Learning, Skills, and Simulation — synthetic preparation, communication rehearsal, and supervised debriefing.
3. Education, Certification, and NCLEX Preparation — current program milestones; NCLEX activates when applicable.
4. Work-School-Wellness Coordination — shifts, clinical days, study, caregiving, recovery, and faculty/supervisor support.

**AI modes:** tutor, simulation facilitator, coach, project manager, governance monitor.

**Human gates:** no PHI; no prohibited assignment completion; no fabricated clinical hours or competencies; no unsupervised clinical authority; faculty, preceptor, nurse, and supervisor oversight remain required; confidence remains separate from demonstrated competence.

## 16. Privacy, academic-integrity, clinical-safety, and governance safeguards

### Privacy and minimization

- No patient-identifiable information, screenshots, narratives, records, or dates tied to patients.
- No student, employee, participant, peer-review, incident, personnel, or employer-confidential records.
- No passwords, API keys, tokens, private keys, recovery codes, or connection details.
- Use generic role and setting labels; no legal name is required.
- Browser draft state uses session-only storage; local exports are controlled by the respondent.
- Approved memory is explicit, minimal, editable, and separable from forbidden memory.

### Academic integrity

- AI may explain, quiz, coach, plan, rehearse, and provide feedback within program rules.
- AI may not impersonate the learner, complete prohibited work, fabricate citations, clinical hours, experiences, assessments, competencies, or accomplishments.
- Grading, progression, accommodation, admission, evaluation, and credentialing remain with authorized humans and institutions.

### Clinical and scope safety

- The quiz is no-PHI and does not become a clinical decision-support, documentation, ordering, EHR, staffing, or operational system.
- Students, assistants, trainees, and professionals remain bound by applicable law, policy, privileges, delegation, supervision, education rules, and institutional authority.
- Education, simulation, interest, and confidence do not create independent clinical authority.
- AI must stop when patient-specific content appears.

### Governance

- Consequential, external, evaluative, employment, institutional, financial, legal, clinical, and academic actions retain human gates.
- Missing or contradictory information is labeled uncertain; the system asks rather than invents.
- Role and dashboard recommendations are self-reported configuration drafts, not EDENA assessments or authority envelopes.
- No agent, connector, memory rule, cron job, publication, message, schedule, transaction, or automation is activated by taking the quiz.
- Safety-first, then nurses-first, then learning/revenue.

## 17. Process for periodically reviewing and updating the profile

Review the profile:

- every three months;
- when a role starts, ends, or changes status;
- when assignment, scope, supervision, privileges, or institutional context changes;
- when a credential, degree, certification, renewal, residency, fellowship, or milestone changes;
- when workload, caregiving, wellness, or available capacity changes materially;
- when AI behavior feels misaligned;
- after any privacy, integrity, safety, scope, or boundary concern.

Update workflow:

1. Review the existing Core SOUL and role constellation before retaking anything.
2. Mark each fact as stable, changed, uncertain, or no longer relevant.
3. Update role statuses, developmental stages, and Advanced Studies pathways.
4. Reconfirm authority, competence-evidence, confidence, and credential fields separately.
5. Revisit values and mission only if they genuinely changed.
6. Recalculate dashboard and agent recommendations.
7. Review privacy, memory, delegation, human gates, and escalation triggers.
8. Compare the new export with the prior version before replacing it.
9. Preserve a dated local backup and rollback path.
10. Ask the accountable human when a claim, scope, credential, or boundary is uncertain.

Core values may remain stable while roles, competencies, credentials, permissions, pressures, goals, and priorities evolve. The quiz supports that continuity without freezing the person in one season.
