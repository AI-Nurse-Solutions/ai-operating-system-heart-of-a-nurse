import {
  STORAGE_KEY,
  ROLE_DOMAINS,
  ROLE_TAXONOMY,
  ROLE_STATUSES,
  DEVELOPMENTAL_STAGES,
  ADVANCED_STUDY_TYPES,
  CONDITIONAL_MODULES,
  AI_RELATIONSHIP_MODES,
  DELEGATION_ACTIVITIES,
  GOVERNANCE_LEVELS,
  createInitialState,
  normalizeState,
  addCustomRole,
  removeCustomRole,
  roleById,
  recommendedModuleIds,
  scoreRoleConstellation,
  recommendDashboards,
  recommendAgents,
  buildOsConfig,
  buildSoulDocuments,
  applyGovernanceFloor
} from './soul-quiz-model.mjs';

const app = document.getElementById('quiz-app');
const status = document.getElementById('quiz-status');
const progress = document.getElementById('quiz-progress');
const progressLabel = document.getElementById('quiz-progress-label');
const resetButton = document.getElementById('reset-quiz');

let state = restoreState();
let stepKey = 'safety';

const CORE_STEP_KEYS = ['safety', 'roles', 'role-details', 'core', 'decisions-ai'];
const STEP_TITLES = Object.freeze({
  safety: 'Stewardship gate',
  roles: 'Your complete role constellation',
  'role-details': 'How each role functions now',
  core: 'Shared Core SOUL and development',
  'decisions-ai': 'Decisions, capacity, and AI relationship',
  review: 'Your integrated SOUL results'
});

const VALUE_OPTIONS = ['dignity', 'safety', 'evidence', 'equity', 'family', 'community', 'integrity', 'service', 'growth', 'rest', 'creativity', 'faith or spirituality', 'agency', 'transparency', 'stewardship'];
const MOTIVATION_OPTIONS = ['service', 'mastery', 'belonging', 'leadership', 'stewardship', 'problem-solving', 'justice', 'creativity', 'independence', 'security', 'learning', 'impact'];
const WORK_STYLE_OPTIONS = ['structured', 'flexible', 'collaborative', 'independent', 'fast-iterative', 'deliberate', 'visual', 'written', 'discussion-based'];
const LEARNING_STYLE_OPTIONS = ['practice questions', 'teach-back', 'simulation', 'case discussion', 'reading', 'video', 'concept maps', 'spaced repetition', 'coaching', 'peer learning'];
const PRESSURE_OPTIONS = ['workload', 'time pressure', 'study time', 'family care', 'financial pressure', 'shift work or call', 'role transition', 'moral distress', 'conflict', 'administrative burden', 'uncertain authority', 'entrepreneurial load'];
const SPHERE_OPTIONS = Object.freeze([
  { id: 'personal', label: 'Personal · private goals, caregiving, and sustainability' },
  { id: 'professional', label: 'Professional · learning, practice, education, leadership, research, and operations' },
  { id: 'community', label: 'Community–Entrepreneurial · advocacy, population work, innovation, and business' },
  { id: 'sidegig', label: 'Side Gig · bounded independent work outside the primary role' },
  { id: 'interest', label: 'Interest · hobbies, curiosity, and non-work development' }
]);
const DECISION_LABELS = Object.freeze({
  evidence: 'Evidence orientation', uncertainty: 'Comfort with uncertainty', risk: 'Risk tolerance', collaboration: 'Collaboration', accountability: 'Explicit accountability', innovation: 'Innovation appetite', conflict: 'Directness in conflict', timePressure: 'Need for structure under time pressure', ethicalConcerns: 'Sensitivity to ethical concerns', competingPriorities: 'Comfort balancing competing priorities'
});
const AUTHORIZATION_OPTIONS = Object.freeze([
  ['self-declared', 'Self-declared role · not verified'],
  ['in-training-supervised', 'In training · supervised · not verified'],
  ['delegated-role-unverified', 'Delegated duties · not verified'],
  ['formally-assigned-unverified', 'Formally assigned · not verified here'],
  ['licensed-or-credentialed-unverified', 'Licensed/credentialed claim · not verified here'],
  ['not-current', 'Not a current assignment']
]);
const COMPETENCE_OPTIONS = Object.freeze([
  ['not-assessed', 'Not assessed'],
  ['developing-not-verified', 'Developing capability · not verified'],
  ['supervised-demonstration-not-verified', 'Supervised demonstration reported · not verified'],
  ['self-reported-practice-not-verified', 'Practice experience reported · not verified'],
  ['formal-verification-not-imported', 'Formal verification exists elsewhere · not imported']
]);
const CREDENTIAL_OPTIONS = Object.freeze([
  ['not-claimed', 'No credential claimed'],
  ['in-progress-not-verified', 'In progress · not verified'],
  ['aspirational-not-verified', 'Aspirational · not current or verified'],
  ['self-reported-not-verified', 'Credential reported · not verified here']
]);
const STUDY_STAGES = Object.freeze([
  ['exploring', 'Exploring'], ['admission-or-application', 'Admission / application'], ['enrolled', 'Enrolled'], ['active-preparation', 'Active preparation'], ['milestone-review', 'Milestone review'], ['exam-ready-self-reported', 'Exam-ready · self-reported only'], ['renewal', 'Renewal / continuing competency'], ['paused', 'Paused']
]);

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
}

function attr(value) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}

function restoreState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    return normalizeState(JSON.parse(raw)) || createInitialState();
  } catch {
    return createInitialState();
  }
}

function saveState(message = 'Draft saved in this tab only.') {
  state.updatedAt = new Date().toISOString();
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    announce(message);
  } catch {
    announce('This browser could not preserve the draft. Download your files when finished.', true);
  }
}

function announce(message, isError = false) {
  status.textContent = message;
  status.classList.toggle('error', isError);
}

function splitList(value, maxItemLength = 160) {
  return [...new Set(String(value || '').split(/[\n,]+/).map((item) => item.trim().slice(0, maxItemLength)).filter(Boolean))].slice(0, 24);
}

function pathwayId(pathway, index) {
  return /^study-pathway-[a-z0-9-]{1,48}$/.test(pathway?.id || '') ? pathway.id : `study-pathway-${index + 1}`;
}

function newStudyPathway() {
  const used = new Set((state.advancedStudies.pathways || []).map((item, index) => pathwayId(item, index)));
  let number = 1;
  while (used.has(`study-pathway-${number}`)) number += 1;
  return { id: `study-pathway-${number}`, type: '', target: '', stage: '', formats: [], verification: 'self-reported-not-verified', authority_granted: false };
}

function studyControlName(id, key) {
  return `study-${id}-${key}`;
}

function optionTags(options, selected) {
  return options.map(([value, label]) => `<option value="${attr(value)}"${value === selected ? ' selected' : ''}>${escapeHtml(label)}</option>`).join('');
}

