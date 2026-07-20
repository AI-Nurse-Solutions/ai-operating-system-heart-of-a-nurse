/* Nurse AI OS SOUL Quiz v2 — deterministic, browser-local role constellation model. */

export const SCHEMA_VERSION = 2;
export const STORAGE_KEY = 'naio.soul-quiz.constellation.v2';
export const ROLE_STATUSES = Object.freeze(['primary', 'supporting', 'emerging', 'contextual']);
export const AUTHORIZATION_VALUES = Object.freeze(['self-declared', 'in-training-supervised', 'delegated-role-unverified', 'formally-assigned-unverified', 'licensed-or-credentialed-unverified', 'not-current']);
export const COMPETENCE_EVIDENCE_VALUES = Object.freeze(['not-assessed', 'developing-not-verified', 'supervised-demonstration-not-verified', 'self-reported-practice-not-verified', 'formal-verification-not-imported']);
export const CREDENTIAL_STATUS_VALUES = Object.freeze(['not-claimed', 'in-progress-not-verified', 'aspirational-not-verified', 'self-reported-not-verified']);
export const STUDY_STAGE_VALUES = Object.freeze(['exploring', 'admission-or-application', 'enrolled', 'active-preparation', 'milestone-review', 'exam-ready-self-reported', 'renewal', 'paused']);
export const GOVERNANCE_LEVELS = Object.freeze([
  'independent-private',
  'prepare-only',
  'explicit-confirmation',
  'professional-supervision',
  'accountable-human-judgment',
  'licensed-human-judgment',
  'never-delegate'
]);

export const ROLE_DOMAINS = Object.freeze([
  { id: 'learning-formation', label: 'Learning and professional formation' },
  { id: 'direct-clinical-care', label: 'Direct clinical care' },
  { id: 'advanced-clinical-practice', label: 'Advanced clinical practice' },
  { id: 'education-mentorship', label: 'Education and mentorship' },
  { id: 'leadership-management', label: 'Leadership and management' },
  { id: 'administration-operations', label: 'Administration and operations' },
  { id: 'quality-safety-governance', label: 'Quality, safety, and governance' },
  { id: 'research-evidence', label: 'Research and evidence-based practice' },
  { id: 'informatics-technology-ai', label: 'Informatics, technology, and AI' },
  { id: 'innovation-product', label: 'Innovation and product development' },
  { id: 'entrepreneurship-business', label: 'Entrepreneurship and business' },
  { id: 'community-population-health', label: 'Community and population health' },
  { id: 'wellness-sustainability', label: 'Wellness and personal sustainability' },
  { id: 'advocacy-stewardship', label: 'Advocacy and professional stewardship' }
]);

const AUTHORITY_DISCLAIMER = 'Selection is self-reported and verifies no credential, competence, appointment, assignment, employment, license, institutional permission, or professional authority.';

function role(id, label, domainId, moduleId, dashboardIds, legacyRole = 'other', extra = {}) {
  return Object.freeze({ id, label, domainId, moduleId, dashboardIds: Object.freeze([...dashboardIds]), legacyRole, authorityDisclaimer: AUTHORITY_DISCLAIMER, ...extra });
}

export const ROLE_TAXONOMY = Object.freeze([
  role('prelicensure-nursing-student', 'Prelicensure Nursing Student', 'learning-formation', 'student-assistant', ['prelicensure-student', 'clinical-learning-simulation', 'education-certification-nclex', 'work-school-wellness'], 'student'),
  role('nursing-assistant-pct', 'Nursing Assistant / CNA / PCT / Healthcare Assistant', 'direct-clinical-care', 'student-assistant', ['nursing-assistant-workforce', 'clinical-learning-simulation', 'work-school-wellness'], 'staff'),
  role('newly-licensed-clinician', 'Newly Licensed Clinician', 'direct-clinical-care', 'clinical-care', ['bedside-clinical-command', 'clinical-learning-simulation', 'wellness-sustainability'], 'staff'),
  role('bedside-nurse', 'Bedside Nurse', 'direct-clinical-care', 'clinical-care', ['bedside-clinical-command', 'wellness-sustainability'], 'staff'),
  role('allied-health-clinician', 'Allied Health Clinician', 'direct-clinical-care', 'clinical-care', ['bedside-clinical-command', 'wellness-sustainability'], 'other'),
  role('advanced-practice-clinician', 'Advanced Practice Clinician', 'advanced-clinical-practice', 'advanced-practice', ['advanced-practice', 'advanced-studies-certification'], 'staff'),
  role('nurse-practitioner', 'Nurse Practitioner', 'advanced-clinical-practice', 'advanced-practice', ['advanced-practice', 'advanced-studies-certification'], 'staff'),
  role('clinical-nurse-specialist', 'Clinical Nurse Specialist', 'advanced-clinical-practice', 'advanced-practice', ['advanced-practice', 'quality-safety-governance', 'education-mentorship'], 'staff'),
  role('medical-resident-fellow', 'Medical Resident / Fellow', 'learning-formation', 'advanced-practice', ['clinical-learning-simulation', 'advanced-studies-certification', 'wellness-sustainability'], 'other'),
  role('physician', 'Physician', 'advanced-clinical-practice', 'advanced-practice', ['advanced-practice', 'research-evidence'], 'other'),
  role('clinical-preceptor', 'Clinical Preceptor', 'education-mentorship', 'education-mentorship', ['education-mentorship', 'clinical-learning-simulation'], 'leader'),
  role('nurse-educator', 'Nurse Educator', 'education-mentorship', 'education-mentorship', ['education-mentorship', 'advanced-studies-certification'], 'leader'),
  role('faculty-instructor', 'Faculty / Clinical Instructor', 'education-mentorship', 'education-mentorship', ['education-mentorship', 'graduate-degree-research'], 'leader'),
  role('simulation-facilitator', 'Simulation Facilitator', 'education-mentorship', 'education-mentorship', ['clinical-learning-simulation', 'education-mentorship'], 'leader'),
  role('nurse-manager', 'Nurse Manager', 'leadership-management', 'leadership-management', ['unit-leadership-operations', 'quality-safety-governance', 'wellness-sustainability'], 'leader'),
  role('healthcare-leader', 'Healthcare Leader', 'leadership-management', 'leadership-management', ['unit-leadership-operations', 'quality-safety-governance'], 'leader'),
  role('charge-nurse-team-lead', 'Charge Nurse / Team Lead', 'leadership-management', 'leadership-management', ['unit-leadership-operations', 'bedside-clinical-command'], 'leader'),
  role('hospital-administrator', 'Hospital Administrator', 'administration-operations', 'administration-operations', ['hospital-administration', 'quality-safety-governance'], 'leader'),
  role('clinic-manager', 'Clinic Manager', 'administration-operations', 'administration-operations', ['clinic-management', 'quality-safety-governance'], 'leader'),
  role('operations-program-manager', 'Healthcare Operations / Program Manager', 'administration-operations', 'administration-operations', ['hospital-administration', 'clinic-management'], 'leader'),
  role('quality-improvement-specialist', 'Quality Improvement Specialist', 'quality-safety-governance', 'quality-research', ['quality-safety-governance', 'research-evidence'], 'leader'),
  role('patient-safety-governance-specialist', 'Patient Safety / Governance Specialist', 'quality-safety-governance', 'quality-research', ['quality-safety-governance'], 'leader'),
  role('nurse-researcher', 'Nurse Researcher', 'research-evidence', 'quality-research', ['research-evidence', 'graduate-degree-research'], 'other'),
  role('evidence-practice-specialist', 'Evidence-Based Practice Specialist', 'research-evidence', 'quality-research', ['research-evidence', 'quality-safety-governance'], 'other'),
  role('nurse-informaticist', 'Nurse Informaticist', 'informatics-technology-ai', 'technology-innovation', ['innovation-product-development', 'quality-safety-governance'], 'other'),
  role('ai-innovator', 'Healthcare AI Innovator / Orchestrator', 'informatics-technology-ai', 'technology-innovation', ['innovation-product-development', 'quality-safety-governance'], 'other'),
  role('health-technology-specialist', 'Health Technology / Informatics Specialist', 'informatics-technology-ai', 'technology-innovation', ['innovation-product-development'], 'other'),
  role('clinical-product-developer', 'Clinical Product / Workflow Developer', 'innovation-product', 'technology-innovation', ['innovation-product-development', 'entrepreneurship-business'], 'other'),
  role('nurse-entrepreneur', 'Nurse Entrepreneur', 'entrepreneurship-business', 'entrepreneurship-business', ['entrepreneurship-business', 'innovation-product-development'], 'other'),
  role('healthcare-business-owner', 'Healthcare / Wellness Business Owner', 'entrepreneurship-business', 'entrepreneurship-business', ['entrepreneurship-business'], 'other'),
  role('community-population-health-professional', 'Community / Population Health Professional', 'community-population-health', 'community-advocacy', ['community-population-health', 'quality-safety-governance'], 'other'),
  role('community-organizer', 'Community Organizer / Program Developer', 'community-population-health', 'community-advocacy', ['community-population-health'], 'other'),
  role('wellness-manager', 'Wellness Manager', 'wellness-sustainability', 'wellness-sustainability', ['wellness-sustainability', 'clinic-management'], 'other'),
  role('wellness-coach-advocate', 'Wellness Coach / Advocate', 'wellness-sustainability', 'wellness-sustainability', ['wellness-sustainability'], 'other'),
  role('professional-advocate-steward', 'Professional Advocate / Steward', 'advocacy-stewardship', 'community-advocacy', ['community-population-health', 'quality-safety-governance'], 'other'),
  role('family-caregiver', 'Family Caregiver', 'wellness-sustainability', 'wellness-sustainability', ['wellness-sustainability', 'work-school-wellness'], 'other')
]);

export const DEVELOPMENTAL_STAGES = Object.freeze([
  { id: 'prelicensure-student', label: 'Prelicensure nursing student' },
  { id: 'nursing-assistant-pct', label: 'Nursing assistant / patient care technician' },
  { id: 'combined-student-assistant', label: 'Combined student and nursing assistant' },
  { id: 'newly-licensed-clinician', label: 'Newly licensed clinician' },
  { id: 'experienced-clinician', label: 'Experienced clinician' },
  { id: 'certification-candidate', label: 'Certification candidate' },
  { id: 'graduate-doctoral-student', label: 'Graduate or doctoral student' },
  { id: 'medical-resident-fellow', label: 'Medical resident or fellow' },
  { id: 'emerging-leader', label: 'Emerging leader' },
  { id: 'entrepreneur-innovator', label: 'Entrepreneur or innovator' },
  { id: 'lifelong-learner', label: 'Lifelong learner' }
]);

