import { createStoredZip } from './zip-store.mjs';

export const SCHEMA_VERSION = '1.0.0';
export const STORAGE_KEY = 'naio.technical-ally-soul-quiz.v1';
export const PACKAGE_FILENAME = 'Nurse-AI-OS-Technical-Ally-Manager-Collaboration-Dashboard.zip';
export const PROFILE_SCHEMA_URL = 'https://nurse-ai-os.org/technical-ally-soul-quiz/technical-ally-soul-profile.schema.json';

export const TECHNICAL_BACKGROUNDS = Object.freeze([
  { id: 'software-engineering', label: 'Software engineering or application development' },
  { id: 'data-ai', label: 'Data, machine learning, or AI engineering' },
  { id: 'cybersecurity-privacy', label: 'Cybersecurity, privacy, identity, or compliance engineering' },
  { id: 'infrastructure-reliability', label: 'Cloud, local infrastructure, DevOps, or reliability' },
  { id: 'automation-integrations', label: 'Automation, APIs, integrations, or agent systems' },
  { id: 'product-ux-accessibility', label: 'Product, UX, human factors, or accessibility' },
  { id: 'analytics-evaluation', label: 'Analytics, testing, measurement, or evaluation' },
  { id: 'technical-business', label: 'Technical entrepreneurship, consulting, or business operations' }
]);

export const COLLABORATION_AREAS = Object.freeze([
  { id: 'workflow-mapping', label: 'Map an existing manager workflow before proposing technology' },
  { id: 'prototype-building', label: 'Build bounded, reversible prototypes' },
  { id: 'source-provenance', label: 'Connect approved sources and preserve provenance' },
  { id: 'model-evaluation', label: 'Evaluate models and routing against a fixed workflow' },
  { id: 'security-boundaries', label: 'Define permissions, privacy, security, and stop conditions' },
  { id: 'reliability-operations', label: 'Test reliability, monitoring, fallback, and rollback' },
  { id: 'product-experience', label: 'Improve usability, accessibility, and human review' },
  { id: 'business-validation', label: 'Validate an offer, buyer, outcome, and sustainable business model' },
  { id: 'training-facilitation', label: 'Teach technical concepts while preserving nurse leadership' }
]);

export const MANAGER_NEEDS = Object.freeze([
  { id: 'meeting-action', label: 'Turn meeting notes into accountable actions' },
  { id: 'evidence-brief', label: 'Turn approved sources into a review-ready brief' },
  { id: 'workflow-spec', label: 'Convert a recurring burden into a testable workflow specification' },
  { id: 'ai-governance', label: 'Prepare an AI governance or readiness packet' },
  { id: 'evaluation', label: 'Evaluate an AI workflow for quality, burden, risk, and adoption' },
  { id: 'implementation-plan', label: 'Prepare a phased implementation and change plan' },
  { id: 'technical-literacy', label: 'Build technical understanding without displacing nursing judgment' }
]);

export const RELATIONSHIPS = Object.freeze([
  { id: 'invited-by-nurse', label: 'A nurse or nurse manager invited me to help' },
  { id: 'existing-partner', label: 'I already collaborate with nurses or nursing organizations' },
  { id: 'independent-builder', label: 'I am independently exploring a nurse-supporting product or service' },
  { id: 'technical-team-member', label: 'I work on a technical, innovation, or operational team serving healthcare' },
  { id: 'learning-first', label: 'I am learning and do not yet have a nurse partner' }
]);

export const BUSINESS_STAGES = Object.freeze([
  { id: 'not-building', label: 'Not currently building a business' },
  { id: 'exploring', label: 'Exploring a possible business or independent practice' },
  { id: 'customer-discovery', label: 'Conducting customer and problem discovery' },
  { id: 'prototype', label: 'Building or testing a prototype' },
  { id: 'repeat-use', label: 'Observed repeat use, but no established revenue yet' },
  { id: 'paid', label: 'At least one real customer has paid' }
]);

export const BUSINESS_MODELS = Object.freeze([
  { id: 'not-sure-or-not-building', label: 'Not sure yet or not currently building' },
  { id: 'professional-service', label: 'Governed technical service, consulting, or implementation sprint' },
  { id: 'workflow-product', label: 'Reusable workflow product or browser-local tool' },
  { id: 'infrastructure-security', label: 'Infrastructure, privacy, security, reliability, or model-evaluation service' },
  { id: 'education-facilitation', label: 'Technical education or facilitation with nurse-led content review' },
  { id: 'open-source-support', label: 'Open-source support, hosting, integration, or maintenance business' }
]);