function checklist(name, options, selected = [], className = 'choice-grid') {
  const chosen = new Set(selected || []);
  return `<div class="${className}">${options.map((option) => {
    const value = typeof option === 'string' ? option : option.id;
    const label = typeof option === 'string' ? option : option.label;
    return `<label class="choice"><input type="checkbox" name="${attr(name)}" value="${attr(value)}"${chosen.has(value) ? ' checked' : ''}> <span>${escapeHtml(label)}</span></label>`;
  }).join('')}</div>`;
}

function ratingSelect(name, value = 3, left = '1 · lower', right = '5 · higher') {
  return `<select id="${attr(name)}" name="${attr(name)}"><option value="1"${value === 1 ? ' selected' : ''}>${escapeHtml(left)}</option><option value="2"${value === 2 ? ' selected' : ''}>2</option><option value="3"${value === 3 ? ' selected' : ''}>3 · situational</option><option value="4"${value === 4 ? ' selected' : ''}>4</option><option value="5"${value === 5 ? ' selected' : ''}>${escapeHtml(right)}</option></select>`;
}

function formShell(title, intro, body, options = {}) {
  const { back = true, nextLabel = 'Continue', next = true, defer = false } = options;
  return `<form id="quiz-form" novalidate>
    <div class="step-heading"><p class="step-kicker">${escapeHtml(options.kicker || 'SOUL Quiz v2')}</p><h2 tabindex="-1">${escapeHtml(title)}</h2><p>${intro}</p></div>
    <div id="step-error" class="form-error" role="alert" tabindex="-1" hidden></div>
    ${body}
    <div class="quiz-actions">
      ${back ? '<button class="btn btn-secondary" type="button" data-nav="back">← Back</button>' : '<span></span>'}
      <button class="btn btn-quiet" type="button" data-action="save">Save in this tab</button>
      ${defer ? '<button class="btn btn-quiet" type="submit" name="defer-optional" value="true">Defer optional details</button>' : ''}
      ${next ? `<button class="btn btn-primary" type="submit">${escapeHtml(nextLabel)} →</button>` : ''}
    </div>
  </form>`;
}

function safetyView() {
  const checks = [
    ['noPhi', 'No PHI, patient identifiers, protected records, patient stories, screenshots, credentials, or secrets.'],
    ['noClinicalAuthority', 'AI may prepare and support; accountable humans retain clinical, academic, employment, legal, financial, and institutional judgment.'],
    ['noAcademicDishonesty', 'AI may tutor and coach; it may not complete prohibited academic work, impersonate me, or fabricate experiences, citations, competencies, or accomplishments.'],
    ['noCredentialInference', 'This quiz does not verify roles, competence, licenses, credentials, appointments, assignments, privileges, or authority.']
  ];
  const body = `<div class="boundary-panel"><strong>Private, no-PHI intake.</strong> Nothing is submitted to Nurse AI OS. Your in-progress draft is stored only in this browser tab. Close or reset the tab to remove it; downloaded files remain under your control.</div>
    <div class="field"><label for="person-name">Name Nurse AI OS should use <span class="required">required</span></label><input id="person-name" name="name" maxlength="80" autocomplete="off" value="${attr(state.name)}" required><small>A first name, nickname, or initials are enough. Do not enter a patient, employee, or student identifier.</small></div>
    <fieldset><legend>Four stewardship confirmations <span class="required">all required</span></legend>
      ${checks.map(([key, label]) => `<label class="safety-check"><input type="checkbox" name="safety-${key}"${state.safety[key] ? ' checked' : ''} required> <span>${escapeHtml(label)}</span></label>`).join('')}
    </fieldset>
    <details class="why"><summary>Why these gates come first</summary><p>They establish privacy, academic integrity, scope, and human accountability before personalization. The system must know its limits before it learns your preferences.</p></details>`;
  return formShell('Begin with stewardship', 'Broad strokes now; go deeper later. More complete answers will help Nurse AI OS serve you better, but trust and detail can grow over time.', body, { back: false });
}

function rolesView() {
  const selected = new Set((state.roleSelections || []).map((item) => item.roleId));
  const grouped = ROLE_DOMAINS.map((domain, index) => {
    const roles = ROLE_TAXONOMY.filter((item) => item.domainId === domain.id);
    return `<details class="role-domain"${index < 2 ? ' open' : ''}><summary>${escapeHtml(domain.label)} <span>${roles.length}</span></summary><div class="role-list">${roles.map((item) => `<label class="role-option" data-search="${attr(`${item.label} ${domain.label}`.toLowerCase())}"><input type="checkbox" name="role" value="${attr(item.id)}"${selected.has(item.id) ? ' checked' : ''}> <span><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(domain.label)}</small></span></label>`).join('')}</div></details>`;
  }).join('');
  const custom = (state.customRoles || []).map((item) => `<li><span><strong>${escapeHtml(item.label)}</strong> · ${escapeHtml(ROLE_DOMAINS.find((domain) => domain.id === item.domainId)?.label || item.domainId)} · local draft, not reviewed</span> <button class="btn btn-quiet" type="button" data-action="remove-custom-role" data-role-id="${attr(item.id)}" aria-label="Remove local role ${attr(item.label)}">Remove</button></li>`).join('');
  const body = `<div class="boundary-panel"><strong>Choose every role that matters.</strong> You will name one current center of gravity next, while keeping supporting, emerging, and contextual roles visible.</div>
    <div class="field"><label for="role-filter">Find a role</label><input id="role-filter" type="search" placeholder="Try educator, clinic, research, AI, caregiver…" autocomplete="off"><small>Filter only changes what is visible; it does not change selections.</small></div>
    <fieldset><legend>Professional role taxonomy <span class="required">choose at least one</span></legend>${grouped}</fieldset>
    <section class="custom-role"><h3>Add an emerging or local role</h3><p>Use a generic role title—never a person, organization, record identifier, or narrative.</p>
      <div class="three-col"><div class="field"><label for="custom-title">Role title</label><input id="custom-title" maxlength="60" placeholder="Example: Rural health program coordinator"></div>
      <div class="field"><label for="custom-domain">Domain</label><select id="custom-domain">${ROLE_DOMAINS.map((domain) => `<option value="${attr(domain.id)}">${escapeHtml(domain.label)}</option>`).join('')}</select></div>
      <div class="field"><label for="custom-status">Status</label><select id="custom-status">${ROLE_STATUSES.map((value) => `<option value="${value}"${value === 'contextual' ? ' selected' : ''}>${value}</option>`).join('')}</select></div></div>
      <button class="btn btn-secondary" type="button" data-action="add-custom-role">Add local role</button>
      ${custom ? `<ul class="compact-list">${custom}</ul>` : ''}
    </section>`;
  return formShell('Map your complete role constellation', 'Roles may be congruent, complementary, and simultaneous. Selecting a role records a self-report only; it grants no authority.', body);
}

function selectedRole(stateValue, id) {
  return stateValue.roleSelections.find((item) => item.roleId === id);
}

function roleLabel(id) {
  return roleById(id)?.label || state.customRoles.find((item) => item.id === id)?.label || id;
}