export const ADVANCED_STUDY_TYPES = Object.freeze([
  { id: 'specialty-certification', label: 'Specialty certification' },
  { id: 'professional-certification', label: 'Professional certification or recertification' },
  { id: 'continuing-competency', label: 'Continuing competency / renewal' },
  { id: 'advanced-clinical-training', label: 'Advanced clinical training' },
  { id: 'bachelors-degree', label: 'Bachelor’s degree' },
  { id: 'masters-degree', label: 'Master’s degree' },
  { id: 'doctoral-degree', label: 'Doctoral degree' },
  { id: 'postdoctoral-study', label: 'Postdoctoral study' },
  { id: 'residency-fellowship', label: 'Residency or fellowship' },
  { id: 'formal-specialization', label: 'Formal specialization' },
  { id: 'leadership-management-credential', label: 'Leadership or management credential' },
  { id: 'education-research-informatics-credential', label: 'Education, research, informatics, or AI credential' },
  { id: 'business-entrepreneurship-education', label: 'Business or entrepreneurship education' },
  { id: 'continuing-professional-development', label: 'Continuing education / structured professional development' },
  { id: 'career-transition-preparation', label: 'Career-transition preparation' }
]);

function q(id, label, purpose, outputs, type = 'textarea', options = []) {
  return Object.freeze({ id, label, purpose, outputs: Object.freeze(outputs), type, options: Object.freeze(options) });
}

export const CORE_QUESTIONS = Object.freeze([
  q('safetyNoPhi', 'Confirm: no PHI, patient identifiers, protected records, or patient stories will be entered.', 'Establish the no-PHI intake gate.', ['governance', 'ai-behavior'], 'confirm'),
  q('safetyHumanJudgment', 'Confirm: AI does not create clinical, academic, employment, legal, financial, or institutional authority.', 'Preserve accountable human judgment.', ['governance', 'soul-document'], 'confirm'),
  q('safetyAcademicIntegrity', 'Confirm: AI may support learning but may not complete prohibited academic work or fabricate experience.', 'Protect academic integrity.', ['governance', 'advanced-studies'], 'confirm'),
  q('safetyNoCredentialInference', 'Confirm: this quiz does not verify roles, competence, licenses, credentials, assignments, or authority.', 'Prevent authority laundering.', ['governance', 'role-constellation'], 'confirm'),
  q('name', 'What name should Nurse AI OS use?', 'Personalize local outputs without requiring a legal identifier.', ['soul-document'], 'text'),
  q('roleSelection', 'Which roles are part of your current or developing professional life?', 'Discover the complete role constellation.', ['role-constellation', 'conditional-branching', 'dashboards'], 'roles'),
  q('roleStatus', 'For each role, is it primary, supporting, emerging, or contextual?', 'Separate role function without forcing one identity.', ['role-constellation', 'scoring'], 'role-matrix'),
  q('developmentalStage', 'Which learner or developmental stages describe this season?', 'Identify cross-role formation needs.', ['development', 'dashboards', 'agents'], 'checks'),
  q('missionControlSpheres', 'Which Personal, Professional, Community–Entrepreneurial, Side Gig, and Interest environments should share this Core SOUL?', 'Preserve one identity while scoping coordinated Mission Controls.', ['soul-document', 'tier-ceilings', 'dashboards'], 'checks'),
  q('coreValues', 'Which principles remain consistent across your roles?', 'Find stable values across changing responsibilities.', ['soul-document', 'ai-behavior'], 'checks'),
  q('missionPurpose', 'Who, what, or which system do you feel responsible for serving?', 'Define mission and purpose.', ['soul-document', 'dashboards'], 'textarea'),
  q('sharedGoalsCommitments', 'Which near-term goals and scheduling boundaries should every Mission Control respect?', 'Coordinate dashboards without collecting exact private calendar details.', ['soul-document', 'dashboards', 'wellness'], 'textarea'),
  q('motivationsStrengths', 'What motivates you, and what strengths do you rely on?', 'Shape recommendations around intrinsic drivers and assets.', ['soul-document', 'agents'], 'textarea'),
  q('workLearningStyle', 'How do you prefer to work, learn, collaborate, and receive feedback?', 'Configure communication, learning, and collaboration.', ['soul-document', 'agents', 'workflows'], 'checks'),
  q('decisionStyle', 'How do you approach evidence, uncertainty, risk, collaboration, accountability, innovation, conflict, time pressure, ethics, and competing priorities?', 'Configure decision support without replacing judgment.', ['decision-profile', 'ai-behavior'], 'likert-matrix'),
  q('pressuresWellness', 'Which responsibilities and pressures are most active, and what limit should the system protect?', 'Identify overload risk and sustainability needs.', ['tensions', 'wellness-dashboard', 'ai-behavior'], 'mixed'),
  q('aiRelationship', 'Which AI relationships are useful in this season?', 'Select preferred AI operating modes.', ['agents', 'workflows'], 'checks'),
  q('aiDelegation', 'What may AI do privately, prepare, or only support behind a human gate?', 'Create a governed delegation matrix.', ['governance', 'ai-behavior'], 'delegation-matrix'),
  q('memoryBoundaries', 'What may the system remember, and what must it never retain?', 'Minimize retained information and protect boundaries.', ['governance', 'memory-policy'], 'mixed'),
  q('escalation', 'When must the system stop and escalate to a human authority?', 'Define fail-closed escalation triggers.', ['governance', 'ai-behavior'], 'checks')
]);

const STUDENT_SAFEGUARDS = Object.freeze([
  'AI must not encourage work beyond the person’s authorized scope or delegated duties.',
  'Required faculty, preceptor, nurse, supervisor, and chain-of-command oversight remain mandatory.',
  'AI must not facilitate academic dishonesty or complete prohibited academic work.',
  'Developing knowledge, confidence, simulation, or practice must never be represented as verified competence.',
  'Students and nursing assistants receive no unsupervised clinical authority from AI.'
]);