export const FIRST_OUTCOMES = Object.freeze([
  { id: 'meeting-to-action', label: 'Meeting-to-Accountable-Action brief' },
  { id: 'evidence-to-brief', label: 'Governed Evidence-to-Brief comparison' },
  { id: 'workflow-map', label: 'Current-state workflow and burden map' },
  { id: 'model-evaluation', label: 'Local-versus-frontier model evaluation' },
  { id: 'permission-boundary', label: 'Data, permission, and stop-condition map' },
  { id: 'prototype-review', label: 'Usability and accessibility prototype review' },
  { id: 'venture-offer', label: 'One-page nurse-supporting venture offer and validation plan' }
]);

export const REVIEW_CADENCES = Object.freeze([
  { id: 'weekly', label: 'Weekly review with the nurse manager or designated nurse steward' },
  { id: 'biweekly', label: 'Review every two weeks' },
  { id: 'milestone', label: 'Review at each named milestone before work continues' }
]);

export const STOP_CONDITIONS = Object.freeze([
  { id: 'phi-sensitive-data', label: 'PHI, patient information, personnel records, credentials, or secrets appear' },
  { id: 'authority-expansion', label: 'The work could create clinical, staffing, employment, compliance, procurement, or institutional authority' },
  { id: 'nurse-disagreement', label: 'The nurse manager or nurse steward disagrees with the problem framing or proposed workflow' },
  { id: 'unexpected-permission', label: 'A tool, model, or connector requests unexpected access' },
  { id: 'source-failure', label: 'A source is missing, expired, unauthorized, or contradictory' },
  { id: 'unsafe-unreliable', label: 'Testing finds unsafe, unreliable, inaccessible, or unreviewable behavior' },
  { id: 'uncompensated-extraction', label: 'Nurse or community knowledge would be commercialized without agreed attribution, participation, or compensation' }
]);

export const ARCHETYPES = Object.freeze([
  {
    id: 'workflow-engineer',
    label: 'Nurse-Supporting Workflow Engineer',
    promise: 'Translate one manager-owned burden into bounded, testable steps without taking over the nursing decision.',
    backgrounds: ['software-engineering', 'automation-integrations'],
    contributions: ['workflow-mapping', 'prototype-building'],
    firstMove: 'Map one recurring manager workflow and build only the smallest reversible preparation step.'
  },
  {
    id: 'model-evidence-evaluator',
    label: 'Model and Evidence Evaluator',
    promise: 'Compare models, sources, and outputs against a fixed professional acceptance contract.',
    backgrounds: ['data-ai', 'analytics-evaluation'],
    contributions: ['source-provenance', 'model-evaluation'],
    firstMove: 'Run one source-linked local-versus-frontier comparison in shadow mode.'
  },
  {
    id: 'security-reliability-steward',
    label: 'Security and Reliability Steward',
    promise: 'Make permissions, failure paths, monitoring, and shutdown conditions visible before capability expands.',
    backgrounds: ['cybersecurity-privacy', 'infrastructure-reliability'],
    contributions: ['security-boundaries', 'reliability-operations'],
    firstMove: 'Create one permission, data-flow, fallback, and stop-condition map for a bounded workflow.'
  },
  {
    id: 'product-experience-builder',
    label: 'Product and Human-Experience Builder',
    promise: 'Help nurse managers and frontline reviewers understand, correct, contest, and safely use technical systems.',
    backgrounds: ['product-ux-accessibility'],
    contributions: ['product-experience', 'training-facilitation'],
    firstMove: 'Observe one nurse-manager task and produce an accessibility and cognitive-burden review before adding features.'
  },
  {
    id: 'technical-founder-operator',
    label: 'Nurse-Aligned Technical Founder–Operator',
    promise: 'Build a viable business around a nurse-defined outcome while preserving nursing leadership, evidence, and rights.',
    backgrounds: ['technical-business'],
    contributions: ['business-validation', 'training-facilitation'],
    firstMove: 'Interview nurses about one costly recurring problem and test a bounded offer before building a platform.'
  }
]);

const SAFE_TEXT_LIMITS = Object.freeze({
  displayName: 80,
  outcomeDetail: 500,
  allyResponsibility: 500,
  nurseDecisionRights: 500,
  successSignal: 360,
  businessBoundary: 500
});