function roleDetailsView() {
  const rows = state.roleSelections.map((item) => `<article class="role-detail-card">
    <header><h3>${escapeHtml(roleLabel(item.roleId))}</h3><p>Self-reported · not independently verified · no authority granted</p></header>
    <div class="role-detail-grid">
      <div class="field"><label for="${attr(item.roleId)}-status">Status</label><select id="${attr(item.roleId)}-status" name="${attr(item.roleId)}-status">${ROLE_STATUSES.map((value) => `<option value="${value}"${item.status === value ? ' selected' : ''}>${value}</option>`).join('')}</select></div>
      <div class="field"><label for="${attr(item.roleId)}-attention">Attention now</label>${ratingSelect(`${item.roleId}-attention`, Number(item.attention || 1))}</div>
      <div class="field"><label for="${attr(item.roleId)}-responsibility">Current responsibility</label>${ratingSelect(`${item.roleId}-responsibility`, Number(item.responsibility || 1))}</div>
      <div class="field"><label for="${attr(item.roleId)}-identity">Identity salience</label>${ratingSelect(`${item.roleId}-identity`, Number(item.identity || 1))}</div>
      <div class="field"><label for="${attr(item.roleId)}-confidence">Confidence <small>not competence</small></label>${ratingSelect(`${item.roleId}-confidence`, Number(item.confidence || 1))}</div>
      <div class="field"><label for="${attr(item.roleId)}-authorization">Current authorization posture</label><select id="${attr(item.roleId)}-authorization" name="${attr(item.roleId)}-authorization">${optionTags(AUTHORIZATION_OPTIONS, item.authorization)}</select></div>
      <div class="field"><label for="${attr(item.roleId)}-competence">Competence-evidence posture</label><select id="${attr(item.roleId)}-competence" name="${attr(item.roleId)}-competence">${optionTags(COMPETENCE_OPTIONS, item.competenceEvidence)}</select></div>
      <div class="field"><label for="${attr(item.roleId)}-credential">Credential posture</label><select id="${attr(item.roleId)}-credential" name="${attr(item.roleId)}-credential">${optionTags(CREDENTIAL_OPTIONS, item.credentialStatus)}</select></div>
    </div>
  </article>`).join('');
  const body = `<div class="boundary-panel"><strong>Exactly one primary role is required.</strong> Primary means this season’s center of gravity—not your only identity. High confidence never becomes verified competence or authority.</div>${rows}`;
  return formShell('Describe how each role functions', 'Use current reality for primary and supporting roles. Use emerging for what you are intentionally developing and contextual for roles active only in certain settings or seasons.', body);
}

function coreView() {
  const studies = state.advancedStudies?.pathways?.length ? state.advancedStudies.pathways : [newStudyPathway()];
  const studyCards = studies.map((study, index) => {
    const id = pathwayId(study, index);
    return `<article class="role-detail-card study-pathway-card" data-study-pathway-quick="${attr(id)}"><header><h3>Pathway ${index + 1}</h3>${state.advancedStudies.pathways.length ? `<button class="btn btn-quiet" type="button" data-action="remove-study-pathway" data-pathway-id="${attr(id)}" aria-label="Remove Advanced Studies pathway ${index + 1}">Remove</button>` : ''}</header><div class="three-col"><div class="field"><label for="${attr(studyControlName(id, 'type'))}">Pathway type</label><select id="${attr(studyControlName(id, 'type'))}" name="${attr(studyControlName(id, 'type'))}"><option value="">Choose when applicable</option>${ADVANCED_STUDY_TYPES.map((item) => `<option value="${attr(item.id)}"${study.type === item.id ? ' selected' : ''}>${escapeHtml(item.label)}</option>`).join('')}</select></div><div class="field"><label for="${attr(studyControlName(id, 'target'))}">Target</label><input id="${attr(studyControlName(id, 'target'))}" name="${attr(studyControlName(id, 'target'))}" maxlength="300" value="${attr(study.target || '')}" placeholder="Example: CCRN, DNP, MBA"></div><div class="field"><label for="${attr(studyControlName(id, 'stage'))}">Current stage</label><select id="${attr(studyControlName(id, 'stage'))}" name="${attr(studyControlName(id, 'stage'))}"><option value="">Choose when applicable</option>${optionTags(STUDY_STAGES, study.stage || '')}</select></div></div></article>`;
  }).join('');
  const body = `<fieldset><legend>Current learner and developmental stages</legend>${checklist('development', DEVELOPMENTAL_STAGES, state.developmentalStages)}</fieldset>
    <fieldset><legend>Advanced Studies <span class="optional">cross-role overlay</span></legend>
      <label class="safety-check"><input type="checkbox" name="advanced-active"${state.advancedStudies.active ? ' checked' : ''}> <span>I am pursuing a certification, credential, degree, specialization, renewal, residency/fellowship, continuing development, or career transition.</span></label>
      <div class="study-pathway-list">${studyCards}</div><button class="btn btn-secondary" type="button" data-action="add-study-pathway">Add another pathway</button>
      <small>Advanced Studies never replaces a role and does not prove enrollment, eligibility, competence, progress, or a credential.</small>
    </fieldset>
    <fieldset><legend>Mission Control environments <span class="required">choose at least one</span></legend>${checklist('spheres', SPHERE_OPTIONS, state.spheres)}<small>All selected environments share one Core SOUL. Personal, Side Gig, and Interest are capped Green; Professional and Community–Entrepreneurial are capped Yellow. These are ceilings, not activations.</small></fieldset>
    <fieldset><legend>Core values <span class="required">choose at least three</span></legend>${checklist('values', VALUE_OPTIONS, state.core.values)}<div class="field"><label for="custom-values">Other values</label><input id="custom-values" name="custom-values" maxlength="300" value="${attr(state.core.customValues || '')}" placeholder="Comma-separated; optional"></div></fieldset>
    <div class="field"><label for="mission">Mission and purpose <span class="required">required</span></label><textarea id="mission" name="mission" maxlength="3000" required placeholder="Who, what, or which system do you feel responsible for serving?">${escapeHtml(state.core.mission)}</textarea></div>
    <div class="field"><label for="populations">People, populations, organizations, problems, or systems served</label><textarea id="populations" name="populations" maxlength="3000" placeholder="Use broad, non-identifying terms only.">${escapeHtml(state.core.populations)}</textarea></div>
    <div class="field"><label for="shared-goals">Shared near-term goals</label><textarea id="shared-goals" name="shared-goals" maxlength="3000" placeholder="Broad goals only—no patient, student, employee, employer, or private calendar details.">${escapeHtml(state.core.sharedGoals || '')}</textarea></div>
    <div class="field"><label for="commitment-boundaries">Scheduling and commitment boundaries</label><textarea id="commitment-boundaries" name="commitment-boundaries" maxlength="3000" placeholder="Example: protect post-shift sleep; no exact appointments, locations, or identifiable records.">${escapeHtml(state.core.commitmentBoundaries || '')}</textarea></div>
    <fieldset><legend>Primary motivations</legend>${checklist('motivations', MOTIVATION_OPTIONS, state.core.motivations)}</fieldset>
    <div class="field"><label for="strengths">Strengths you rely on</label><textarea id="strengths" name="strengths" maxlength="3000">${escapeHtml(state.core.strengths)}</textarea></div>
    <fieldset><legend>Preferred working styles</legend>${checklist('work-styles', WORK_STYLE_OPTIONS, state.core.workStyles)}</fieldset>
    <fieldset><legend>Preferred learning styles</legend>${checklist('learning-styles', LEARNING_STYLE_OPTIONS, state.core.learningStyles)}</fieldset>
    <div class="two-col"><div class="field"><label for="voice-length">Answer style</label><select id="voice-length" name="voice-length">${optionTags([['Short & direct','Short & direct'],['Long & thorough','Long & thorough'],['Bulleted & structured','Bulleted & structured'],['Conversational','Conversational']],state.core.voice.length)}</select></div>
      <div class="field"><label for="voice-formality">Formality</label><select id="voice-formality" name="voice-formality">${optionTags([['Casual','Casual'],['Professional','Professional'],['Formal','Formal']],state.core.voice.formality)}</select></div></div>
    <div class="field"><label for="voice-pushback">Pushback preference</label><input id="voice-pushback" name="voice-pushback" maxlength="500" value="${attr(state.core.voice.pushback)}"></div>
    <div class="field"><label for="voice-avoid">Language or habits to avoid</label><input id="voice-avoid" name="voice-avoid" maxlength="500" value="${attr(state.core.voice.avoid)}"></div>
    <div class="field"><label for="always-remember">One stable thing Nurse AI OS may remember</label><input id="always-remember" name="always-remember" maxlength="1000" value="${attr(state.core.alwaysRemember)}" placeholder="Do not include health, patient, student, employee, or credential details."></div>`;
  return formShell('Define the shared foundation', 'Values, mission, and preferences remain coherent across every role and Mission Control. Advanced Studies sits beside your roles as an active growth layer.', body);
}