export const CONDITIONAL_MODULES = Object.freeze({
  'student-assistant': Object.freeze({
    id: 'student-assistant', name: 'Prelicensure Student and Nursing Assistant', requiredWhenSelected: true, safeguards: STUDENT_SAFEGUARDS,
    questions: Object.freeze([
      q('studentAssistantCombination', 'Which applies: student, nursing assistant/PCT, or both?', 'Differentiate overlapping but non-interchangeable roles.', ['role-constellation', 'authority']),
      q('programAndStage', 'If studying, what program type and stage are you in?', 'Locate educational progression without inferring standing.', ['development', 'learning-pathway']),
      q('trainingEmploymentStatus', 'What training, certification, employment, and clinical-placement statuses apply?', 'Separate education, employment, and certification contexts.', ['authority', 'dashboard-context']),
      q('careEnvironmentResponsibilities', 'Which care environments and assigned responsibilities are current?', 'Map frontline context without patient data.', ['dashboard-context', 'workflows']),
      q('authorizedScope', 'How is your authorized scope defined in each current setting?', 'Prevent scope expansion.', ['governance', 'authority']),
      q('delegatedDuties', 'Which duties are delegated to you, and by whom?', 'Identify bounded delegated work.', ['governance', 'authority']),
      q('supervision', 'What supervision, escalation, and chain-of-command rules apply?', 'Preserve required human oversight.', ['governance', 'agents']),
      q('clinicalSimulationExperience', 'Summarize clinical placements, simulation, and frontline-care experience without identifiable details.', 'Distinguish exposure, simulation, and employment experience.', ['development', 'learning-pathway']),
      q('foundationalSkillsSafety', 'Which foundational caregiving, communication, teamwork, infection-prevention, safety, handoff, and documentation skills are developing?', 'Target safe foundational learning.', ['learning-pathway', 'agents']),
      q('confidenceVsCompetence', 'Where is confidence high or low, and what evidence of supervised competence exists?', 'Keep confidence separate from demonstrated competence.', ['scoring', 'authority']),
      q('entranceProgressionNclex', 'What entrance, progression, skills, simulation, graduation, or NCLEX needs are active?', 'Route learning support to the current milestone.', ['advanced-studies', 'dashboards']),
      q('studentAssistantPressuresSupport', 'What work, school, family, scheduling, stress, wellness, faculty, preceptor, supervisor, or mentorship pressures shape this season?', 'Identify sustainability and support needs.', ['tensions', 'wellness-dashboard']),
      q('careerSpecialtyInterests', 'Which specialty interests and longer-term pathways are emerging?', 'Capture aspirations without granting future authority.', ['emerging-roles', 'learning-pathway']),
      q('transitionGoals', 'Which transition goals matter next?', 'Define milestones from admission through licensure and future development.', ['milestones', 'dashboards']),
      q('studentAssistantAiBoundary', 'How may AI support study, simulation, work preparation, and reflection—and what is prohibited?', 'Configure lane-specific AI boundaries.', ['governance', 'agents'])
    ])
  }),
  'clinical-care': Object.freeze({
    id: 'clinical-care', name: 'Direct Clinical Care', safeguards: Object.freeze(['No PHI or patient-specific content.', 'AI may support preparation and learning; licensed humans retain clinical judgment.']),
    questions: Object.freeze([
      q('clinicalEnvironmentResponsibilities', 'What environments, responsibilities, and shift patterns shape your role?', 'Configure a bounded clinical-preparation context.', ['dashboard-context', 'wellness']),
      q('clinicalAuthorizationSupervision', 'What license, assignment, delegation, supervision, and institutional boundaries apply?', 'Record self-reported authority boundaries without verification.', ['authority', 'governance']),
      q('clinicalStrengthsGaps', 'Which strengths, knowledge gaps, and professional-development priorities are active?', 'Route learning support.', ['learning-pathway', 'agents']),
      q('clinicalPressures', 'Which workload, communication, moral-distress, scheduling, or transition pressures are active?', 'Identify risk and sustainability needs.', ['tensions', 'wellness-dashboard']),
      q('clinicalAiSupport', 'Which no-PHI planning, learning, communication-practice, and reflection workflows would help?', 'Recommend safe workflows.', ['agents', 'workflows'])
    ])
  }),
  'advanced-practice': Object.freeze({
    id: 'advanced-practice', name: 'Advanced Clinical Practice / Medical Training', safeguards: Object.freeze(['No patient-specific diagnosis, treatment, prescribing, orders, or clinical documentation.', 'Privileges, supervision, law, policy, and licensed judgment remain controlling.']),
    questions: Object.freeze([
      q('advancedPracticeContext', 'What training, population, specialty, or practice context applies?', 'Route non-clinical professional development.', ['dashboard-context']),
      q('advancedPracticeAuthority', 'What supervision, privileges, credentialing, policy, and legal boundaries apply?', 'Prevent clinical authority inference.', ['authority', 'governance']),
      q('advancedPracticeLearning', 'Which competencies, boards, milestones, or continuing-development needs are active?', 'Recommend learning support.', ['advanced-studies', 'agents']),
      q('advancedPracticePressures', 'Which workload, call, training, leadership, or wellness pressures are active?', 'Identify overload and sustainability risk.', ['tensions', 'wellness-dashboard']),
      q('advancedPracticeAiBoundary', 'Which public-source, synthetic, reflective, or administrative tasks may AI support?', 'Keep support non-clinical and governed.', ['governance', 'workflows'])
    ])
  }),
  'education-mentorship': Object.freeze({
    id: 'education-mentorship', name: 'Education and Mentorship', safeguards: Object.freeze(['No student records or identifiable learner data.', 'Human faculty retain grading, accommodation, progression, curriculum, and release authority.']),
    questions: Object.freeze([
      q('educationLearnersSetting', 'Who do you teach, precept, mentor, or facilitate, and in what setting?', 'Configure the educational context.', ['dashboard-context']),
      q('educationResponsibilities', 'Which teaching, precepting, assessment, feedback, curriculum, or faculty responsibilities are current?', 'Map role responsibilities.', ['workflows']),
      q('educationAuthority', 'What grading, progression, accommodation, curriculum, and supervision authority is formally assigned?', 'Prevent academic authority inference.', ['authority', 'governance']),
      q('educationGoalsGaps', 'Which learner outcomes, teaching strengths, and development gaps matter now?', 'Recommend educational support.', ['learning-pathway', 'agents']),
      q('educationAiBoundary', 'Where may AI draft synthetic learning material, and where is human review mandatory?', 'Protect learner-impact decisions.', ['governance', 'workflows'])
    ])
  }),
  'leadership-management': Object.freeze({
    id: 'leadership-management', name: 'Leadership and Management', safeguards: Object.freeze(['No personnel files, surveillance, or autonomous workforce decisions.', 'Authorized leaders retain staffing, performance, discipline, budget, and release authority.']),
    questions: Object.freeze([
      q('leadershipScope', 'What team, service, committee, or program responsibilities are current?', 'Configure leadership context.', ['dashboard-context']),
      q('leadershipAuthority', 'Which staffing, personnel, budget, policy, and decision rights are formally assigned?', 'Prevent management authority inference.', ['authority', 'governance']),
      q('leadershipPriorities', 'What outcomes, relationships, and operational priorities matter most?', 'Shape leadership dashboards.', ['dashboards', 'workflows']),
      q('leadershipPressures', 'Which conflict, workload, accountability, change, or political pressures are active?', 'Identify tensions and support needs.', ['tensions', 'agents']),
      q('leadershipAiBoundary', 'Which briefs, agendas, plans, and analyses may AI prepare for human review?', 'Recommend governed leadership support.', ['governance', 'workflows'])
    ])
  }),
  'administration-operations': Object.freeze({
    id: 'administration-operations', name: 'Administration and Operations', safeguards: Object.freeze(['No autonomous staffing, procurement, financial, compliance, or institutional decisions.', 'Organization-approved systems and accountable owners remain controlling.']),
    questions: Object.freeze([
      q('operationsEnvironment', 'Which hospital, clinic, service, or operational environment is relevant?', 'Select the appropriate operations dashboard.', ['dashboard-context']),
      q('operationsResponsibilities', 'Which workforce, finance, access, capacity, service, procurement, or compliance responsibilities are current?', 'Map operational scope.', ['dashboards']),
      q('operationsAuthority', 'Which decisions and data are formally authorized, restricted, or outside scope?', 'Prevent institutional authority laundering.', ['authority', 'governance']),
      q('operationsPrioritiesIndicators', 'Which priorities and indicators require human-reviewed monitoring?', 'Recommend metrics without activating surveillance.', ['performance-indicators', 'dashboards']),
      q('operationsAiBoundary', 'Which planning, public-source, synthetic, and drafting tasks may AI support?', 'Configure bounded administrative support.', ['governance', 'workflows'])
    ])
  }),
  'quality-research': Object.freeze({
    id: 'quality-research', name: 'Quality, Safety, Research, and Evidence', safeguards: Object.freeze(['The quiz makes no research-versus-QI determination.', 'No participant, patient, peer-review, incident, person-level, or protected data.', 'Authorized IRB, privacy, quality, data, and institutional bodies retain authority.']),
    questions: Object.freeze([
      q('qualityResearchFunction', 'Is the current work research, evidence review, quality improvement, safety, governance, or still undetermined?', 'Prevent unsupported research/QI classification.', ['governance', 'dashboard-context']),
      q('qualityResearchAuthority', 'What charter, sponsor, PI, committee, data, privacy, or review authority is formally present?', 'Map accountable authority.', ['authority', 'governance']),
      q('qualityResearchQuestion', 'What question, problem, aim, or evidence need is being explored using non-sensitive language?', 'Configure inquiry support.', ['agents', 'workflows']),
      q('qualityResearchMethodsGaps', 'Which methods, evidence, measurement, or dissemination capabilities are developing?', 'Recommend learning support.', ['learning-pathway', 'agents']),
      q('qualityResearchAiBoundary', 'Which public-source, synthetic, aggregate, or separately authorized tasks may AI prepare?', 'Protect data and determination boundaries.', ['governance', 'workflows'])
    ])
  }),
  'technology-innovation': Object.freeze({
    id: 'technology-innovation', name: 'Informatics, Technology, AI, and Innovation', safeguards: Object.freeze(['No production access, connector activation, secret handling, clinical integration, procurement, or deployment authority.', 'Prototypes remain local, synthetic, reversible, and human-reviewed.']),
    questions: Object.freeze([
      q('technologyInnovationFocus', 'Which workflow, informatics, AI, product, or innovation problems matter?', 'Configure innovation support.', ['dashboards', 'agents']),
      q('technologyAuthority', 'What system access, technical ownership, governance, procurement, or deployment authority is formally assigned?', 'Prevent technical authority inference.', ['authority', 'governance']),
      q('technologyUsersImpact', 'Who may be affected, and what dignity, equity, environmental, nursing, or agency concerns apply?', 'Apply the EDENA stewardship lens.', ['governance', 'soul-document']),
      q('technologyStageEvidence', 'What stage, evidence, tests, assumptions, and failure criteria exist?', 'Distinguish idea, prototype, validation, and deployment.', ['workflows', 'performance-indicators']),
      q('technologyAiBoundary', 'Which synthetic requirements, prototypes, test plans, and reviews may AI support?', 'Keep building bounded and reversible.', ['governance', 'workflows'])
    ])
  }),
  'entrepreneurship-business': Object.freeze({
    id: 'entrepreneurship-business', name: 'Entrepreneurship and Business', safeguards: Object.freeze(['No fabricated validation, customers, revenue, legal status, clinical readiness, or authority.', 'Human review is required before publication, commitments, transactions, or outreach.']),
    questions: Object.freeze([
      q('businessFocusAudience', 'What is the venture, offer, audience, or problem being explored?', 'Configure entrepreneurship support.', ['dashboards', 'agents']),
      q('businessStageEvidence', 'What stage and real evidence exist today?', 'Separate aspiration from proof.', ['scoring', 'performance-indicators']),
      q('businessResponsibilities', 'Which product, content, finance, operations, sales, or partnership responsibilities are current?', 'Map entrepreneurial workload.', ['workflows', 'tensions']),
      q('businessBoundaries', 'Which clinical claims, employer conflicts, customer data, legal, financial, or ethical boundaries apply?', 'Protect professional and commercial integrity.', ['governance']),
      q('businessAiSupport', 'Which research, planning, drafting, prototyping, and project-management tasks may AI support?', 'Recommend governed business workflows.', ['agents', 'workflows'])
    ])
  }),
  'community-advocacy': Object.freeze({
    id: 'community-advocacy', name: 'Community, Population Health, Advocacy, and Stewardship', safeguards: Object.freeze(['No claimed community mandate, participant consent, spokesperson status, fundraising, or political authority.', 'No sensitive participant information or automatic outreach.']),
    questions: Object.freeze([
      q('communityMissionPopulation', 'Which community, population, profession, or stewardship mission matters?', 'Configure mission-aligned support.', ['soul-document', 'dashboards']),
      q('communityRoleAuthority', 'What assignment, mandate, consent, representation, or organizational authority is actually present?', 'Prevent representation laundering.', ['authority', 'governance']),
      q('communityResponsibilities', 'Which listening, education, organizing, advocacy, navigation, or program responsibilities are current?', 'Map community workflows.', ['workflows']),
      q('communityRisksBoundaries', 'Which equity, privacy, safety, cultural, political, or conflict risks require human stewardship?', 'Configure safeguards.', ['governance']),
      q('communityAiSupport', 'Which public education, stakeholder mapping, agenda, and resource-navigation drafts may AI support?', 'Recommend governed community support.', ['agents', 'workflows'])
    ])
  }),
  'wellness-sustainability': Object.freeze({
    id: 'wellness-sustainability', name: 'Wellness and Personal Sustainability', safeguards: Object.freeze(['This is planning and reflection support—not diagnosis, treatment, fitness-for-duty, crisis assessment, or medical or mental-health care.', 'No sensitive health details, hidden health inference, surveillance, or performance scoring.', 'Emergencies and immediate safety concerns leave the AI workflow for official local emergency routes and appropriate human support.']),
    questions: Object.freeze([
      q('wellnessResponsibilities', 'Which caregiving, work, study, recovery, household, or wellness responsibilities matter?', 'Map sustainability demands.', ['tensions', 'wellness-dashboard']),
      q('wellnessPatternsLimits', 'Which non-sensitive patterns, limits, and recovery practices should the system protect?', 'Configure humane workload boundaries.', ['soul-document', 'ai-behavior']),
      q('wellnessOverloadSignals', 'What early overload signals should prompt slowing down or human support?', 'Create escalation cues.', ['governance', 'ai-behavior']),
      q('wellnessSupportNetwork', 'Which human supports, mentors, peers, or resources may be appropriate?', 'Preserve human connection.', ['agents', 'escalation']),
      q('wellnessAiBoundary', 'Which scheduling, reflection, habit, and recovery-planning tasks may AI support?', 'Recommend non-clinical wellness workflows.', ['workflows', 'governance'])
    ])
  }),
  'advanced-studies': Object.freeze({
    id: 'advanced-studies', name: 'Advanced Studies', crossRoleOverlay: true, safeguards: Object.freeze(['Advanced Studies never creates or replaces a professional identity.', 'AI may tutor, coach, plan, and rehearse; it may not impersonate, fabricate, grade, certify, or complete prohibited work.']),
    questions: Object.freeze([
      q('pathwayTarget', 'What certification, credential, degree, specialization, renewal, or transition is active?', 'Identify the growth pathway.', ['advanced-studies', 'dashboards']),
      q('motivationOutcome', 'Why are you pursuing it, and what professional outcome do you intend?', 'Connect study to mission and roles.', ['soul-document', 'advanced-studies']),
      q('preparationStage', 'What stage of preparation are you in?', 'Locate the current developmental milestone.', ['scoring', 'milestones']),
      q('competenciesMilestones', 'Which competencies, examinations, graduation, renewal, or milestone dates apply?', 'Create a milestone map.', ['learning-pathway', 'dashboards']),
      q('progressEvidenceGaps', 'What evidence of progress, knowledge gaps, and competency gaps exist?', 'Separate proof, confidence, and developing capability.', ['scoring', 'learning-pathway']),
      q('learningTimeSupport', 'Which formats, study time, schedule, accountability, coaching, and mentorship supports work?', 'Configure the learning system.', ['agents', 'workflows']),
      q('roleRelationship', 'How does this pathway support or compete with your other roles?', 'Identify role synergy and tension.', ['synergies', 'tensions']),
      q('barriersWellness', 'Which financial, workload, family, institutional, and wellness barriers matter?', 'Protect sustainability and access.', ['tensions', 'wellness-dashboard']),
      q('applicationRenewal', 'Where can learning be applied safely, and what continuing-education or renewal requirements apply?', 'Connect learning to governed practice.', ['workflows', 'milestones']),
      q('academicIntegrityBoundary', 'What academic-integrity and responsible-AI boundaries apply?', 'Protect honest learning and assessment.', ['governance', 'ai-behavior'])
    ])
  })
});