function cleanText(value, limit) {
  return String(value ?? '').replace(/\s+/g, ' ').trim().slice(0, limit);
}

function cleanList(value, allowed, limit = 12) {
  const allow = new Set(allowed);
  return [...new Set(Array.isArray(value) ? value : [])].filter((item) => allow.has(item)).slice(0, limit);
}

function allowedId(value, catalog, fallback = '') {
  const id = String(value || '');
  return catalog.some((item) => item.id === id) ? id : fallback;
}

export function containsRestrictedText(value) {
  const text = String(value || '');
  const patterns = [
    /<\/?[a-z][^>]*>/i,
    /\b(?:MRN|medical record|DOB|date of birth|SSN|social security|employee\s*(?:id|number)|student\s*(?:id|number)|API\s*key|password|access\s*token|secret)\b/i,
    /\b(?:patient|employee|student)\s*(?:name\s*)?(?:[:#=-]\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b/i,
    /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i,
    /(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}/,
    /\b\d{3}-\d{2}-\d{4}\b/
  ];
  return patterns.some((pattern) => pattern.test(text));
}

export function createInitialState(now = new Date().toISOString()) {
  return {
    schemaVersion: SCHEMA_VERSION,
    updatedAt: now,
    step: 0,
    safety: {
      noPhi: false,
      noNursingAuthority: false,
      nursesDecide: false,
      noInstitutionalAuthority: false,
      noUnapprovedAction: false
    },
    identity: {
      displayName: '',
      backgrounds: [],
      experience: '',
      relationship: ''
    },
    collaboration: {
      contributionAreas: [],
      managerNeeds: [],
      firstOutcome: '',
      outcomeDetail: '',
      allyResponsibility: '',
      nurseDecisionRights: '',
      reviewCadence: '',
      successSignal: '',
      stopConditions: []
    },
    venture: {
      businessStage: '',
      businessModel: '',
      businessBoundary: '',
      nurseParticipation: false,
      attributionCompensation: false,
      evidenceBeforeClaims: false,
      conflictDisclosure: false
    }
  };
}

export function normalizeState(candidate) {
  if (!candidate || typeof candidate !== 'object' || candidate.schemaVersion !== SCHEMA_VERSION) return null;
  const base = createInitialState(typeof candidate.updatedAt === 'string' ? candidate.updatedAt : new Date().toISOString());
  const safety = candidate.safety && typeof candidate.safety === 'object' ? candidate.safety : {};
  for (const key of Object.keys(base.safety)) base.safety[key] = safety[key] === true;
  const identity = candidate.identity && typeof candidate.identity === 'object' ? candidate.identity : {};
  base.identity.displayName = cleanText(identity.displayName, SAFE_TEXT_LIMITS.displayName);
  base.identity.backgrounds = cleanList(identity.backgrounds, TECHNICAL_BACKGROUNDS.map((item) => item.id));
  base.identity.experience = ['learning', 'practitioner', 'senior', 'founder'].includes(identity.experience) ? identity.experience : '';
  base.identity.relationship = allowedId(identity.relationship, RELATIONSHIPS);
  const collaboration = candidate.collaboration && typeof candidate.collaboration === 'object' ? candidate.collaboration : {};
  base.collaboration.contributionAreas = cleanList(collaboration.contributionAreas, COLLABORATION_AREAS.map((item) => item.id));
  base.collaboration.managerNeeds = cleanList(collaboration.managerNeeds, MANAGER_NEEDS.map((item) => item.id));
  base.collaboration.firstOutcome = allowedId(collaboration.firstOutcome, FIRST_OUTCOMES);
  for (const key of ['outcomeDetail', 'allyResponsibility', 'nurseDecisionRights', 'successSignal']) base.collaboration[key] = cleanText(collaboration[key], SAFE_TEXT_LIMITS[key]);
  base.collaboration.reviewCadence = allowedId(collaboration.reviewCadence, REVIEW_CADENCES);
  base.collaboration.stopConditions = cleanList(collaboration.stopConditions, STOP_CONDITIONS.map((item) => item.id));
  const venture = candidate.venture && typeof candidate.venture === 'object' ? candidate.venture : {};
  base.venture.businessStage = allowedId(venture.businessStage, BUSINESS_STAGES);
  base.venture.businessModel = allowedId(venture.businessModel, BUSINESS_MODELS);
  base.venture.businessBoundary = cleanText(venture.businessBoundary, SAFE_TEXT_LIMITS.businessBoundary);
  for (const key of ['nurseParticipation', 'attributionCompensation', 'evidenceBeforeClaims', 'conflictDisclosure']) base.venture[key] = venture[key] === true;
  const requestedStep = Number.isInteger(candidate.step) ? Math.max(0, Math.min(5, candidate.step)) : 0;
  base.step = 0;
  const freeText = [base.identity.displayName, base.collaboration.outcomeDetail, base.collaboration.allyResponsibility, base.collaboration.nurseDecisionRights, base.collaboration.successSignal, base.venture.businessBoundary];
  if (freeText.some(containsRestrictedText)) return null;
  while (base.step < requestedStep && base.step < 5 && !validateStep(base, base.step)) base.step += 1;
  return base;
}

export function validateStep(state, step) {
  if (!state) return 'The quiz state is unavailable. Reset and begin again.';
  if (step === 0) {
    if (!state.identity.displayName) return 'Enter a first name, nickname, initials, or project alias.';
    if (containsRestrictedText(state.identity.displayName)) return 'Use a generic display name without identifiers, contact information, markup, or secrets.';
    if (!Object.values(state.safety).every(Boolean)) return 'Confirm every stewardship boundary before continuing.';
  }
  if (step === 1) {
    if (!state.identity.backgrounds.length) return 'Choose at least one technical background.';
    if (!state.identity.experience) return 'Choose your current technical experience level.';
    if (!state.identity.relationship) return 'Choose your current relationship to nurse-led work.';
  }
  if (step === 2) {
    if (!state.collaboration.contributionAreas.length) return 'Choose at least one contribution area.';
    if (!state.collaboration.managerNeeds.length) return 'Choose at least one nurse-manager need you want to understand.';
  }
  if (step === 3) {
    if (!state.venture.businessStage) return 'Choose your current business or venture stage.';
    if (!state.venture.businessModel) return 'Choose the business path you are exploring, including “not sure yet.”';
    if (![state.venture.nurseParticipation, state.venture.attributionCompensation, state.venture.evidenceBeforeClaims, state.venture.conflictDisclosure].every(Boolean)) return 'Confirm all four venture-stewardship commitments.';
    if (containsRestrictedText(state.venture.businessBoundary)) return 'Remove identifiers, contact information, markup, credentials, or secrets from the business boundary.';
  }
  if (step === 4) {
    if (!state.collaboration.firstOutcome) return 'Choose one bounded first outcome.';
    if (!state.collaboration.reviewCadence) return 'Choose a human review cadence.';
    if (state.collaboration.stopConditions.length < 3) return 'Choose at least three stop conditions.';
    for (const key of ['outcomeDetail', 'allyResponsibility', 'nurseDecisionRights', 'successSignal']) {
      if (!state.collaboration[key]) return 'Complete the bounded collaboration contract using broad, non-identifying language.';
      if (containsRestrictedText(state.collaboration[key])) return 'Remove identifiers, contact information, markup, credentials, or secrets from the collaboration contract.';
    }
  }
  return '';
}

function labelFor(catalog, id) {
  return catalog.find((item) => item.id === id)?.label || id;
}

function labelsFor(catalog, ids) {
  return ids.map((id) => labelFor(catalog, id));
}

export function deriveResult(state) {
  const scores = ARCHETYPES.map((archetype, index) => {
    let score = 0;
    for (const id of state.identity.backgrounds) if (archetype.backgrounds.includes(id)) score += 3;
    for (const id of state.collaboration.contributionAreas) if (archetype.contributions.includes(id)) score += 2;
    if (archetype.id === 'technical-founder-operator' && state.venture.businessStage !== 'not-building') score += 2;
    return { ...archetype, score, index };
  }).sort((a, b) => b.score - a.score || a.index - b.index);
  return {
    primary: scores[0],
    supporting: scores.slice(1).filter((item) => item.score > 0).slice(0, 2),
    firstOutcome: labelFor(FIRST_OUTCOMES, state.collaboration.firstOutcome),
    reviewCadence: labelFor(REVIEW_CADENCES, state.collaboration.reviewCadence),
    stopConditions: labelsFor(STOP_CONDITIONS, state.collaboration.stopConditions),
    backgrounds: labelsFor(TECHNICAL_BACKGROUNDS, state.identity.backgrounds),
    contributions: labelsFor(COLLABORATION_AREAS, state.collaboration.contributionAreas),
    managerNeeds: labelsFor(MANAGER_NEEDS, state.collaboration.managerNeeds),
    businessStage: labelFor(BUSINESS_STAGES, state.venture.businessStage),
    businessModel: labelFor(BUSINESS_MODELS, state.venture.businessModel)
  };
}

export function buildProfile(state, generatedAt = new Date().toISOString()) {
  const normalized = normalizeState({ ...state, updatedAt: generatedAt, step: 5 });
  if (!normalized) throw new Error('Profile state is invalid.');
  for (let step = 0; step <= 4; step += 1) {
    const error = validateStep(normalized, step);
    if (error) throw new Error(error);
  }
  const result = deriveResult(normalized);
  const profile = {
    schema_version: SCHEMA_VERSION,
    schema_url: PROFILE_SCHEMA_URL,
    profile_type: 'nurse-connected-technical-ally',
    generated_at: generatedAt,
    self_reported: true,
    import_authorized: false,
    stewardship_confirmations: normalized.safety,
    identity: normalized.identity,
    collaboration: normalized.collaboration,
    venture: normalized.venture,
    result: {
      primary_orientation: result.primary.id,
      primary_label: result.primary.label,
      supporting_orientations: result.supporting.map((item) => item.id),
      first_outcome: normalized.collaboration.firstOutcome,
      first_move: result.primary.firstMove
    },
    authority: {
      nursing_identity_verified: false,
      nursing_authority_granted: false,
      clinical_authority_granted: false,
      managerial_authority_granted: false,
      institutional_authority_granted: false,
      deployment_authority_granted: false
    },
    governance_posture: {
      edena: 'not-evaluated',
      autonomy: 'A0-no-action',
      execution: 'draft-only',
      connectors: 'off',
      external_actions: 'off',
      persistent_memory: 'off',
      data: 'no-PHI; no patient, learner, workforce, credential, secret, or restricted institutional records'
    }
  };
  const semantic = validateProfileSemantics(profile);
  if (!semantic.valid) throw new Error(`Generated profile failed semantic validation: ${semantic.errors.join('; ')}`);
  return profile;
}

export function validateProfileSemantics(profile) {
  const errors = [];
  if (!profile || typeof profile !== 'object') return { valid: false, errors: ['Profile must be an object.'] };
  if (profile.self_reported !== true || profile.import_authorized !== false) errors.push('Profile must remain self-reported and not import-authorized.');
  const reconstructed = normalizeState({
    schemaVersion: profile.schema_version,
    updatedAt: profile.generated_at,
    step: 5,
    safety: profile.stewardship_confirmations,
    identity: profile.identity,
    collaboration: profile.collaboration,
    venture: profile.venture
  });
  if (!reconstructed || reconstructed.step !== 5) errors.push('Profile answers do not satisfy every quiz gate.');
  if (reconstructed) {
    const expected = deriveResult(reconstructed);
    if (profile.result?.primary_orientation !== expected.primary.id) errors.push('Primary orientation does not match the answers.');
    if (profile.result?.primary_label !== expected.primary.label) errors.push('Primary label does not match the orientation.');
    if (JSON.stringify(profile.result?.supporting_orientations || []) !== JSON.stringify(expected.supporting.map((item) => item.id))) errors.push('Supporting orientations do not match the answers.');
    if (profile.result?.first_outcome !== reconstructed.collaboration.firstOutcome) errors.push('First outcome does not match the collaboration contract.');
    if (profile.result?.first_move !== expected.primary.firstMove) errors.push('First move does not match the primary orientation.');
  }
  const authority = profile.authority && typeof profile.authority === 'object' ? profile.authority : {};
  if (Object.keys(authority).length !== 6 || Object.values(authority).some((value) => value !== false)) errors.push('Authority flags must all be explicitly false.');
  const posture = profile.governance_posture || {};
  const requiredPosture = { edena: 'not-evaluated', autonomy: 'A0-no-action', execution: 'draft-only', connectors: 'off', external_actions: 'off', persistent_memory: 'off', data: 'no-PHI; no patient, learner, workforce, credential, secret, or restricted institutional records' };
  for (const [key, value] of Object.entries(requiredPosture)) if (posture[key] !== value) errors.push(`Governance posture mismatch: ${key}.`);
  return { valid: errors.length === 0, errors };
}

function markdownList(items) {
  return items.map((item) => `- ${item}`).join('\n');
}

export function buildSoulMarkdown(state, generatedAt = new Date().toISOString()) {
  const profile = buildProfile(state, generatedAt);
  const result = deriveResult(profile);
  const supporting = result.supporting.map((item) => item.label);
  return `# Technical Ally SOUL — ${profile.identity.displayName}\n\n` +
    `Generated: ${generatedAt}\n\n` +
    `## Identity and posture\n\n` +
    `I am a non-nurse technical ally. This profile is self-reported and verifies no credential, competence, appointment, assignment, nursing identity, managerial authority, institutional permission, or deployment authority.\n\n` +
    `**Primary working orientation:** ${result.primary.label}\n\n` +
    `**Supporting orientations:** ${supporting.join(', ') || 'None selected'}\n\n` +
    `**Current relationship to nurse-led work:** ${labelFor(RELATIONSHIPS, profile.identity.relationship)}\n\n` +
    `## Technical background\n\n${markdownList(result.backgrounds)}\n\n` +
    `## Contributions I can offer\n\n${markdownList(result.contributions)}\n\n` +
    `## Nurse-manager problems I want to understand\n\n${markdownList(result.managerNeeds)}\n\n` +
    `## First bounded collaboration\n\n` +
    `**Outcome:** ${result.firstOutcome}\n\n` +
    `**Broad detail:** ${profile.collaboration.outcomeDetail}\n\n` +
    `**What I own:** ${profile.collaboration.allyResponsibility}\n\n` +
    `**What the nurse manager or authorized nurse decides:** ${profile.collaboration.nurseDecisionRights}\n\n` +
    `**Success signal:** ${profile.collaboration.successSignal}\n\n` +
    `**Review cadence:** ${result.reviewCadence}\n\n` +
    `## Stop conditions\n\n${markdownList(result.stopConditions)}\n\n` +
    `## Venture stewardship\n\n` +
    `**Current stage:** ${result.businessStage}\n\n` +
    `**Business path:** ${result.businessModel}\n\n` +
    `**Business boundary:** ${profile.venture.businessBoundary || 'No additional boundary supplied.'}\n\n` +
    `- Nurses participate in defining nursing problems and judging nursing impact.\n` +
    `- Attribution, participation, and compensation are agreed before nurse or community knowledge is commercialized.\n` +
    `- Claims follow evidence; no customer, revenue, validation, clinical readiness, or endorsement is fabricated.\n` +
    `- Conflicts, incentives, sponsorship, and commercial interests are disclosed.\n\n` +
    `## Governance posture\n\n` +
    `EDENA: Not evaluated · A0/no action · Draft only · Connectors off · External actions off · Persistent memory off.\n\n` +
    `No PHI. No patient-specific work. No workforce or learner records. No clinical, staffing, employment, procurement, compliance, financial, legal, or institutional decisions.\n\n` +
    `> Agents propose. Humans judge. Nurses steward.\n`;
}

export function buildCharter(state, generatedAt = new Date().toISOString()) {
  const profile = buildProfile(state, generatedAt);
  const result = deriveResult(profile);
  return `# Manager–Technical Ally Collaboration Charter\n\n` +
    `Status: Self-reported draft for human review · ${generatedAt}\n\n` +
    `## Shared purpose\n\n${profile.collaboration.outcomeDetail}\n\n` +
    `## Technical ally responsibility\n\n${profile.collaboration.allyResponsibility}\n\n` +
    `## Nurse-manager decision rights\n\n${profile.collaboration.nurseDecisionRights}\n\n` +
    `The nurse manager or authorized nurse owns nursing meaning, professional priorities, acceptance, escalation, and any decision that affects nurses, learners, patients, communities, or institutions. Technical access and implementation skill do not transfer that authority.\n\n` +
    `## First deliverable\n\n${result.firstOutcome}\n\n` +
    `## Evidence of value\n\n${profile.collaboration.successSignal}\n\n` +
    `## Review cadence\n\n${result.reviewCadence}\n\n` +
    `## Stop conditions\n\n${markdownList(result.stopConditions)}\n\n` +
    `## Responsible business path\n\n**Stage:** ${result.businessStage}\n\n**Path:** ${result.businessModel}\n\n**Boundary:** ${profile.venture.businessBoundary || 'No additional business boundary supplied.'}\n\n` +
    `## Commercial and contribution rights\n\n` +
    `Nurse and community knowledge remains attributed. Participation, compensation, ownership, reuse, publication, and withdrawal terms must be agreed before commercialization. This charter creates no endorsement, partnership, employment, procurement decision, or institutional authorization.\n\n` +
    `## Current system posture\n\nEDENA not evaluated · A0/no action · draft-only · no connectors · no external actions · no persistent memory · no PHI.\n`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
}

function htmlList(items) {
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
}

export function buildDashboardHtml(state, generatedAt = new Date().toISOString()) {
  const profile = buildProfile(state, generatedAt);
  const result = deriveResult(profile);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manager–Technical Ally Collaboration Dashboard</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext y='26' font-size='26'%3E🕯️%3C/text%3E%3C/svg%3E"><style>
:root{--navy:#10213f;--teal:#0f766e;--gold:#b7791f;--cream:#fbf6ec;--ink:#1f2e3d;--muted:#526273;--white:#fff;--border:#d8e2e8}*{box-sizing:border-box}body{margin:0;font:17px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--cream)}header{padding:42px 22px;color:var(--white);background:linear-gradient(135deg,var(--navy),#174e5c)}main,footer{max-width:1040px;margin:auto;padding:24px}h1,h2,h3{line-height:1.15}h1{max-width:800px;margin:.2em 0;font-size:clamp(2rem,6vw,4rem)}h2{color:var(--navy)}.tag{display:inline-block;padding:5px 10px;border-radius:999px;color:var(--navy);background:#f2d799;font-weight:800}.boundary{margin:18px 0;padding:16px;border-left:5px solid var(--gold);border-radius:8px;background:#fff4d8}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{padding:20px;border:1px solid var(--border);border-radius:14px;background:var(--white);box-shadow:0 2px 8px #10213f12}.wide{grid-column:1/-1}dt{margin-top:10px;color:var(--muted);font-size:.8rem;font-weight:800;text-transform:uppercase}dd{margin:3px 0 10px}li{margin:.35rem 0}.posture{font-weight:800;color:var(--teal)}footer{color:var(--muted);font-size:.9rem}@media(max-width:700px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}}</style></head><body><header><span class="tag">Browser-local collaboration packet</span><h1>Manager–Technical Ally Dashboard</h1><p>Prepared for ${escapeHtml(profile.identity.displayName)} · ${escapeHtml(generatedAt.slice(0, 10))}</p></header><main><div class="boundary"><strong>Not authority.</strong> This self-reported dashboard verifies no nursing identity, competence, credential, appointment, managerial authority, institutional permission, or deployment authority. It contains no connectors and performs no action.</div><section class="grid"><article class="card"><h2>Ally orientation</h2><h3>${escapeHtml(result.primary.label)}</h3><p>${escapeHtml(result.primary.promise)}</p><p><strong>First move:</strong> ${escapeHtml(result.primary.firstMove)}</p></article><article class="card"><h2>Technical foundation</h2>${htmlList(result.backgrounds)}</article><article class="card wide"><h2>First bounded collaboration</h2><dl><dt>Outcome</dt><dd>${escapeHtml(result.firstOutcome)}</dd><dt>Broad detail</dt><dd>${escapeHtml(profile.collaboration.outcomeDetail)}</dd><dt>Success signal</dt><dd>${escapeHtml(profile.collaboration.successSignal)}</dd><dt>Review cadence</dt><dd>${escapeHtml(result.reviewCadence)}</dd></dl></article><article class="card"><h2>Technical ally owns</h2><p>${escapeHtml(profile.collaboration.allyResponsibility)}</p><h3>Contribution areas</h3>${htmlList(result.contributions)}</article><article class="card"><h2>Nurse manager decides</h2><p>${escapeHtml(profile.collaboration.nurseDecisionRights)}</p><p>Nursing meaning, professional priorities, acceptance, escalation, and impact on nurses remain under nurse-led human judgment.</p></article><article class="card"><h2>Manager needs to understand</h2>${htmlList(result.managerNeeds)}</article><article class="card"><h2>Stop conditions</h2>${htmlList(result.stopConditions)}</article><article class="card wide"><h2>Responsible venture path</h2><p><strong>Stage:</strong> ${escapeHtml(result.businessStage)}</p><p><strong>Business path:</strong> ${escapeHtml(result.businessModel)}</p><ol><li>Interview nurses about one recurring problem.</li><li>Choose one bounded, no-PHI outcome.</li><li>Build a reversible draft-only prototype.</li><li>Let nurse reviewers correct the workflow and claims.</li><li>Ask for repeat use and payment before expanding.</li></ol><p><strong>Boundary:</strong> ${escapeHtml(profile.venture.businessBoundary || 'No additional business boundary supplied.')}</p><p>Nurse and community knowledge must not be commercialized without agreed participation, attribution, rights, and compensation.</p></article><article class="card wide"><h2>System posture</h2><p class="posture">EDENA: Not evaluated · A0/no action · Draft only</p><p>Connectors off · External actions off · Persistent memory off · No PHI · No patient, learner, workforce, credential, secret, or restricted institutional records.</p></article></section></main><footer><p><strong>Agents propose. Humans judge. Nurses steward.</strong></p><p>This file is a static local dashboard. Opening it does not install software, activate an agent, connect a service, upload data, or authorize institutional use.</p></footer></body></html>`;
}

const encoder = new TextEncoder();

export async function sha256Hex(value) {
  const bytes = value instanceof Uint8Array ? value : encoder.encode(String(value));
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function buildPackageEntries(state, generatedAt = new Date().toISOString()) {
  const profile = buildProfile(state, generatedAt);
  const payloads = [
    {
      name: 'README-FIRST.md',
      data: `# Technical Ally + Nurse Manager Collaboration Package\n\nGenerated: ${generatedAt}\n\nThis package was created locally in the browser from the Technical Ally SOUL Quiz. It contains a self-reported ally profile, collaboration charter, and static manager-facing dashboard.\n\n## What opening this package does\n\nOpening or unzipping creates no installation, connection, account, agent, schedule, memory, message, task, or external action. Open \`manager-ally-collaboration-dashboard.html\` in a browser to review the static dashboard.\n\n## Boundaries\n\n- No PHI, patient information, learner or workforce records, credentials, secrets, or restricted institutional material.\n- The quiz verifies no identity, credential, competence, appointment, authority, endorsement, partnership, or institutional permission.\n- The technical ally may propose and build within the agreed scope. Nurses define nursing meaning and judge nursing impact. Authorized humans decide and act.\n- Institutional use requires separate privacy, security, legal, labor, procurement, accessibility, clinical/informatics, operational-owner, and data-governance review as applicable.\n- Review every file before importing into Hermes or sharing. This is not a Hermes self-install build kit.\n\n*Agents propose. Humans judge. Nurses steward.*\n`
    },
    { name: 'ally-soul-profile.json', data: `${JSON.stringify(profile, null, 2)}\n` },
    { name: 'ALLY-SOUL.md', data: buildSoulMarkdown(state, generatedAt) },
    { name: 'MANAGER-ALLY-COLLABORATION-CHARTER.md', data: buildCharter(state, generatedAt) },
    { name: 'manager-ally-collaboration-dashboard.html', data: buildDashboardHtml(state, generatedAt) }
  ];
  const inventory = [];
  for (const item of payloads) {
    const bytes = encoder.encode(item.data);
    inventory.push({ path: item.name, bytes: bytes.length, sha256: await sha256Hex(bytes) });
  }
  const manifest = {
    package_id: 'naio-technical-ally-manager-collaboration-dashboard',
    package_version: SCHEMA_VERSION,
    generated_at: generatedAt,
    profile_type: profile.profile_type,
    profile_schema_url: PROFILE_SCHEMA_URL,
    install_on_download: false,
    static_dashboard_only: true,
    readiness: 'self-reported-draft-for-human-review',
    authority_granted: false,
    edena: 'not-evaluated',
    autonomy: 'A0-no-action',
    data_boundary: 'no-PHI',
    file_inventory: inventory
  };
  const manifestEntry = { name: 'PACKAGE-MANIFEST.json', data: `${JSON.stringify(manifest, null, 2)}\n` };
  const ledgerItems = [...payloads, manifestEntry];
  const ledgerRows = [];
  for (const item of ledgerItems) ledgerRows.push(`${await sha256Hex(item.data)}  ${item.name}`);
  return [...ledgerItems, { name: 'SHA256SUMS.txt', data: `${ledgerRows.join('\n')}\n` }];
}

export async function buildPackageZip(state, generatedAt = new Date().toISOString()) {
  const entries = await buildPackageEntries(state, generatedAt);
  return { entries, bytes: createStoredZip(entries, new Date(generatedAt)) };
}