function decisionsAiView() {
  const decisionRows = Object.entries(DECISION_LABELS).map(([key, label]) => `<div class="matrix-row"><label for="decision-${attr(key)}">${escapeHtml(label)}</label>${ratingSelect(`decision-${key}`, Number(state.decisionStyle[key] || 3))}</div>`).join('');
  const chosenModes = state.ai.relationshipModes || [];
  const primaryOptions = AI_RELATIONSHIP_MODES;
  const delegationRows = DELEGATION_ACTIVITIES.map((activity) => {
    const current = applyGovernanceFloor(activity.id, state.ai.delegation[activity.id]);
    const floorIndex = GOVERNANCE_LEVELS.indexOf(activity.floor);
    const allowed = GOVERNANCE_LEVELS.slice(floorIndex).map((level) => [level, level.replaceAll('-', ' ')]);
    return `<div class="delegation-row"><label for="delegation-${attr(activity.id)}"><strong>${escapeHtml(activity.label)}</strong><small>Minimum gate: ${escapeHtml(activity.floor.replaceAll('-', ' '))}</small></label><select id="delegation-${attr(activity.id)}" name="delegation-${attr(activity.id)}">${optionTags(allowed, current)}</select></div>`;
  }).join('');
  const body = `<fieldset><legend>Decision-support preferences <span class="optional">1–5 preference scales, not ability scores</span></legend><div class="matrix">${decisionRows}</div></fieldset>
    <fieldset><legend>Current pressures</legend>${checklist('pressures', PRESSURE_OPTIONS, state.pressures.selected)}<div class="matrix-row"><label for="pressure-load">Overall load</label>${ratingSelect('pressure-load', Number(state.pressures.load || 3), '1 · sustainable', '5 · overloaded')}</div><div class="field"><label for="wellness-limit">Limit the system should protect</label><textarea id="wellness-limit" name="wellness-limit" maxlength="2000" placeholder="Example: protect post-shift sleep and one no-study day.">${escapeHtml(state.pressures.wellnessLimit)}</textarea></div></fieldset>
    <fieldset><legend>How should AI relate to you?</legend>${checklist('ai-modes', AI_RELATIONSHIP_MODES.map((id) => ({ id, label: id.replaceAll('-', ' ') })), chosenModes)}<div class="field"><label for="primary-ai-mode">Primary mode this season</label><select id="primary-ai-mode" name="primary-ai-mode"><option value="">Choose one</option>${primaryOptions.map((id) => `<option value="${attr(id)}"${state.ai.primaryMode === id ? ' selected' : ''}>${escapeHtml(id.replaceAll('-', ' '))}</option>`).join('')}</select></div></fieldset>
    <fieldset><legend>Governed delegation matrix</legend><p class="field-note">“Independent” means private, reversible, no-PHI preparation only. The model enforces minimum human-review floors.</p><div class="delegation-matrix">${delegationRows}</div></fieldset>
    <div class="two-col"><div class="field"><label for="memory-allowed">Information AI may remember with approval</label><textarea id="memory-allowed" name="memory-allowed" maxlength="3000">${escapeHtml(state.ai.memoryAllowed.join('\n'))}</textarea></div><div class="field"><label for="memory-forbidden">Information AI must not retain</label><textarea id="memory-forbidden" name="memory-forbidden" maxlength="3000">${escapeHtml(state.ai.memoryForbidden.join('\n'))}</textarea></div></div>
    <div class="field"><label for="escalation-triggers">Human escalation triggers</label><textarea id="escalation-triggers" name="escalation-triggers" maxlength="3000">${escapeHtml(state.ai.escalationTriggers.join('\n'))}</textarea></div>`;
  return formShell('Configure decisions, capacity, and AI behavior', 'These answers shape support—not competence or authority. Consequential work remains behind the appropriate human gate.', body);
}

function moduleView(moduleId) {
  const module = CONDITIONAL_MODULES[moduleId];
  const answers = state.moduleAnswers[moduleId] || {};
  if (moduleId === 'advanced-studies') return advancedStudiesModuleView(module, answers);
  const requiredIds = moduleId === 'student-assistant' ? new Set(['authorizedScope', 'supervision', 'studentAssistantAiBoundary']) : new Set();
  const studentAssistant = (() => {
    const ids = new Set(state.roleSelections.map((item) => item.roleId));
    if (ids.has('prelicensure-nursing-student') && ids.has('nursing-assistant-pct')) return 'Both selected · student and nursing-assistant contexts remain distinct and non-interchangeable.';
    if (ids.has('prelicensure-nursing-student')) return 'Prelicensure nursing student only · no nursing-assistant employment context inferred.';
    return 'Nursing assistant / CNA / PCT / healthcare assistant only · no student status inferred.';
  })();
  const fields = module.questions.map((question) => question.id === 'studentAssistantCombination'
    ? `<div class="field module-question"><span class="field-label">${escapeHtml(question.label)}</span><p class="derived-answer">${escapeHtml(studentAssistant)}</p><small>Derived from the selected taxonomy roles; it cannot be overwritten with contradictory free text.</small></div>`
    : `<div class="field module-question"><label for="module-${attr(question.id)}">${escapeHtml(question.label)}${requiredIds.has(question.id) ? ' <span class="required">required</span>' : ''}</label><textarea id="module-${attr(question.id)}" name="module-${attr(question.id)}" maxlength="3000"${requiredIds.has(question.id) ? ' required' : ''}>${escapeHtml(answers[question.id] || '')}</textarea><small><strong>Purpose:</strong> ${escapeHtml(question.purpose)} · <strong>Feeds:</strong> ${question.outputs.map(escapeHtml).join(', ')}</small></div>`).join('');
  const safeguards = `<section class="module-safeguards" aria-label="Non-negotiable safeguards"><h3>Non-negotiable safeguards</h3><ul>${module.safeguards.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section>`;
  return formShell(module.name, 'Optional deep dive · about 3–5 minutes. Use generic, non-identifying information. Complete any marked safety fields; broad strokes are enough and all other details can deepen during a later review.', safeguards + fields, { kicker: 'Conditional role module', defer: true });
}