function dashboard(id, name, purpose, specifics = {}) {
  return Object.freeze({
    id, name, purpose,
    rolesSupported: Object.freeze(specifics.rolesSupported || []),
    primaryObjectives: Object.freeze(specifics.primaryObjectives || ['Keep role-specific priorities visible', 'Prepare bounded work for human judgment']),
    currentPriorities: Object.freeze(specifics.currentPriorities || ['Confirm current context and authority', 'Choose one safe first workflow']),
    informationRequirements: Object.freeze(specifics.informationRequirements || ['Public, synthetic, personal no-PHI, or separately authorized information only']),
    recommendedAgents: Object.freeze(specifics.recommendedAgents || ['project-manager', 'governance-monitor']),
    coreWorkflows: Object.freeze(specifics.coreWorkflows || ['Weekly huddle', 'Priority review', 'Human-gated draft queue']),
    learningGoals: Object.freeze(specifics.learningGoals || ['Build role-relevant capability without overstating competence']),
    milestones: Object.freeze(specifics.milestones || ['First safe workflow reviewed', 'Monthly role and boundary review']),
    performanceIndicators: Object.freeze(specifics.performanceIndicators || ['Milestones reviewed', 'Human gates completed', 'Wellness limits respected']),
    permissions: Object.freeze(specifics.permissions || ['A0 recommendation only', 'No connectors or external actions']),
    dataBoundaries: Object.freeze(specifics.dataBoundaries || ['No PHI', 'No protected academic, employee, participant, or institutional records']),
    humanReview: Object.freeze(specifics.humanReview || ['Human review before consequential, external, evaluative, or institutional use']),
    safeguards: Object.freeze(specifics.safeguards || ['Role selection grants no authority', 'Escalate uncertainty or conflicting information']),
    relationships: Object.freeze(specifics.relationships || ['Shares Core SOUL, approved memory, goals, calendar, and wellness limits with other dashboards'])
  });
}

export const DASHBOARD_CATALOG = Object.freeze(Object.fromEntries([
  dashboard('prelicensure-student', 'Prelicensure Student Mission Control', 'Coordinate academic learning, clinical placement, simulation, progression, and integrity boundaries without implying employment scope.', { rolesSupported: ['Prelicensure Nursing Student'], recommendedAgents: ['tutor', 'coach', 'simulation-facilitator', 'governance-monitor'] }),
  dashboard('nursing-assistant-workforce', 'Nursing Assistant / Healthcare Assistant Mission Control', 'Coordinate assigned frontline-support work, delegated duties, supervision, and professional growth without importing student-nurse authority.', { rolesSupported: ['Nursing Assistant / CNA / PCT / Healthcare Assistant'], recommendedAgents: ['coach', 'tutor', 'simulation-facilitator', 'governance-monitor'] }),
  dashboard('student-assistant-bridge', 'Student and Nursing Assistant Bridge Mission Control', 'Coordinate distinct school and employment contexts only when both roles are selected; no automatic transfer of scope, records, or authority.', { rolesSupported: ['Prelicensure Nursing Student', 'Nursing Assistant / CNA / PCT / Healthcare Assistant'], recommendedAgents: ['tutor', 'coach', 'simulation-facilitator', 'governance-monitor'] }),
  dashboard('clinical-learning-simulation', 'Clinical Learning, Skills, and Simulation', 'Support synthetic preparation, supervised skills development, communication practice, and reflective debriefing.', { recommendedAgents: ['tutor', 'simulation-facilitator', 'mentor'] }),
  dashboard('education-certification-nclex', 'Education, Certification, and NCLEX Preparation', 'Coordinate entrance, progression, exam, certification, and continuing-development milestones.', { recommendedAgents: ['tutor', 'coach', 'project-manager'] }),
  dashboard('work-school-wellness', 'Work-School-Wellness Coordination', 'Protect capacity across work, study, family, caregiving, and recovery.', { recommendedAgents: ['coach', 'project-manager'] }),
  dashboard('bedside-clinical-command', 'Bedside Clinical Command', 'Prepare private no-PHI learning, communication, shift-organization, and professional-development work; never function as a clinical system.', { recommendedAgents: ['coach', 'tutor', 'governance-monitor'] }),
  dashboard('advanced-practice', 'Advanced Practice', 'Coordinate non-clinical professional development while licensed humans retain all patient-specific judgment.', { recommendedAgents: ['research-assistant', 'tutor', 'governance-monitor'] }),
  dashboard('advanced-studies-certification', 'Advanced Studies and Certification', 'Operate as a cross-role learning overlay for credentials, degrees, specialization, renewal, and transition.', { recommendedAgents: ['tutor', 'coach', 'mentor', 'project-manager'] }),
  dashboard('graduate-degree-research', 'Graduate Degree and Research', 'Coordinate degree milestones, public evidence, methods learning, writing support, and academic-integrity gates.', { recommendedAgents: ['research-assistant', 'tutor', 'project-manager', 'governance-monitor'] }),
  dashboard('education-mentorship', 'Education and Mentorship', 'Support teaching, precepting, mentoring, and learning-design preparation with human academic authority preserved.', { recommendedAgents: ['teacher', 'mentor', 'simulation-facilitator', 'governance-monitor'] }),
  dashboard('unit-leadership-operations', 'Unit Leadership and Operations', 'Prepare briefs, huddles, plans, governance work, and follow-through without becoming an HR or staffing decision system.', { recommendedAgents: ['strategic-advisor', 'project-manager', 'analyst', 'governance-monitor'] }),
  dashboard('hospital-administration', 'Hospital Administration', 'Coordinate bounded strategy, operations, governance, workforce, finance, and service planning with institutional human authority preserved.', { recommendedAgents: ['strategic-advisor', 'analyst', 'project-manager', 'governance-monitor'] }),
  dashboard('clinic-management', 'Clinic Management', 'Coordinate clinic access, operations, team, service, and improvement preparation without live operational authority.', { recommendedAgents: ['project-manager', 'analyst', 'governance-monitor'] }),
  dashboard('quality-safety-governance', 'Quality, Safety, and Governance', 'Prepare quality, safety, evidence, and governance work without making research/QI, compliance, or institutional determinations.', { recommendedAgents: ['analyst', 'research-assistant', 'governance-monitor'] }),
  dashboard('research-evidence', 'Research and Evidence', 'Frame questions, synthesize public evidence, learn methods, and prepare human-reviewed research or evidence work.', { recommendedAgents: ['research-assistant', 'analyst', 'governance-monitor'] }),
  dashboard('innovation-product-development', 'Innovation and Product Development', 'Coordinate local synthetic prototypes, requirements, tests, and human-gated product decisions.', { recommendedAgents: ['creative-collaborator', 'project-manager', 'analyst', 'governance-monitor'] }),
  dashboard('entrepreneurship-business', 'Entrepreneurship and Business', 'Coordinate evidence, offers, products, operations, and communications without fabricating validation or authority.', { recommendedAgents: ['creative-collaborator', 'strategic-advisor', 'project-manager', 'governance-monitor'] }),
  dashboard('community-population-health', 'Community and Population Health', 'Support listening, education, resource navigation, advocacy, and participatory planning without claiming a mandate.', { recommendedAgents: ['thought-partner', 'research-assistant', 'project-manager', 'governance-monitor'] }),
  dashboard('wellness-sustainability', 'Wellness and Personal Sustainability', 'Protect recovery, capacity, caregiving, humane scheduling, and escalation to human support.', { recommendedAgents: ['coach', 'project-manager'] })
].map((item) => [item.id, item])));

export const AI_RELATIONSHIP_MODES = Object.freeze([
  'teacher', 'tutor', 'coach', 'mentor', 'research-assistant', 'thought-partner',
  'creative-collaborator', 'administrative-assistant', 'project-manager',
  'workflow-coordinator', 'analyst', 'simulation-facilitator', 'strategic-advisor',
  'governance-monitor', 'automation-agent'
]);

const AGENT_CATALOG = Object.freeze(Object.fromEntries(AI_RELATIONSHIP_MODES.map((id) => [id, Object.freeze({
  id,
  name: id.split('-').map((word) => word[0].toUpperCase() + word.slice(1)).join(' '),
  activation: 'not-authorized',
  humanGate: id === 'automation-agent' ? 'Automation remains off until a separate task-level governance review and explicit activation.' : 'Human review remains required before consequential or external use.',
  workflows: Object.freeze(id === 'tutor' ? ['Concept review', 'Practice questions', 'Teach-back'] : id === 'governance-monitor' ? ['Boundary check', 'Claim-vs-proof review', 'Escalation queue'] : id === 'project-manager' ? ['Milestone map', 'Weekly review', 'Dependency check'] : ['Private no-PHI preparation', 'Human-reviewed draft'])
})])));

export const DELEGATION_ACTIVITIES = Object.freeze([
  { id: 'public-source-summary', label: 'Summarize public, non-sensitive sources', defaultLevel: 'independent-private', floor: 'independent-private' },
  { id: 'private-plan-draft', label: 'Draft a private, reversible plan', defaultLevel: 'independent-private', floor: 'independent-private' },
  { id: 'external-send', label: 'Send, publish, submit, schedule, purchase, or contact someone', defaultLevel: 'explicit-confirmation', floor: 'explicit-confirmation' },
  { id: 'patient-specific-clinical-decision', label: 'Process patient-specific content or make a clinical decision', defaultLevel: 'never-delegate', floor: 'never-delegate' },
  { id: 'graded-or-evaluative-work', label: 'Grade, evaluate, rank, discipline, admit, hire, promote, or credential a person', defaultLevel: 'professional-supervision', floor: 'professional-supervision' },
  { id: 'institutional-change', label: 'Change an institutional system, policy, workflow, staffing, budget, or configuration', defaultLevel: 'accountable-human-judgment', floor: 'accountable-human-judgment' },
  { id: 'academic-learning-support', label: 'Tutor, quiz, explain, or help plan legitimate learning', defaultLevel: 'prepare-only', floor: 'prepare-only' },
  { id: 'credential-or-competence-claim', label: 'Claim a credential, competence, completed experience, or professional authority', defaultLevel: 'never-delegate', floor: 'never-delegate' }
]);