function advancedStudiesModuleView(module) {
  const textField = (id, key, label, value = '', maxLength = 3000, placeholder = '') => `<div class="field"><label for="${attr(studyControlName(id, key))}">${escapeHtml(label)}</label><textarea id="${attr(studyControlName(id, key))}" name="${attr(studyControlName(id, key))}" maxlength="${maxLength}" placeholder="${attr(placeholder)}">${escapeHtml(value)}</textarea></div>`;
  const cards = state.advancedStudies.pathways.map((pathway, index) => {
    const id = pathwayId(pathway, index);
    return `<article class="role-detail-card study-pathway-card study-pathway-full" data-study-pathway-editor="${attr(id)}"><header><h3>Pathway ${index + 1}: ${escapeHtml(pathway.target || 'Untitled pathway')}</h3><button class="btn btn-quiet" type="button" data-action="remove-study-pathway" data-pathway-id="${attr(id)}" aria-label="Remove Advanced Studies pathway ${index + 1}">Remove</button></header>
      <div class="three-col"><div class="field"><label for="${attr(studyControlName(id, 'type'))}">Pathway type <span class="required">required</span></label><select id="${attr(studyControlName(id, 'type'))}" name="${attr(studyControlName(id, 'type'))}" required><option value="">Choose</option>${ADVANCED_STUDY_TYPES.map((item) => `<option value="${attr(item.id)}"${pathway.type === item.id ? ' selected' : ''}>${escapeHtml(item.label)}</option>`).join('')}</select></div><div class="field"><label for="${attr(studyControlName(id, 'target'))}">Target <span class="required">required</span></label><input id="${attr(studyControlName(id, 'target'))}" name="${attr(studyControlName(id, 'target'))}" maxlength="300" required value="${attr(pathway.target || '')}"></div><div class="field"><label for="${attr(studyControlName(id, 'stage'))}">Preparation stage <span class="required">required</span></label><select id="${attr(studyControlName(id, 'stage'))}" name="${attr(studyControlName(id, 'stage'))}" required><option value="">Choose</option>${optionTags(STUDY_STAGES, pathway.stage || '')}</select></div></div>
      <div class="field"><label for="${attr(studyControlName(id, 'milestone'))}">Milestone date <span class="optional">optional</span></label><input id="${attr(studyControlName(id, 'milestone'))}" type="date" name="${attr(studyControlName(id, 'milestone'))}" value="${attr(pathway.milestoneDate || '')}"><small>Use only a pathway milestone—not a date of birth or patient date.</small></div>
      ${textField(id, 'motivation', 'Motivation', pathway.motivation, 2000)}${textField(id, 'outcome', 'Intended professional outcome', pathway.outcome, 2000)}${textField(id, 'competencies', 'Required competencies and milestones', pathway.requiredCompetencies)}${textField(id, 'progress', 'Evidence of progress', pathway.progressEvidence, 3000, 'Self-reported; do not fabricate scores, hours, or accomplishments.')}${textField(id, 'gaps', 'Knowledge and competency gaps', pathway.gaps)}${textField(id, 'priorities', 'Learning priorities', pathway.priorities)}
      <fieldset><legend>Preferred learning formats</legend>${checklist(studyControlName(id, 'formats'), ['practice questions','concept maps','reading','video','simulation','case discussion','teach-back','coaching','peer learning'], pathway.formats || [])}</fieldset>
      <div class="two-col"><div class="field"><label for="${attr(studyControlName(id, 'time'))}">Available study time</label><input id="${attr(studyControlName(id, 'time'))}" name="${attr(studyControlName(id, 'time'))}" maxlength="300" value="${attr(pathway.availableTime || '')}"></div><div class="field"><label for="${attr(studyControlName(id, 'constraints'))}">Scheduling limitations</label><input id="${attr(studyControlName(id, 'constraints'))}" name="${attr(studyControlName(id, 'constraints'))}" maxlength="1000" value="${attr(pathway.constraints || '')}"></div></div>
      ${textField(id, 'accountability', 'Accountability or coaching needs', pathway.accountability, 1000)}${textField(id, 'mentorship', 'Mentorship requirements', pathway.mentorship, 1000)}${textField(id, 'relationship', 'Relationship to your other roles', pathway.roleRelationship, 2000)}
      <div class="two-col">${textField(id, 'financial', 'Financial barriers', pathway.financialBarriers, 1000)}${textField(id, 'workload', 'Workload barriers', pathway.workloadBarriers, 1000)}${textField(id, 'family', 'Family and personal responsibilities', pathway.familyResponsibilities, 1000)}${textField(id, 'wellness', 'Wellness and burnout considerations', pathway.wellnessConsiderations, 1000)}</div>
      ${textField(id, 'institution', 'Institutional support', pathway.institutionalSupport, 1000)}${textField(id, 'application', 'Safe opportunities to apply new learning', pathway.applicationOpportunities, 2000)}${textField(id, 'renewal', 'Continuing-education and renewal requirements', pathway.renewalRequirements, 1000)}${textField(id, 'integrity', 'Academic-integrity and responsible-AI boundary', pathway.integrityBoundary, 2000, 'AI may tutor and plan; it may not impersonate, fabricate, or complete prohibited work.')}</article>`;
  }).join('');
  const body = `<section class="module-safeguards" aria-label="Advanced Studies safeguards"><h3>Cross-role overlay</h3><ul>${module.safeguards.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section><div class="study-pathway-list">${cards}</div><button class="btn btn-secondary" type="button" data-action="add-study-pathway">Add another pathway</button>`;
  return formShell('Advanced Studies', 'Optional deep dive · about 3–5 minutes per pathway. Complete each pathway independently, or defer the optional detail fields. Study never becomes current authority.', body, { kicker: 'Cross-role growth module', defer: true });
}

function listHtml(items, empty = 'None declared') {
  return items.length ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : `<p class="muted">${escapeHtml(empty)}</p>`;
}