const LEVEL_RANK = Object.freeze(Object.fromEntries(GOVERNANCE_LEVELS.map((level, index) => [level, index])));

export function applyGovernanceFloor(activityId, requestedLevel) {
  const activity = DELEGATION_ACTIVITIES.find((item) => item.id === activityId);
  if (!activity) return 'never-delegate';
  const requested = LEVEL_RANK[requestedLevel] === undefined ? activity.defaultLevel : requestedLevel;
  return LEVEL_RANK[requested] < LEVEL_RANK[activity.floor] ? activity.floor : requested;
}

export function roleById(id) {
  return ROLE_TAXONOMY.find((item) => item.id === id) || null;
}

function defaultDelegation() {
  return Object.fromEntries(DELEGATION_ACTIVITIES.map((item) => [item.id, item.defaultLevel]));
}

export function createInitialState(now = null) {
  const timestamp = now ? new Date(now).toISOString() : new Date().toISOString();
  return {
    schemaVersion: SCHEMA_VERSION,
    name: '',
    selectedRoleIds: [],
    roleSelections: [],
    customRoles: [],
    spheres: ['professional'],
    developmentalStages: [],
    advancedStudies: { active: false, pathways: [] },
    core: {
      values: [], customValues: '', mission: '', populations: '', sharedGoals: '', commitmentBoundaries: '', motivations: [], strengths: '',
      workStyles: [], learningStyles: [],
      voice: { length: 'Bulleted & structured', formality: 'Professional', pushback: 'Push back when stakes are high', avoid: '' },
      alwaysRemember: ''
    },
    pressures: { selected: [], load: 3, wellnessLimit: '' },
    decisionStyle: { evidence: 3, uncertainty: 3, risk: 3, collaboration: 3, accountability: 3, innovation: 3, conflict: 3, timePressure: 3, ethicalConcerns: 3, competingPriorities: 3 },
    ai: {
      relationshipModes: [], primaryMode: '', delegation: defaultDelegation(),
      memoryAllowed: ['communication preferences', 'stable values', 'approved long-term goals'],
      memoryForbidden: ['PHI', 'patient identifiers', 'passwords, credentials, or secrets', 'protected student or employee records'],
      escalationTriggers: ['patient-specific or clinical content', 'uncertain authority or scope', 'academic integrity concern', 'high-stakes or irreversible action']
    },
    safety: { noPhi: false, noClinicalAuthority: false, noAcademicDishonesty: false, noCredentialInference: false },
    moduleAnswers: {},
    updatedAt: timestamp
  };
}

const TITLE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9 &/()'’\-]{1,59}$/;
const PROHIBITED_TITLE_PATTERN = /\b(?:patient|mrn|medical record|record number|patient id|patient identifier|dob|date of birth|ssn|social security|employee id|student id|case number)\b/i;

export function validateCustomRoleTitle(title) {
  const normalized = String(title || '').trim().replace(/\s+/g, ' ');
  return TITLE_PATTERN.test(normalized) && !PROHIBITED_TITLE_PATTERN.test(normalized) ? normalized : null;
}

export function addCustomRole(state, title, domainId, status = 'contextual') {
  const clean = validateCustomRoleTitle(title);
  if (!clean) throw new Error('Use a generic role title only—no names, organizations, record identifiers, or narratives.');
  if (!ROLE_DOMAINS.some((item) => item.id === domainId)) throw new Error('Choose a valid role domain.');
  if (!ROLE_STATUSES.includes(status)) throw new Error('Choose a valid role status.');
  const idBase = clean.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48);
  const id = `local-role-${idBase}`;
  if (ROLE_TAXONOMY.some((item) => item.id === id) || state.customRoles.some((item) => item.id === id)) throw new Error('That custom role already exists.');
  const domainModule = {
    'learning-formation': 'advanced-studies', 'direct-clinical-care': 'clinical-care', 'advanced-clinical-practice': 'advanced-practice',
    'education-mentorship': 'education-mentorship', 'leadership-management': 'leadership-management', 'administration-operations': 'administration-operations',
    'quality-safety-governance': 'quality-research', 'research-evidence': 'quality-research', 'informatics-technology-ai': 'technology-innovation',
    'innovation-product': 'technology-innovation', 'entrepreneurship-business': 'entrepreneurship-business', 'community-population-health': 'community-advocacy',
    'wellness-sustainability': 'wellness-sustainability', 'advocacy-stewardship': 'community-advocacy'
  };
  const domainDashboard = {
    'learning-formation': 'advanced-studies-certification', 'direct-clinical-care': 'bedside-clinical-command', 'advanced-clinical-practice': 'advanced-practice',
    'education-mentorship': 'education-mentorship', 'leadership-management': 'unit-leadership-operations', 'administration-operations': 'hospital-administration',
    'quality-safety-governance': 'quality-safety-governance', 'research-evidence': 'research-evidence', 'informatics-technology-ai': 'innovation-product-development',
    'innovation-product': 'innovation-product-development', 'entrepreneurship-business': 'entrepreneurship-business', 'community-population-health': 'community-population-health',
    'wellness-sustainability': 'wellness-sustainability', 'advocacy-stewardship': 'community-population-health'
  };
  state.customRoles.push({ id, label: clean, domainId, moduleId: domainModule[domainId], dashboardIds: [domainDashboard[domainId]], authorityDisclaimer: AUTHORITY_DISCLAIMER, status: 'local-draft-not-reviewed' });
  state.roleSelections.push({ roleId: id, status, attention: 1, responsibility: 1, identity: 1, confidence: 1, authorization: 'self-declared', competenceEvidence: 'not-assessed', credentialStatus: 'not-claimed' });
  return state;
}

export function removeCustomRole(state, roleId) {
  if (!String(roleId || '').startsWith('local-role-')) throw new Error('Only local draft roles may be removed here.');
  if (!state.customRoles.some((item) => item.id === roleId)) throw new Error('That local draft role no longer exists.');
  const removedSelection = state.roleSelections.find((item) => item.roleId === roleId);
  state.customRoles = state.customRoles.filter((item) => item.id !== roleId);
  state.roleSelections = state.roleSelections.filter((item) => item.roleId !== roleId);
  if (removedSelection?.status === 'primary' && state.roleSelections.length && !state.roleSelections.some((item) => item.status === 'primary')) {
    state.roleSelections[0].status = 'primary';
  }
  return state;
}

function lookupRole(state, roleId) {
  return roleById(roleId) || state.customRoles?.find((item) => item.id === roleId) || null;
}

function boundedRating(value, fallback = 1) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 1 && n <= 5 ? n : fallback;
}

export function scoreRoleConstellation(state) {
  const buckets = { primary: [], supporting: [], emerging: [], contextual: [] };
  const bases = { primary: 100, supporting: 70, emerging: 50, contextual: 35 };
  for (const selection of state.roleSelections || []) {
    const roleItem = lookupRole(state, selection.roleId);
    if (!roleItem || !ROLE_STATUSES.includes(selection.status)) continue;
    const attention = boundedRating(selection.attention);
    const responsibility = boundedRating(selection.responsibility);
    const identity = boundedRating(selection.identity);
    const confidence = boundedRating(selection.confidence);
    buckets[selection.status].push({
      roleId: roleItem.id,
      label: roleItem.label,
      domainId: roleItem.domainId,
      status: selection.status,
      intensity: bases[selection.status] + attention * 4 + responsibility * 5 + identity * 3,
      attention, responsibility, identity, confidence,
      authorization: AUTHORIZATION_VALUES.includes(selection.authorization) ? selection.authorization : 'self-declared',
      competenceEvidence: COMPETENCE_EVIDENCE_VALUES.includes(selection.competenceEvidence) ? selection.competenceEvidence : 'not-assessed',
      credentialStatus: CREDENTIAL_STATUS_VALUES.includes(selection.credentialStatus) ? selection.credentialStatus : 'not-claimed',
      verification: 'self-reported-not-verified',
      authorityGranted: false
    });
  }
  for (const key of ROLE_STATUSES) buckets[key].sort((a, b) => b.intensity - a.intensity || (a.roleId < b.roleId ? -1 : a.roleId > b.roleId ? 1 : 0));
  const domains = new Set(Object.values(buckets).flat().map((item) => item.domainId));
  const synergies = [];
  if (domains.has('direct-clinical-care') && domains.has('education-mentorship')) synergies.push('Role synergies: current clinical experience can strengthen teaching and precepting while learners sharpen reflective practice.');
  if (domains.has('direct-clinical-care') && domains.has('quality-safety-governance')) synergies.push('Role synergies: frontline pattern recognition can inform bounded quality and safety preparation.');
  if (domains.has('leadership-management') && domains.has('research-evidence')) synergies.push('Role synergies: evidence skills can strengthen human-led leadership decisions.');
  if ((domains.has('informatics-technology-ai') || domains.has('innovation-product')) && domains.has('entrepreneurship-business')) synergies.push('Role synergies: technical building and entrepreneurship can share evidence, product, and governance workflows.');
  if (!synergies.length && Object.values(buckets).flat().length > 1) synergies.push('Role synergies: complementary roles can share values, goals, learning, and reusable no-PHI workflows through one Core SOUL.');
  const tensions = [];
  const count = Object.values(buckets).flat().length;
  if (count >= 4) tensions.push('Four or more active or developing roles create a realistic overload risk; protect capacity and choose a lead dashboard for each week.');
  if (state.advancedStudies?.active && (state.pressures?.load >= 3 || state.pressures?.selected?.length)) tensions.push('Advanced Studies competes with work, family, and recovery time; milestones need explicit capacity limits.');
  if ((domains.has('direct-clinical-care') || domains.has('advanced-clinical-practice')) && domains.has('entrepreneurship-business')) tensions.push('Clinical and entrepreneurial roles require strict separation of patient, employer, claim, conflict-of-interest, and commercial boundaries.');
  const ids = new Set(Object.values(buckets).flat().map((item) => item.roleId));
  if (ids.has('prelicensure-nursing-student') && ids.has('nursing-assistant-pct')) tensions.push('Student and nursing-assistant responsibilities may coexist but retain different scope, delegation, supervision, academic, and employment boundaries.');
  return { ...buckets, synergies, tensions };
}