function resultsView() {
  const scored = scoreRoleConstellation(state);
  const dashboards = recommendDashboards(state);
  const agents = recommendAgents(state);
  const roleColumns = ROLE_STATUSES.map((key) => `<section class="result-role-group"><h3>${escapeHtml(key)}</h3>${scored[key].length ? scored[key].map((item) => `<article><strong>${escapeHtml(item.label)}</strong><span>Intensity ${item.intensity}</span><small>Confidence ${item.confidence}/5 · ${escapeHtml(item.authorization)} · ${escapeHtml(item.competenceEvidence)} · ${escapeHtml(item.credentialStatus)} · not verified · no authority granted</small></article>`).join('') : '<p class="muted">None declared</p>'}</section>`).join('');
  const dashboardCards = dashboards.map((item) => `<details class="result-dashboard"><summary><span>${escapeHtml(item.name)}</span><small>${escapeHtml(item.autonomy)}</small></summary><p>${escapeHtml(item.purpose)}</p><dl><dt>Roles supported</dt><dd>${escapeHtml(item.rolesSupported.join(', ') || 'Cross-role')}</dd><dt>Agents</dt><dd>${escapeHtml(item.recommendedAgents.join(', '))}</dd><dt>Core workflows</dt><dd>${escapeHtml(item.coreWorkflows.join('; '))}</dd><dt>Human review</dt><dd>${escapeHtml(item.humanReview.join('; '))}</dd><dt>Data boundaries</dt><dd>${escapeHtml(item.dataBoundaries.join('; '))}</dd><dt>Relationship</dt><dd>${escapeHtml(item.relationships.join('; '))}</dd></dl></details>`).join('');
  const agentCards = agents.map((item) => `<article class="agent-card"><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.humanGate)}</p><small>Activation: ${escapeHtml(item.activation)}</small></article>`).join('');
  const body = `<div class="completion-banner"><span>✓</span><div><strong>One Core SOUL. ${state.roleSelections.length} role${state.roleSelections.length === 1 ? '' : 's'}. ${dashboards.length} coordinated Mission Control${dashboards.length === 1 ? '' : 's'}.</strong><p>Recommendations only—nothing has been activated, connected, remembered outside this tab, sent, scheduled, or published.</p></div></div>
    <section class="result-section"><h2>Your multidimensional role constellation</h2><div class="result-role-grid">${roleColumns}</div></section>
    <div class="two-col"><section class="result-section"><h2>Role synergies</h2>${listHtml(scored.synergies)}</section><section class="result-section warning"><h2>Tensions and overload risks</h2>${listHtml(scored.tensions, 'No rule-based tension was identified. Review capacity with human judgment.')}</section></div>
    <section class="result-section"><h2>Coordinated Mission Controls</h2><div class="shared-foundation"><strong>Shared foundation:</strong> Core SOUL, values, mission, approved memory, governance boundaries, goals, commitments, wellness limits, and learning priorities.<br><strong>Meaning:</strong> “Mission Control” is an organizational view—not a credential, competence finding, approval, command authority, or separate personality.</div>${dashboardCards}</section>
    <section class="result-section"><h2>Recommended AI agents</h2><p>All recommendations are inactive configuration drafts.</p><div class="agent-grid">${agentCards}</div></section>
    <section class="result-section governance-summary"><h2>Governance posture</h2><ul><li>No PHI or patient-specific content.</li><li>Confidence, interest, study, simulation, and self-identification do not verify competence, credentials, or authority.</li><li>Consequential clinical, academic, employment, institutional, legal, and financial decisions remain with accountable humans.</li><li>External actions require confirmation; patient-specific decisions and fabricated claims are never delegated.</li></ul></section>
    <section class="download-panel"><h2>Download your evolving SOUL</h2><p>Keep these files locally. Review before importing. The v2 JSON preserves legacy fields while adding the full role constellation.</p><div class="download-actions"><button class="btn btn-primary" type="button" data-download="bundle">Download full SOUL bundle (.md)</button><button class="btn btn-secondary" type="button" data-download="config">Export OS Config (naio-soul.json)</button></div><div id="document-downloads" class="document-downloads"></div></section>
    <div class="quiz-actions"><button class="btn btn-secondary" type="button" data-nav="back">← Review answers</button><button class="btn btn-quiet" type="button" data-action="restart">Start a new profile</button><a class="btn btn-primary" href="start-here.html">Continue to Start Here →</a></div>`;
  return `<div class="results" id="results-heading" tabindex="-1">${body}</div>`;
}

function currentSteps() {
  return [...CORE_STEP_KEYS, ...recommendedModuleIds(state).map((id) => `module:${id}`), 'review'];
}

function updateProgress() {
  const steps = currentSteps();
  const index = Math.max(0, steps.indexOf(stepKey));
  const percent = Math.round(((index + 1) / steps.length) * 100);
  progress.style.width = `${percent}%`;
  progress.parentElement.setAttribute('aria-valuenow', String(percent));
  progressLabel.textContent = `Step ${index + 1} of ${steps.length} · ${stepKey.startsWith('module:') ? CONDITIONAL_MODULES[stepKey.slice(7)]?.name : STEP_TITLES[stepKey]}`;
}

function render() {
  if (stepKey === 'safety') app.innerHTML = safetyView();
  else if (stepKey === 'roles') app.innerHTML = rolesView();
  else if (stepKey === 'role-details') app.innerHTML = roleDetailsView();
  else if (stepKey === 'core') app.innerHTML = coreView();
  else if (stepKey === 'decisions-ai') app.innerHTML = decisionsAiView();
  else if (stepKey.startsWith('module:')) app.innerHTML = moduleView(stepKey.slice(7));
  else app.innerHTML = resultsView();
  updateProgress();
  bindView();
  requestAnimationFrame(() => app.querySelector('h2,[tabindex="-1"]')?.focus({ preventScroll: true }));
}

function valuesFromForm(form, name) {
  return [...form.querySelectorAll(`input[name="${CSS.escape(name)}"]:checked`)].map((input) => input.value);
}

function collectSafety(form) {
  state.name = form.elements.name.value.trim();
  for (const key of ['noPhi', 'noClinicalAuthority', 'noAcademicDishonesty', 'noCredentialInference']) state.safety[key] = form.elements[`safety-${key}`].checked;
}

function collectRoles(form) {
  const selected = valuesFromForm(form, 'role');
  const customIds = state.customRoles.map((item) => item.id);
  const ids = [...new Set([...selected, ...customIds])];
  state.roleSelections = ids.map((id, index) => selectedRole(state, id) || {
    roleId: id,
    status: index === 0 && !state.roleSelections.some((item) => item.status === 'primary') ? 'primary' : 'supporting',
    attention: 3, responsibility: 3, identity: 3, confidence: 3,
    authorization: 'self-declared', competenceEvidence: 'not-assessed', credentialStatus: 'not-claimed'
  });
  if (!state.roleSelections.some((item) => item.status === 'primary') && state.roleSelections[0]) state.roleSelections[0].status = 'primary';
}

function collectRoleDetails(form) {
  for (const item of state.roleSelections) {
    item.status = form.elements[`${item.roleId}-status`].value;
    item.attention = Number(form.elements[`${item.roleId}-attention`].value);
    item.responsibility = Number(form.elements[`${item.roleId}-responsibility`].value);
    item.identity = Number(form.elements[`${item.roleId}-identity`].value);
    item.confidence = Number(form.elements[`${item.roleId}-confidence`].value);
    item.authorization = form.elements[`${item.roleId}-authorization`].value;
    item.competenceEvidence = form.elements[`${item.roleId}-competence`].value;
    item.credentialStatus = form.elements[`${item.roleId}-credential`].value;
  }
}