export function recommendedModuleIds(state) {
  const modules = new Set();
  for (const selection of state.roleSelections || []) {
    const roleItem = lookupRole(state, selection.roleId);
    if (roleItem?.moduleId) modules.add(roleItem.moduleId);
  }
  if (state.advancedStudies?.active) modules.add('advanced-studies');
  return [...modules];
}

export function recommendDashboards(state) {
  const dashboardIds = new Set();
  for (const selection of state.roleSelections || []) {
    const roleItem = lookupRole(state, selection.roleId);
    for (const id of roleItem?.dashboardIds || []) dashboardIds.add(id);
  }
  const selectedRoleIds = new Set((state.roleSelections || []).map((item) => item.roleId));
  if (selectedRoleIds.has('prelicensure-nursing-student') && selectedRoleIds.has('nursing-assistant-pct')) {
    dashboardIds.delete('prelicensure-student');
    dashboardIds.delete('nursing-assistant-workforce');
    dashboardIds.add('student-assistant-bridge');
  }
  if (state.advancedStudies?.active) {
    dashboardIds.add('advanced-studies-certification');
    const types = new Set((state.advancedStudies.pathways || []).map((item) => item.type));
    if (['masters-degree', 'doctoral-degree', 'postdoctoral-study', 'residency-fellowship'].some((item) => types.has(item))) dashboardIds.add('graduate-degree-research');
  }
  if ((state.pressures?.load || 0) >= 4) dashboardIds.add('wellness-sustainability');
  const scored = scoreRoleConstellation(state);
  const roleLabels = Object.fromEntries(Object.values(scored).filter(Array.isArray).flat().map((item) => [item.roleId, item.label]));
  return [...dashboardIds].map((id) => {
    const item = DASHBOARD_CATALOG[id];
    if (!item) return null;
    const rolesSupported = (state.roleSelections || []).filter((selection) => (lookupRole(state, selection.roleId)?.dashboardIds || []).includes(id)).map((selection) => roleLabels[selection.roleId] || lookupRole(state, selection.roleId)?.label).filter(Boolean);
    return {
      ...item,
      rolesSupported: rolesSupported.length ? rolesSupported : [...item.rolesSupported],
      currentPriorities: [...item.currentPriorities, ...(state.advancedStudies?.active && id === 'advanced-studies-certification' ? (state.advancedStudies.pathways || []).map((pathway) => pathway.target).filter(Boolean) : [])],
      sharedFoundation: 'one-core-soul',
      autonomy: 'A0-recommendation-only'
    };
  }).filter(Boolean);
}

function defaultAgentIdsForRoles(state) {
  const ids = new Set();
  for (const selection of state.roleSelections || []) {
    const roleItem = lookupRole(state, selection.roleId);
    for (const dashboardId of roleItem?.dashboardIds || []) {
      for (const agentId of DASHBOARD_CATALOG[dashboardId]?.recommendedAgents || []) ids.add(agentId);
    }
  }
  return ids;
}

export function recommendAgents(state) {
  const ids = defaultAgentIdsForRoles(state);
  for (const id of state.ai?.relationshipModes || []) if (AGENT_CATALOG[id]) ids.add(id);
  if (state.advancedStudies?.active) ['tutor', 'coach', 'project-manager'].forEach((id) => ids.add(id));
  return [...ids].map((id) => AGENT_CATALOG[id]).filter(Boolean);
}

function list(value, maxItems = 24, maxLength = 200) {
  return Array.isArray(value) ? value.filter((item) => typeof item === 'string' && item.trim()).map((item) => item.trim().slice(0, maxLength)).slice(0, maxItems) : [];
}

function text(value, maxLength = 3000) {
  return String(value || '').slice(0, maxLength);
}

function legacyRoleFor(state) {
  const primary = state.roleSelections?.find((item) => item.status === 'primary');
  return lookupRole(state, primary?.roleId)?.legacyRole || 'other';
}

function serializedRole(item) {
  return {
    role_id: item.roleId,
    label: item.label,
    domain_id: item.domainId,
    status: item.status,
    intensity: item.intensity,
    attention: item.attention,
    responsibility: item.responsibility,
    identity_salience: item.identity,
    confidence: item.confidence,
    authorization: item.authorization,
    competence_evidence: item.competenceEvidence,
    credential_status: item.credentialStatus,
    verification: item.verification,
    authority_granted: false
  };
}

function serializedModuleAnswers(state) {
  const allowedModules = new Set(recommendedModuleIds(state));
  return Object.fromEntries(Object.entries(state.moduleAnswers || {}).filter(([moduleId, answers]) => allowedModules.has(moduleId) && answers && typeof answers === 'object' && !Array.isArray(answers)).map(([moduleId, answers]) => [moduleId, {
    verification: 'self-reported-context-not-verification',
    authority_granted: false,
    answers: Object.fromEntries(Object.entries(answers).filter(([questionId, value]) => /^[A-Za-z][A-Za-z0-9]{1,79}$/.test(questionId) && typeof value === 'string').map(([questionId, value]) => [questionId, value.slice(0, 3000)]))
  }]));
}

function serializedStudyPathway(item, index) {
  const id = /^study-pathway-[a-z0-9-]{1,48}$/.test(item?.id || '') ? item.id : `study-pathway-${index + 1}`;
  return {
    id,
    type: text(item?.type, 80), target: text(item?.target, 300), stage: text(item?.stage, 80),
    motivation: text(item?.motivation, 2000), outcome: text(item?.outcome, 2000), milestoneDate: text(item?.milestoneDate, 10),
    requiredCompetencies: text(item?.requiredCompetencies), progressEvidence: text(item?.progressEvidence),
    gaps: text(item?.gaps), priorities: text(item?.priorities), formats: list(item?.formats, 24, 160),
    availableTime: text(item?.availableTime, 300), constraints: text(item?.constraints, 1000), accountability: text(item?.accountability, 1000),
    mentorship: text(item?.mentorship, 1000), roleRelationship: text(item?.roleRelationship, 2000), financialBarriers: text(item?.financialBarriers, 1000),
    workloadBarriers: text(item?.workloadBarriers, 1000), familyResponsibilities: text(item?.familyResponsibilities, 1000), wellnessConsiderations: text(item?.wellnessConsiderations, 1000),
    institutionalSupport: text(item?.institutionalSupport, 1000), applicationOpportunities: text(item?.applicationOpportunities, 2000), renewalRequirements: text(item?.renewalRequirements, 1000),
    integrityBoundary: text(item?.integrityBoundary, 2000), verification: 'self-reported-not-verified', authority_granted: false
  };
}

export function buildOsConfig(state, generatedAt = null) {
  const timestamp = generatedAt ? new Date(generatedAt).toISOString() : new Date().toISOString();
  const scored = scoreRoleConstellation(state);
  const primaryLabel = scored.primary[0]?.label || '';
  const delegation = Object.fromEntries(DELEGATION_ACTIVITIES.map((activity) => [activity.id, applyGovernanceFloor(activity.id, state.ai?.delegation?.[activity.id])]));
  const allowedSpheres = new Set(['personal', 'professional', 'community', 'sidegig', 'interest']);
  const spheres = [...new Set(Array.isArray(state.spheres) ? state.spheres.filter((item) => allowedSpheres.has(item)) : [])];
  if (!spheres.length) spheres.push('professional');
  const tierCeilings = Object.fromEntries(spheres.map((sphere) => [sphere, ['personal', 'sidegig', 'interest'].includes(sphere) ? 'green' : 'yellow']));
  return {
    schema_version: '2.0.0',
    generated_at: timestamp,
    generator: 'soul-quiz-role-constellation',
    identity: {
      name: String(state.name || ''),
      role: legacyRoleFor(state),
      role_label: primaryLabel,
      one_liner: String(state.core?.mission || ''),
      always_remember: String(state.core?.alwaysRemember || '')
    },
    voice: {
      length: state.core?.voice?.length || 'Bulleted & structured',
      formality: state.core?.voice?.formality || 'Professional',
      pushback: state.core?.voice?.pushback || '',
      avoid: state.core?.voice?.avoid || ''
    },
    values: list(state.core?.values),
    spheres,
    interests: [],
    tier_ceilings: tierCeilings,
    boundaries: {
      no_phi_confirmed: state.safety?.noPhi === true,
      no_clinical_decisions_confirmed: state.safety?.noClinicalAuthority === true,
      no_academic_dishonesty_confirmed: state.safety?.noAcademicDishonesty === true,
      no_credential_inference_confirmed: state.safety?.noCredentialInference === true,
      confidential_list: [],
      wellbeing_rule: String(state.pressures?.wellnessLimit || ''),
      decisions_always_mine: ['Clinical decisions', 'Academic and evaluative decisions', 'Employment and personnel decisions', 'Legal and financial decisions', 'Institutional authority decisions'],
      drafts_without_asking: Object.entries(delegation).filter(([, level]) => level === 'independent-private').map(([id]) => id),
      memory_allowed: list(state.ai?.memoryAllowed, 24, 200),
      memory_forbidden: list(state.ai?.memoryForbidden, 24, 200),
      escalation_triggers: list(state.ai?.escalationTriggers, 24, 300),
      delegation_matrix: delegation
    },
    role_constellation: {
      primary: scored.primary.map(serializedRole),
      supporting: scored.supporting.map(serializedRole),
      emerging: scored.emerging.map(serializedRole),
      contextual: scored.contextual.map(serializedRole),
      synergies: scored.synergies,
      tensions: scored.tensions,
      custom_roles: (state.customRoles || []).map((item) => ({ role_id: item.id, label: item.label, domain_id: item.domainId, status: 'local-draft-not-reviewed', authority_granted: false }))
    },
    development: {
      stages: list(state.developmentalStages),
      confidence_is_not_competence: true,
      quiz_verifies_competence: false
    },
    capacity: {
      current_pressures: list(state.pressures?.selected),
      self_reported_load: boundedRating(state.pressures?.load, 3),
      wellness_limit: String(state.pressures?.wellnessLimit || ''),
      performance_or_fitness_assessment: false
    },
    role_module_context: serializedModuleAnswers(state),
    advanced_studies: {
      active: state.advancedStudies?.active === true,
      pathways: state.advancedStudies?.active ? (state.advancedStudies.pathways || []).map(serializedStudyPathway) : []
    },
    mission: {
      purpose: String(state.core?.mission || ''),
      populations_and_systems: String(state.core?.populations || ''),
      shared_goals: String(state.core?.sharedGoals || ''),
      commitment_boundaries: String(state.core?.commitmentBoundaries || ''),
      motivations: list(state.core?.motivations),
      strengths: String(state.core?.strengths || ''),
      work_styles: list(state.core?.workStyles),
      learning_styles: list(state.core?.learningStyles)
    },
    decision_style: Object.fromEntries(Object.keys(createInitialState().decisionStyle).map((key) => [key, boundedRating(state.decisionStyle?.[key], 3)])),
    ai_operating_preferences: {
      primary_mode: state.ai?.primaryMode || '',
      relationship_modes: list(state.ai?.relationshipModes),
      delegation_matrix: delegation
    },
    mission_controls: recommendDashboards(state).map((item) => ({ id: item.id, name: item.name, shared_foundation: item.sharedFoundation, autonomy: item.autonomy, roles_supported: item.rolesSupported, human_review: item.humanReview, data_boundaries: item.dataBoundaries })),
    recommended_agents: recommendAgents(state).map((item) => ({ id: item.id, name: item.name, activation: item.activation, human_gate: item.humanGate })),
    authority: {
      self_reported_profile: true,
      credentials_verified: false,
      competence_verified: false,
      employment_or_assignment_verified: false,
      professional_authority_granted: false,
      institutional_authority_granted: false
    },
    doctrine: {
      edena: 'edena-policy@2.0.0',
      florence_x: 'florence-x@2.0.0',
      core_line: 'Agents propose. Humans judge. Nurses steward.'
    }
  };
}

function mdList(items, empty = '_(not specified)_') {
  const values = Array.isArray(items) ? items.filter(Boolean) : [];
  return values.length ? values.map((item) => `- ${item}`).join('\n') : `- ${empty}`;
}

function roleSection(title, items) {
  return `### ${title}\n${items.length ? items.map((item) => `- **${item.label}** — intensity ${item.intensity}; authorization: ${item.authorization}; competence evidence: ${item.competenceEvidence}; credential: ${item.credentialStatus}; self-reported, not verified; no authority granted.`).join('\n') : '- _(none declared)_'}`;
}

export function buildSoulDocuments(state, generatedAt = null) {
  const timestamp = generatedAt ? new Date(generatedAt).toISOString() : new Date().toISOString();
  const scored = scoreRoleConstellation(state);
  const dashboards = recommendDashboards(state);
  const agents = recommendAgents(state);
  const delegation = Object.fromEntries(DELEGATION_ACTIVITIES.map((activity) => [activity.label, applyGovernanceFloor(activity.id, state.ai?.delegation?.[activity.id])]));
  const core = `# Core SOUL — ${state.name || '(name not supplied)'}

> One integrated professional soul expressed through multiple roles. This Core SOUL is the shared foundation for every Mission Control.

## Who I am
- **Mission and purpose:** ${state.core?.mission || '_(not specified)_'}
- **People, populations, and systems I serve:** ${state.core?.populations || '_(not specified)_'}
- **Shared near-term goals:** ${state.core?.sharedGoals || '_(not specified)_'}
- **Scheduling and commitment boundaries:** ${state.core?.commitmentBoundaries || '_(not specified)_'}
- **Always remember:** ${state.core?.alwaysRemember || '_(not specified)_'}

## Mission Control environments
${mdList(state.spheres)}

## Core values
${mdList(state.core?.values)}

## Motivations and strengths
${mdList(state.core?.motivations)}
- **Strengths:** ${state.core?.strengths || '_(not specified)_'}

## Working and learning preferences
- **Work styles:** ${list(state.core?.workStyles).join(', ') || '_(not specified)_'}
- **Learning styles:** ${list(state.core?.learningStyles).join(', ') || '_(not specified)_'}
- **Communication:** ${state.core?.voice?.length || ''}; ${state.core?.voice?.formality || ''}; ${state.core?.voice?.pushback || ''}

## Role constellation
${roleSection('Primary roles', scored.primary)}

${roleSection('Supporting roles', scored.supporting)}

${roleSection('Emerging roles', scored.emerging)}

${roleSection('Contextual roles', scored.contextual)}

## Role synergies
${mdList(scored.synergies)}

## Potential tensions and overload
${mdList(scored.tensions)}

## Wellness and sustainability
- **Current pressures:** ${list(state.pressures?.selected).join(', ') || '_(not specified)_'}
- **Protected limit:** ${state.pressures?.wellnessLimit || '_(not specified)_'}

## Human judgment
Clinical, academic, evaluative, employment, legal, financial, and institutional decisions remain with accountable humans. Role selection, confidence, interest, and aspiration do not verify competence, credentials, assignments, or authority.

## Stewardship line
> Agents propose. Humans judge. Nurses steward.
`;
  const constellation = `# Role Constellation — ${state.name || '(name not supplied)'}

> Current roles, current authorization, demonstrated competence evidence, confidence, developing capability, formal credential, and aspiration remain separate fields.

${roleSection('Primary roles', scored.primary)}

${roleSection('Supporting roles', scored.supporting)}

${roleSection('Emerging roles', scored.emerging)}

${roleSection('Contextual roles', scored.contextual)}

## Current developmental stages
${mdList(state.developmentalStages)}

## Synergies
${mdList(scored.synergies)}

## Tensions
${mdList(scored.tensions)}

## Interpretation rule
No single archetype is produced. The declared primary role names the current center of gravity; supporting, emerging, and contextual roles remain visible and coordinated through one Core SOUL.
`;
  const missionControls = `# Mission Control Recommendations — ${state.name || '(name not supplied)'}

## Shared foundation
Every dashboard uses the same Core SOUL, core values, mission, approved memory, governance boundaries, goals, calendar, commitments, wellness limits, and learning priorities. “Mission Control” is an organizational view—not a credential, competence finding, approval, command authority, separate personality, or authority grant.

${dashboards.map((item) => `## ${item.name}
- **Purpose:** ${item.purpose}
- **Roles supported:** ${item.rolesSupported.join(', ') || 'Cross-role'}
- **Primary objectives:** ${item.primaryObjectives.join('; ')}
- **Current priorities:** ${item.currentPriorities.join('; ')}
- **Information requirements:** ${item.informationRequirements.join('; ')}
- **Recommended AI agents:** ${item.recommendedAgents.join(', ')}
- **Core workflows:** ${item.coreWorkflows.join('; ')}
- **Learning or competency goals:** ${item.learningGoals.join('; ')}
- **Milestones:** ${item.milestones.join('; ')}
- **Performance indicators:** ${item.performanceIndicators.join('; ')}
- **Permissions:** ${item.permissions.join('; ')}
- **Data boundaries:** ${item.dataBoundaries.join('; ')}
- **Human-review requirements:** ${item.humanReview.join('; ')}
- **Safety safeguards:** ${item.safeguards.join('; ')}
- **Relationship to other dashboards:** ${item.relationships.join('; ')}
- **Current posture:** A0 recommendation only; EDENA not evaluated; nothing activated.
`).join('\n')}`;
  const governance = `# AI Governance Profile — ${state.name || '(name not supplied)'}

## AI relationship
- **Primary mode:** ${state.ai?.primaryMode || '_(not specified)_'}
- **Supporting modes:** ${list(state.ai?.relationshipModes).join(', ') || '_(not specified)_'}

## What AI may do independently
Only private, reversible, no-PHI preparation explicitly marked \`independent-private\`; output remains subject to human review before use.

## Delegation matrix
${Object.entries(delegation).map(([activity, level]) => `- **${activity}:** ${level}`).join('\n')}

## What requires confirmation
External, consequential, irreversible, or authority-sensitive work requires explicit confirmation and the appropriate accountable human.

## What requires supervision or accountable professional judgment
Clinical, learner-impact, employment, personnel, research/QI determination, institutional, legal, financial, and governance decisions remain human-owned.

## What AI must never do
- Process PHI or patient-identifiable content in this no-PHI system
- Make patient-specific clinical decisions
- Fabricate citations, qualifications, credentials, experiences, competencies, evidence, validation, or accomplishments
- Complete prohibited academic work, impersonate the user, or facilitate academic dishonesty
- Grant professional, institutional, community, clinical, academic, or employment authority
- Activate tools, connectors, agents, publishing, messaging, scheduling, or automation from this recommendation

## Memory
### May remember only with approval
${mdList(state.ai?.memoryAllowed)}

### Must not retain
${mdList(state.ai?.memoryForbidden)}

## Escalation triggers
${mdList(state.ai?.escalationTriggers)}

## Human judgment
When information is missing, contradictory, high-risk, or outside declared authority, stop and ask for clarification or escalate to the appropriate human authority.
`;
  const moduleContexts = serializedModuleAnswers(state);
  const roleContext = `# Role Context Deep Dives — ${state.name || '(name not supplied)'}

> These answers are self-reported context, not verification of a role, assignment, credential, competence, scope, privilege, permission, or authority. No authority is granted.

${Object.entries(moduleContexts).length ? Object.entries(moduleContexts).map(([moduleId, context]) => {
    const module = CONDITIONAL_MODULES[moduleId];
    const labels = Object.fromEntries((module?.questions || []).map((question) => [question.id, question.label]));
    return `## ${module?.name || moduleId}\n${Object.entries(context.answers).map(([questionId, answer]) => `### ${labels[questionId] || questionId}\n${answer || '_(not specified)_'}`).join('\n\n')}\n\n- **Verification:** self-reported context, not verification\n- **Authority granted:** no`;
  }).join('\n\n') : 'No optional role deep-dive answers were recorded in this version.'}

## Human judgment
Jurisdiction, law, policy, assignment, delegation, supervision, privileges, credentialing, program rules, and accountable institutional owners remain controlling.
`;
  const documents = [
    { name: 'Core-SOUL.md', path: '01-SOUL/Core-SOUL.md', content: core },
    { name: 'Role-Constellation.md', path: '01-SOUL/Role-Constellation.md', content: constellation },
    { name: 'Role-Context-Deep-Dives.md', path: '01-SOUL/Role-Context-Deep-Dives.md', content: roleContext },
    { name: 'Mission-Control-Recommendations.md', path: '02-Mission-Control/Mission-Control-Recommendations.md', content: missionControls },
    { name: 'AI-Governance-Profile.md', path: '04-Governance/AI-Governance-Profile.md', content: governance }
  ];
  if (state.advancedStudies?.active) {
    documents.push({
      name: 'Advanced-Studies-SOUL.md', path: '01-SOUL/Advanced-Studies-SOUL.md',
      content: `# Advanced Studies SOUL — ${state.name || '(name not supplied)'}

> Advanced Studies is a cross-role growth layer, not a separate professional identity and not proof of enrollment, eligibility, progress, competence, certification, or authority.

${(state.advancedStudies.pathways || []).map((item, index) => `## Pathway ${index + 1}: ${item.target || '_(target not specified)_'}
- **Type:** ${item.type || ''}
- **Motivation:** ${item.motivation || ''}
- **Intended outcome:** ${item.outcome || ''}
- **Current stage:** ${item.stage || ''}
- **Milestone:** ${item.milestoneDate || ''}
- **Progress evidence:** ${item.progressEvidence || ''}
- **Knowledge or competency gaps:** ${item.gaps || ''}
- **Relationship to other roles:** ${item.roleRelationship || ''}
- **Barriers and wellness:** ${[item.financialBarriers, item.workloadBarriers, item.familyResponsibilities, item.wellnessConsiderations].filter(Boolean).join('; ')}
- **Academic-integrity boundary:** ${item.integrityBoundary || 'AI may tutor and plan; it may not impersonate, fabricate, or complete prohibited work.'}
`).join('\n')}