function collectCore(form) {
  state.developmentalStages = valuesFromForm(form, 'development');
  state.spheres = valuesFromForm(form, 'spheres');
  state.advancedStudies.active = form.elements['advanced-active'].checked;
  if (state.advancedStudies.active) {
    state.advancedStudies.pathways = [...form.querySelectorAll('[data-study-pathway-quick]')].slice(0, 8).map((card, index) => {
      const id = card.dataset.studyPathwayQuick;
      const prior = state.advancedStudies.pathways.find((item, itemIndex) => pathwayId(item, itemIndex) === id) || {};
      return { ...prior, id, type: form.elements[studyControlName(id, 'type')].value, target: form.elements[studyControlName(id, 'target')].value.trim(), stage: form.elements[studyControlName(id, 'stage')].value, formats: prior.formats || [], verification: 'self-reported-not-verified', authority_granted: false };
    });
  } else state.advancedStudies.pathways = [];
  const customValues = splitList(form.elements['custom-values'].value);
  state.core.values = [...new Set([...valuesFromForm(form, 'values'), ...customValues])].slice(0, 24);
  state.core.customValues = form.elements['custom-values'].value.trim();
  state.core.mission = form.elements.mission.value.trim();
  state.core.populations = form.elements.populations.value.trim();
  state.core.sharedGoals = form.elements['shared-goals'].value.trim();
  state.core.commitmentBoundaries = form.elements['commitment-boundaries'].value.trim();
  state.core.motivations = valuesFromForm(form, 'motivations');
  state.core.strengths = form.elements.strengths.value.trim();
  state.core.workStyles = valuesFromForm(form, 'work-styles');
  state.core.learningStyles = valuesFromForm(form, 'learning-styles');
  state.core.voice = { length: form.elements['voice-length'].value, formality: form.elements['voice-formality'].value, pushback: form.elements['voice-pushback'].value.trim(), avoid: form.elements['voice-avoid'].value.trim() };
  state.core.alwaysRemember = form.elements['always-remember'].value.trim();
}

function collectDecisionsAi(form) {
  for (const key of Object.keys(DECISION_LABELS)) state.decisionStyle[key] = Number(form.elements[`decision-${key}`].value);
  state.pressures.selected = valuesFromForm(form, 'pressures');
  state.pressures.load = Number(form.elements['pressure-load'].value);
  state.pressures.wellnessLimit = form.elements['wellness-limit'].value.trim();
  state.ai.relationshipModes = valuesFromForm(form, 'ai-modes');
  const requestedPrimaryMode = form.elements['primary-ai-mode'].value;
  state.ai.primaryMode = state.ai.relationshipModes.includes(requestedPrimaryMode) ? requestedPrimaryMode : (state.ai.relationshipModes[0] || '');
  for (const activity of DELEGATION_ACTIVITIES) state.ai.delegation[activity.id] = applyGovernanceFloor(activity.id, form.elements[`delegation-${activity.id}`].value);
  state.ai.memoryAllowed = splitList(form.elements['memory-allowed'].value, 200);
  state.ai.memoryForbidden = splitList(form.elements['memory-forbidden'].value, 200);
  state.ai.escalationTriggers = splitList(form.elements['escalation-triggers'].value, 300);
}

function collectModule(form, moduleId) {
  if (moduleId === 'advanced-studies') return collectAdvancedStudies(form);
  const ids = new Set(state.roleSelections.map((item) => item.roleId));
  const derivedCombination = ids.has('prelicensure-nursing-student') && ids.has('nursing-assistant-pct')
    ? 'both-distinct-contexts'
    : ids.has('prelicensure-nursing-student') ? 'student-only' : 'nursing-assistant-only';
  state.moduleAnswers[moduleId] = Object.fromEntries(CONDITIONAL_MODULES[moduleId].questions.map((question) => [question.id, question.id === 'studentAssistantCombination' ? derivedCombination : form.elements[`module-${question.id}`].value.trim()]));
}

function collectAdvancedStudies(form) {
  const value = (id, key) => form.elements[studyControlName(id, key)].value.trim();
  state.advancedStudies.pathways = [...form.querySelectorAll('[data-study-pathway-editor]')].slice(0, 8).map((card, index) => {
    const id = card.dataset.studyPathwayEditor;
    const prior = state.advancedStudies.pathways.find((item, itemIndex) => pathwayId(item, itemIndex) === id) || {};
    return { ...prior, id, type: value(id, 'type'), target: value(id, 'target'), stage: value(id, 'stage'), milestoneDate: value(id, 'milestone'), motivation: value(id, 'motivation'), outcome: value(id, 'outcome'), requiredCompetencies: value(id, 'competencies'), progressEvidence: value(id, 'progress'), gaps: value(id, 'gaps'), priorities: value(id, 'priorities'), formats: valuesFromForm(form, studyControlName(id, 'formats')), availableTime: value(id, 'time'), constraints: value(id, 'constraints'), accountability: value(id, 'accountability'), mentorship: value(id, 'mentorship'), roleRelationship: value(id, 'relationship'), financialBarriers: value(id, 'financial'), workloadBarriers: value(id, 'workload'), familyResponsibilities: value(id, 'family'), wellnessConsiderations: value(id, 'wellness'), institutionalSupport: value(id, 'institution'), applicationOpportunities: value(id, 'application'), renewalRequirements: value(id, 'renewal'), integrityBoundary: value(id, 'integrity'), verification: 'self-reported-not-verified', authority_granted: false };
  });
}

function collectCurrent() {
  const form = document.getElementById('quiz-form');
  if (!form) return;
  if (stepKey === 'safety') collectSafety(form);
  else if (stepKey === 'roles') collectRoles(form);
  else if (stepKey === 'role-details') collectRoleDetails(form);
  else if (stepKey === 'core') collectCore(form);
  else if (stepKey === 'decisions-ai') collectDecisionsAi(form);
  else if (stepKey.startsWith('module:')) collectModule(form, stepKey.slice(7));
}

function showError(message) {
  const element = document.getElementById('step-error');
  if (!element) return;
  element.textContent = message;
  element.hidden = false;
  element.focus();
  announce(message, true);
}