## Human judgment
Faculty, preceptors, programs, employers, certifying bodies, and licensed or otherwise accountable professionals retain their respective authority.
`
    });
  }
  documents.push({ name: 'SOUL-Profile-Metadata.md', path: '01-SOUL/SOUL-Profile-Metadata.md', content: `# SOUL Profile Metadata

- **Generated:** ${timestamp}
- **Schema:** 2.0.0
- **Verification:** self-reported profile context; not independently verified
- **Authority posture:** no authority granted
- **Routine review:** every 90 days
- **Review sooner when:** a role, assignment, scope, supervision arrangement, credential, study pathway, workload, wellness limit, goal, permission, or privacy boundary changes

## Update process
1. Reopen or rerun the SOUL Quiz without entering PHI or protected records.
2. Compare roles, authorization, competence evidence, confidence, credentials, goals, capacity, and study pathways as separate fields.
3. Review Mission Control recommendations and governance floors with the accountable human owner.
4. Export a new bundle and preserve the prior approved version according to local policy.
5. Do not treat a profile update as verification, permission, credentialing, or tool activation.
` });
  return documents;
}

export function normalizeState(candidate) {
  const plain = (value) => Boolean(value) && typeof value === 'object' && !Array.isArray(value);
  const text = (value, max = 3000) => typeof value === 'string' && value.length <= max ? value : null;
  const strings = (value, maxItems = 24, maxLength = 3000) => Array.isArray(value) && value.length <= maxItems && value.every((item) => typeof item === 'string' && item.length <= maxLength) ? [...value] : null;
  const rating = (value) => Number.isInteger(value) && value >= 1 && value <= 5;
  try {
    if (!plain(candidate) || candidate.schemaVersion !== SCHEMA_VERSION || text(candidate.name, 80) === null) return null;
    for (const key of ['core', 'pressures', 'decisionStyle', 'ai', 'advancedStudies', 'safety', 'moduleAnswers']) if (!plain(candidate[key])) return null;
    if (!plain(candidate.core.voice) || !plain(candidate.ai.delegation)) return null;
    const base = createInitialState(candidate.updatedAt || null);
    const domainIds = new Set(ROLE_DOMAINS.map((item) => item.id));
    if (!Array.isArray(candidate.customRoles) || candidate.customRoles.length > 12) return null;
    const customRoles = candidate.customRoles.map((item) => {
      if (!plain(item) || !/^local-role-[a-z0-9][a-z0-9-]{0,69}$/.test(item.id || '') || validateCustomRoleTitle(item.label) !== item.label || !domainIds.has(item.domainId)) throw new Error('invalid custom role');
      if (text(item.moduleId, 80) === null || !Array.isArray(item.dashboardIds) || item.dashboardIds.some((id) => text(id, 80) === null) || item.status !== 'local-draft-not-reviewed') throw new Error('invalid custom role metadata');
      return { id: item.id, label: item.label, domainId: item.domainId, moduleId: item.moduleId, dashboardIds: [...item.dashboardIds], authorityDisclaimer: AUTHORITY_DISCLAIMER, status: 'local-draft-not-reviewed' };
    });
    if (new Set(customRoles.map((item) => item.id)).size !== customRoles.length) return null;
    const customById = new Map(customRoles.map((item) => [item.id, item]));
    if (!Array.isArray(candidate.roleSelections) || candidate.roleSelections.length > 24) return null;
    const roleSelections = candidate.roleSelections.map((item) => {
      if (!plain(item) || !ROLE_STATUSES.includes(item.status) || (!roleById(item.roleId) && !customById.has(item.roleId))) throw new Error('invalid role selection');
      if (![item.attention, item.responsibility, item.identity, item.confidence].every(rating)) throw new Error('invalid role rating');
      if (!AUTHORIZATION_VALUES.includes(item.authorization) || !COMPETENCE_EVIDENCE_VALUES.includes(item.competenceEvidence) || !CREDENTIAL_STATUS_VALUES.includes(item.credentialStatus)) throw new Error('invalid role posture');
      if (['primary', 'supporting'].includes(item.status) && item.authorization === 'not-current') throw new Error('contradictory current role');
      return { roleId: item.roleId, status: item.status, attention: item.attention, responsibility: item.responsibility, identity: item.identity, confidence: item.confidence, authorization: item.authorization, competenceEvidence: item.competenceEvidence, credentialStatus: item.credentialStatus };
    });
    const selectedIds = roleSelections.map((item) => item.roleId);
    if (new Set(selectedIds).size !== selectedIds.length || roleSelections.filter((item) => item.status === 'primary').length > 1) return null;
    if (customRoles.some((item) => !selectedIds.includes(item.id)) || selectedIds.some((id) => id.startsWith('local-role-') && !customById.has(id))) return null;
    const developmentalStages = strings(candidate.developmentalStages, 11, 80);
    const spheres = strings(candidate.spheres, 5, 20);
    if (!developmentalStages || developmentalStages.some((id) => !DEVELOPMENTAL_STAGES.some((item) => item.id === id)) || !spheres?.length || spheres.some((id) => !['personal', 'professional', 'community', 'sidegig', 'interest'].includes(id))) return null;
    const safety = {};
    for (const key of ['noPhi', 'noClinicalAuthority', 'noAcademicDishonesty', 'noCredentialInference']) {
      if (typeof candidate.safety[key] !== 'boolean') return null;
      safety[key] = candidate.safety[key];
    }
    const coreArrays = {};
    for (const key of ['values', 'motivations', 'workStyles', 'learningStyles']) {
      coreArrays[key] = strings(candidate.core[key]);
      if (!coreArrays[key]) return null;
    }
    const coreTexts = {};
    for (const key of ['customValues', 'mission', 'populations', 'sharedGoals', 'commitmentBoundaries', 'strengths', 'alwaysRemember']) {
      coreTexts[key] = text(candidate.core[key]);
      if (coreTexts[key] === null) return null;
    }
    const voice = {};
    for (const key of ['length', 'formality', 'pushback', 'avoid']) {
      voice[key] = text(candidate.core.voice[key], 1000);
      if (voice[key] === null) return null;
    }
    const pressureSelected = strings(candidate.pressures.selected);
    if (!pressureSelected || !rating(candidate.pressures.load) || text(candidate.pressures.wellnessLimit, 2000) === null) return null;
    const decisionStyle = {};
    for (const key of Object.keys(base.decisionStyle)) {
      if (!rating(candidate.decisionStyle[key])) return null;
      decisionStyle[key] = candidate.decisionStyle[key];
    }
    const relationshipModes = strings(candidate.ai.relationshipModes, AI_RELATIONSHIP_MODES.length, 80);
    if (!relationshipModes || relationshipModes.some((id) => !AI_RELATIONSHIP_MODES.includes(id)) || (candidate.ai.primaryMode && !relationshipModes.includes(candidate.ai.primaryMode))) return null;
    const memoryAllowed = strings(candidate.ai.memoryAllowed);
    const memoryForbidden = strings(candidate.ai.memoryForbidden);
    const escalationTriggers = strings(candidate.ai.escalationTriggers);
    if (!memoryAllowed || !memoryForbidden || !escalationTriggers || text(candidate.ai.primaryMode, 80) === null) return null;
    if (typeof candidate.advancedStudies.active !== 'boolean' || !Array.isArray(candidate.advancedStudies.pathways) || candidate.advancedStudies.pathways.length > 8 || (!candidate.advancedStudies.active && candidate.advancedStudies.pathways.length)) return null;
    const pathwayIds = new Set();
    const pathways = candidate.advancedStudies.pathways.map((item, index) => {
      if (!plain(item)) throw new Error('invalid pathway');
      const id = item.id || `study-pathway-${index + 1}`;
      if (!/^study-pathway-[a-z0-9-]{1,48}$/.test(id) || pathwayIds.has(id)) throw new Error('invalid pathway id');
      pathwayIds.add(id);
      if (item.type && !ADVANCED_STUDY_TYPES.some((option) => option.id === item.type)) throw new Error('invalid pathway type');
      if (item.stage && !STUDY_STAGE_VALUES.includes(item.stage)) throw new Error('invalid pathway stage');
      const result = { id, type: text(item.type, 100), target: text(item.target, 300), stage: text(item.stage, 160), formats: strings(item.formats || [], 24, 160), verification: 'self-reported-not-verified', authority_granted: false };
      if (Object.values(result).some((value) => value === null)) throw new Error('invalid pathway field');
      for (const key of ['motivation', 'outcome', 'milestoneDate', 'requiredCompetencies', 'progressEvidence', 'gaps', 'priorities', 'availableTime', 'constraints', 'accountability', 'mentorship', 'roleRelationship', 'financialBarriers', 'workloadBarriers', 'familyResponsibilities', 'wellnessConsiderations', 'institutionalSupport', 'applicationOpportunities', 'renewalRequirements', 'integrityBoundary']) {
        const value = text(item[key] || '', key === 'target' ? 300 : 3000);
        if (value === null) throw new Error('invalid pathway text');
        result[key] = value;
      }
      return result;
    });
    const moduleAnswers = {};
    for (const [moduleId, answers] of Object.entries(candidate.moduleAnswers)) {
      if (!CONDITIONAL_MODULES[moduleId] || moduleId === 'advanced-studies' || !plain(answers)) return null;
      moduleAnswers[moduleId] = {};
      for (const [questionId, value] of Object.entries(answers)) {
        if (!CONDITIONAL_MODULES[moduleId].questions.some((item) => item.id === questionId) || text(value) === null) return null;
        moduleAnswers[moduleId][questionId] = value;
      }
    }
    return {
      ...base, name: candidate.name, selectedRoleIds: [...selectedIds], roleSelections, customRoles, spheres: [...new Set(spheres)], developmentalStages: [...new Set(developmentalStages)],
      advancedStudies: { active: candidate.advancedStudies.active, pathways },
      core: { ...coreArrays, ...coreTexts, voice }, pressures: { selected: pressureSelected, load: candidate.pressures.load, wellnessLimit: candidate.pressures.wellnessLimit }, decisionStyle,
      ai: { relationshipModes, primaryMode: candidate.ai.primaryMode, delegation: Object.fromEntries(DELEGATION_ACTIVITIES.map((activity) => [activity.id, applyGovernanceFloor(activity.id, candidate.ai.delegation[activity.id])])), memoryAllowed, memoryForbidden, escalationTriggers },
      safety, moduleAnswers, updatedAt: base.updatedAt
    };
  } catch {
    return null;
  }
}