function validateCurrent(form) {
  if (!form.reportValidity()) return false;
  if (stepKey === 'safety') {
    if (!state.name) return showError('Enter the name Nurse AI OS should use.'), false;
    if (!Object.values(state.safety).every(Boolean)) return showError('Confirm all four stewardship boundaries before continuing.'), false;
  }
  if (stepKey === 'roles' && state.roleSelections.length < 1) return showError('Select at least one role.'), false;
  if (stepKey === 'role-details') {
    if (state.roleSelections.filter((item) => item.status === 'primary').length !== 1) return showError('Choose exactly one primary role. Other roles may be supporting, emerging, or contextual.'), false;
    const contradiction = state.roleSelections.find((item) => ['primary', 'supporting'].includes(item.status) && item.authorization === 'not-current');
    if (contradiction) return showError('A primary or supporting role cannot be marked “Not a current assignment.” Change its role status to emerging/contextual or update its authorization posture.'), false;
  }
  if (stepKey === 'core') {
    if (!state.spheres.length) return showError('Choose at least one Mission Control environment.'), false;
    if (state.core.values.length < 3) return showError('Choose at least three core values.'), false;
    if (!state.core.mission) return showError('Describe your mission or purpose in broad, non-identifying terms.'), false;
    if (state.advancedStudies.active && (!state.advancedStudies.pathways.length || state.advancedStudies.pathways.some((item) => !item.type || !item.target || !item.stage))) return showError('Complete the type, target, and stage for every Advanced Studies pathway, or turn the overlay off for now.'), false;
  }
  if (stepKey === 'decisions-ai') {
    if (!state.ai.relationshipModes.length || !state.ai.primaryMode) return showError('Choose at least one AI relationship and one primary mode.'), false;
    if (!state.ai.relationshipModes.includes(state.ai.primaryMode)) return showError('Choose a primary AI mode from the modes you selected.'), false;
  }
  return true;
}

function nextStep() {
  const steps = currentSteps();
  const index = steps.indexOf(stepKey);
  stepKey = steps[Math.min(index + 1, steps.length - 1)];
  render();
  window.scrollTo({ top: document.querySelector('.quiz-shell').offsetTop - 80, behavior: 'smooth' });
}

function previousStep() {
  const steps = currentSteps();
  const index = steps.indexOf(stepKey);
  stepKey = steps[Math.max(0, index - 1)];
  render();
  window.scrollTo({ top: document.querySelector('.quiz-shell').offsetTop - 80, behavior: 'smooth' });
}

function downloadFile(name, content, type = 'text/markdown;charset=utf-8') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function handleDownload(kind) {
  const generatedAt = new Date().toISOString();
  const docs = buildSoulDocuments(state, generatedAt);
  if (kind === 'bundle') {
    const content = docs.map((item) => `<!-- ${item.path} -->\n\n${item.content.trim()}\n`).join('\n\n---\n\n');
    downloadFile('Nurse-AI-OS-SOUL-Bundle.md', content);
  } else if (kind === 'config') downloadFile('naio-soul.json', `${JSON.stringify(buildOsConfig(state, generatedAt), null, 2)}\n`, 'application/json;charset=utf-8');
  else {
    const doc = docs.find((item) => item.name === kind);
    if (doc) downloadFile(doc.name, doc.content);
  }
  announce('Download prepared locally. Review it before importing or sharing.');
}

function bindView() {
  const form = document.getElementById('quiz-form');
  form?.addEventListener('submit', (event) => {
    event.preventDefault();
    collectCurrent();
    if (!validateCurrent(form)) return;
    saveState();
    nextStep();
  });
  app.querySelectorAll('[data-nav="back"]').forEach((button) => button.addEventListener('click', () => { collectCurrent(); saveState(); previousStep(); }));
  app.querySelector('[data-action="save"]')?.addEventListener('click', () => { collectCurrent(); saveState(); });
  app.querySelector('[data-action="add-custom-role"]')?.addEventListener('click', () => {
    try {
      collectRoles(form);
      addCustomRole(state, document.getElementById('custom-title').value, document.getElementById('custom-domain').value, document.getElementById('custom-status').value);
      saveState('Local draft role added. It remains unreviewed and grants no authority.');
      render();
    } catch (error) { showError(error.message); }
  });
  app.querySelectorAll('[data-action="remove-custom-role"]').forEach((button) => button.addEventListener('click', () => {
    try {
      collectRoles(form);
      removeCustomRole(state, button.dataset.roleId);
      saveState('Local draft role removed. Other role selections were preserved.');
      render();
    } catch (error) { showError(error.message); }
  }));
  app.querySelector('[data-action="add-study-pathway"]')?.addEventListener('click', () => {
    if (stepKey === 'core') form.elements['advanced-active'].checked = true;
    collectCurrent();
    state.advancedStudies.active = true;
    if (state.advancedStudies.pathways.length < 8) state.advancedStudies.pathways.push(newStudyPathway());
    saveState('Advanced Studies pathway added. Complete it independently; no credential or authority is inferred.');
    render();
  });
  app.querySelectorAll('[data-action="remove-study-pathway"]').forEach((button) => button.addEventListener('click', () => {
    collectCurrent();
    state.advancedStudies.pathways = state.advancedStudies.pathways.filter((item, index) => pathwayId(item, index) !== button.dataset.pathwayId);
    if (!state.advancedStudies.pathways.length) {
      state.advancedStudies.active = false;
      if (stepKey === 'module:advanced-studies') stepKey = 'core';
    }
    saveState('Advanced Studies pathway removed. Other pathways and role information were preserved.');
    render();
  }));
  app.querySelector('#role-filter')?.addEventListener('input', (event) => {
    const query = event.target.value.trim().toLowerCase();
    app.querySelectorAll('.role-option').forEach((item) => { item.hidden = Boolean(query) && !item.dataset.search.includes(query); });
    app.querySelectorAll('.role-domain').forEach((domain) => { if (query) domain.open = Boolean(domain.querySelector('.role-option:not([hidden])')); });
  });
  const primaryMode = app.querySelector('#primary-ai-mode');
  const relationshipModes = [...app.querySelectorAll('input[name="ai-modes"]')];
  primaryMode?.addEventListener('change', () => {
    const matchingMode = relationshipModes.find((input) => input.value === primaryMode.value);
    if (matchingMode) matchingMode.checked = true;
    else primaryMode.value = relationshipModes.find((input) => input.checked)?.value || '';
  });
  relationshipModes.forEach((input) => input.addEventListener('change', () => {
    if (input.checked && primaryMode && !primaryMode.value) primaryMode.value = input.value;
    else if (!input.checked && primaryMode?.value === input.value) primaryMode.value = relationshipModes.find((mode) => mode.checked)?.value || '';
  }));
  app.querySelectorAll('[data-download]').forEach((button) => button.addEventListener('click', () => handleDownload(button.dataset.download)));
  app.querySelector('[data-action="restart"]')?.addEventListener('click', resetQuiz);
  const docs = document.getElementById('document-downloads');
  if (docs) docs.innerHTML = buildSoulDocuments(state).map((item) => `<button class="text-button" type="button" data-download="${attr(item.name)}">${escapeHtml(item.name)}</button>`).join('');
  docs?.querySelectorAll('[data-download]').forEach((button) => button.addEventListener('click', () => handleDownload(button.dataset.download)));
}

function resetQuiz() {
  if (!window.confirm('Clear this tab’s SOUL Quiz draft and start again? Downloaded files will not be removed.')) return;
  sessionStorage.removeItem(STORAGE_KEY);
  state = createInitialState();
  stepKey = 'safety';
  announce('This tab’s draft was cleared.');
  render();
}

resetButton.addEventListener('click', resetQuiz);
render();
