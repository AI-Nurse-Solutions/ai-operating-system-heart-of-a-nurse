import {
  STORAGE_KEY,
  PACKAGE_FILENAME,
  TECHNICAL_BACKGROUNDS,
  COLLABORATION_AREAS,
  MANAGER_NEEDS,
  RELATIONSHIPS,
  BUSINESS_STAGES,
  BUSINESS_MODELS,
  FIRST_OUTCOMES,
  REVIEW_CADENCES,
  STOP_CONDITIONS,
  ARCHETYPES,
  createInitialState,
  normalizeState,
  validateStep,
  deriveResult,
  buildProfile,
  buildSoulMarkdown,
  buildPackageZip
} from './ally-quiz-model.mjs';

const app = document.getElementById('quiz-app');
const status = document.getElementById('quiz-status');
const progress = document.getElementById('quiz-progress');
const progressLabel = document.getElementById('quiz-progress-label');
const resetButton = document.getElementById('reset-quiz');
const STEP_TITLES = ['Stewardship gate', 'Technical foundation', 'Nurse-manager collaboration', 'Venture stewardship', 'First bounded outcome', 'Results and dashboard'];

let storageWarning = '';
let state = restoreState();

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
    const restored = normalizeState(JSON.parse(raw));
    if (restored) return restored;
    sessionStorage.removeItem(STORAGE_KEY);
    storageWarning = 'An invalid saved draft was removed. Begin again with broad, non-identifying information.';
  } catch {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { storageWarning = 'Stored quiz data could not be repaired. Use browser site-data controls before continuing.'; }
  }
  return createInitialState();
}

function announce(message, isError = false) {
  status.textContent = message;
  status.classList.toggle('error', isError);
}

function saveState(message = 'Draft saved in this browser tab only.') {
  state.updatedAt = new Date().toISOString();
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    announce(message);
  } catch {
    announce('This browser could not preserve the draft. Finish and download your files before closing the tab.', true);
  }
}

function checkedValues(form, name) {
  return [...form.querySelectorAll(`input[name="${CSS.escape(name)}"]:checked`)].map((input) => input.value);
}

function choiceGrid(name, options, selected = []) {
  const chosen = new Set(selected);
  return `<div class="choice-grid">${options.map((option) => `<label class="choice"><input type="checkbox" name="${attr(name)}" value="${attr(option.id)}"${chosen.has(option.id) ? ' checked' : ''}><span>${escapeHtml(option.label)}</span></label>`).join('')}</div>`;
}

function radioGrid(name, options, selected = '', descriptions = {}) {
  return `<div class="radio-grid">${options.map((option) => `<label class="radio-card"><input type="radio" name="${attr(name)}" value="${attr(option.id)}"${selected === option.id ? ' checked' : ''} required><span><strong>${escapeHtml(option.label)}</strong>${descriptions[option.id] ? `<small>${escapeHtml(descriptions[option.id])}</small>` : ''}</span></label>`).join('')}</div>`;
}

function formShell(title, intro, body, { back = true, nextLabel = 'Continue' } = {}) {
  return `<form id="ally-form" novalidate><div class="step-heading"><p class="step-kicker">${escapeHtml(STEP_TITLES[state.step])}</p><h2 tabindex="-1">${escapeHtml(title)}</h2><p>${escapeHtml(intro)}</p></div><div id="form-error" class="form-error" role="alert" tabindex="-1" hidden></div>${body}<div class="quiz-actions">${back ? '<button class="btn btn-secondary" type="button" data-nav="back">← Back</button>' : '<span></span>'}<button class="btn btn-quiet" type="button" data-action="save">Save in this tab</button><button class="btn btn-primary" type="submit">${escapeHtml(nextLabel)} →</button></div></form>`;
}

function safetyView() {
  const confirmations = [
    ['noPhi', 'I will not enter PHI, patient stories, workforce or learner records, credentials, secrets, or restricted institutional information.'],
    ['noNursingAuthority', 'I understand that technical skill, this quiz, and access to Nurse AI OS do not make me a nurse or create nursing authority.'],
    ['nursesDecide', 'Nurses define nursing meaning, workflow reality, acceptable burden, and nursing impact; I will not speak for them without participation and consent.'],
    ['noInstitutionalAuthority', 'This profile verifies no appointment, partnership, endorsement, employment, procurement decision, system access, or institutional permission.'],
    ['noUnapprovedAction', 'I will keep prototypes bounded, reversible, and draft-only until the appropriate humans approve any connection, publication, commitment, or action.']
  ];
  const body = `<div class="boundary-panel"><strong>Private browser-local intake.</strong> Your working draft stays in this tab. The page has no submission endpoint. Downloads remain on your device. Simple checks block some obvious identifier, contact, markup, and secret patterns, but they cannot detect every form of sensitive information.</div><div class="field"><label for="display-name">Name, initials, or project alias <span class="required">required</span></label><input id="display-name" name="display-name" type="text" maxlength="80" autocomplete="off" value="${attr(state.identity.displayName)}" required><small>Do not enter a legal identifier, email, phone number, employer, customer, patient, student, or employee name.</small></div><fieldset><legend>Five stewardship commitments <span class="required">all required</span></legend>${confirmations.map(([key, label]) => `<label class="safety-check"><input type="checkbox" name="safety-${attr(key)}"${state.safety[key] ? ' checked' : ''} required><span>${escapeHtml(label)}</span></label>`).join('')}</fieldset>`;
  return formShell('Begin as an ally—not a substitute', 'This quiz is for non-nurse technologists supporting nurse-led work or building nurse-supporting businesses.', body, { back: false });
}

function identityView() {
  const experience = [
    { id: 'learning', label: 'Learning or early-career technical practitioner' },
    { id: 'practitioner', label: 'Independent practitioner or experienced contributor' },
    { id: 'senior', label: 'Senior technical, product, security, or operational leader' },
    { id: 'founder', label: 'Founder, consultant, or business operator' }
  ];
  const body = `<fieldset><legend>Technical background <span class="required">choose at least one</span></legend>${choiceGrid('background', TECHNICAL_BACKGROUNDS, state.identity.backgrounds)}</fieldset><fieldset><legend>Current technical season <span class="required">choose one</span></legend>${radioGrid('experience', experience, state.identity.experience)}</fieldset><fieldset><legend>Relationship to nurse-led work <span class="required">choose one</span></legend>${radioGrid('relationship', RELATIONSHIPS, state.identity.relationship)}</fieldset>`;
  return formShell('Name the capability you bring', 'Choose functions you can contribute. This is a working orientation—not a competence assessment or credential.', body);
}

function collaborationView() {
  const body = `<div class="boundary-panel"><strong>Start with the nurse manager’s work.</strong> Technology follows a nurse-defined problem, affected-person review, evidence, and accountable ownership.</div><fieldset><legend>How could you contribute? <span class="required">choose at least one</span></legend>${choiceGrid('contribution', COLLABORATION_AREAS, state.collaboration.contributionAreas)}</fieldset><fieldset><legend>Which manager needs do you want to understand? <span class="required">choose at least one</span></legend>${choiceGrid('manager-needs', MANAGER_NEEDS, state.collaboration.managerNeeds)}</fieldset>`;
  return formShell('Stand beside the manager’s workflow', 'Select where your technical capability might reduce burden without taking over professional judgment.', body);
}

function ventureView() {
  const commitments = [
    ['nurseParticipation', 'Nurses will participate in defining nursing problems, reviewing workflow effects, and deciding whether the result is useful.'],
    ['attributionCompensation', 'Attribution, participation, ownership, reuse, publication, compensation, and withdrawal terms will be agreed before nurse or community knowledge is commercialized.'],
    ['evidenceBeforeClaims', 'I will not fabricate customers, revenue, endorsements, validation, readiness, compliance, savings, or outcomes.'],
    ['conflictDisclosure', 'I will disclose sponsorship, incentives, commercial interests, employer conflicts, and material limitations.']
  ];
  const body = `<fieldset><legend>Business or venture stage <span class="required">choose one</span></legend>${radioGrid('business-stage', BUSINESS_STAGES, state.venture.businessStage)}</fieldset><fieldset><legend>Business path <span class="required">choose one</span></legend>${radioGrid('business-model', BUSINESS_MODELS, state.venture.businessModel)}</fieldset><div class="field"><label for="business-boundary">Business boundary <span class="optional">optional</span></label><textarea id="business-boundary" name="business-boundary" maxlength="500" placeholder="Broadly state what your business will not do, claim, collect, or automate.">${escapeHtml(state.venture.businessBoundary)}</textarea><small>No company names, customer records, contact details, credentials, secrets, or protected information.</small></div><fieldset><legend>Four venture commitments <span class="required">all required</span></legend>${commitments.map(([key, label]) => `<label class="safety-check"><input type="checkbox" name="venture-${attr(key)}"${state.venture[key] ? ' checked' : ''} required><span>${escapeHtml(label)}</span></label>`).join('')}</fieldset>`;
  return formShell('Build a business that earns nurse trust', 'Commercial ambition is welcome. Legitimacy comes from participation, attribution, evidence, and honest boundaries.', body);
}

function contractView() {
  const body = `<fieldset><legend>First bounded outcome <span class="required">choose one</span></legend>${radioGrid('first-outcome', FIRST_OUTCOMES, state.collaboration.firstOutcome)}</fieldset><div class="field"><label for="outcome-detail">Describe the outcome in broad terms <span class="required">required</span></label><textarea id="outcome-detail" name="outcome-detail" maxlength="500" required>${escapeHtml(state.collaboration.outcomeDetail)}</textarea><small>No patient, nurse, employee, employer, customer, or organization identifiers.</small></div><div class="field"><label for="ally-responsibility">What will you own? <span class="required">required</span></label><textarea id="ally-responsibility" name="ally-responsibility" maxlength="500" required placeholder="Example: prototype structure, test harness, documented limitations, and rollback path.">${escapeHtml(state.collaboration.allyResponsibility)}</textarea></div><div class="field"><label for="nurse-rights">What must the nurse manager or authorized nurse decide? <span class="required">required</span></label><textarea id="nurse-rights" name="nurse-rights" maxlength="500" required placeholder="Example: problem framing, nursing meaning, acceptance criteria, burden, escalation, and whether the result should be used.">${escapeHtml(state.collaboration.nurseDecisionRights)}</textarea></div><div class="field"><label for="success-signal">What observable signal would show value? <span class="required">required</span></label><textarea id="success-signal" name="success-signal" maxlength="360" required placeholder="Example: the manager completes the artifact, a reviewer accepts it with less rework, and the manager returns with a second problem.">${escapeHtml(state.collaboration.successSignal)}</textarea></div><fieldset><legend>Human review cadence <span class="required">choose one</span></legend>${radioGrid('review-cadence', REVIEW_CADENCES, state.collaboration.reviewCadence)}</fieldset><fieldset><legend>Stop conditions <span class="required">choose at least three</span></legend>${choiceGrid('stop-condition', STOP_CONDITIONS, state.collaboration.stopConditions)}</fieldset>`;
  return formShell('Write the first collaboration contract', 'One outcome, explicit ownership, nurse decision rights, measurable value, and visible stop conditions.', body, { nextLabel: 'Build my results and dashboard' });
}

function resultsView() {
  const result = deriveResult(state);
  const supporting = result.supporting.map((item) => item.label);
  return `<div class="results"><div class="completion-banner"><span class="mark">✓</span><div><strong>Your Technical Ally SOUL is ready for review.</strong><p>Nothing was installed, connected, activated, uploaded, sent, scheduled, or institutionally authorized.</p></div></div><section class="result-grid"><article class="result-card"><h3>Primary working orientation</h3><p><strong>${escapeHtml(result.primary.label)}</strong></p><p>${escapeHtml(result.primary.promise)}</p><p><strong>First move:</strong> ${escapeHtml(result.primary.firstMove)}</p></article><article class="result-card"><h3>Supporting orientations</h3>${supporting.length ? `<ul>${supporting.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : '<p>No supporting orientation was derived. Review the primary orientation with a nurse partner.</p>'}</article><article class="result-card wide"><h3>First bounded collaboration</h3><dl><dt>Outcome</dt><dd>${escapeHtml(result.firstOutcome)}</dd><dt>Broad detail</dt><dd>${escapeHtml(state.collaboration.outcomeDetail)}</dd><dt>Technical ally owns</dt><dd>${escapeHtml(state.collaboration.allyResponsibility)}</dd><dt>Nurse manager decides</dt><dd>${escapeHtml(state.collaboration.nurseDecisionRights)}</dd><dt>Success signal</dt><dd>${escapeHtml(state.collaboration.successSignal)}</dd><dt>Review cadence</dt><dd>${escapeHtml(result.reviewCadence)}</dd></dl></article><article class="result-card"><h3>Manager needs to understand</h3><ul>${result.managerNeeds.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></article><article class="result-card"><h3>Stop conditions</h3><ul>${result.stopConditions.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></article><article class="result-card wide"><h3>Responsible business path</h3><p><strong>Stage:</strong> ${escapeHtml(result.businessStage)}</p><p><strong>Path:</strong> ${escapeHtml(result.businessModel)}</p><p>${escapeHtml(state.venture.businessBoundary || 'No additional business boundary supplied.')}</p><p>Interview nurses → choose one bounded outcome → build a reversible no-PHI prototype → accept nurse correction → ask for return use and payment.</p></article><article class="result-card wide"><h3>Governance posture</h3><p><strong>EDENA: Not evaluated · A0/no action · Draft only.</strong></p><p>No nursing, clinical, managerial, institutional, procurement, deployment, or representation authority. No connectors, external actions, persistent memory, PHI, patient information, workforce records, credentials, secrets, or restricted institutional material.</p></article></section><section class="download-panel"><h2>Download your results with the manager dashboard</h2><p>The ZIP includes your JSON profile, Technical Ally SOUL, collaboration charter, static manager-facing dashboard, manifest, and SHA-256 ledger. Review every file before sharing or importing.</p><div class="download-actions"><button class="btn btn-primary" type="button" data-download="package">Download results + dashboard ZIP</button><button class="btn btn-secondary" type="button" data-download="profile">Download JSON profile</button><button class="btn btn-secondary" type="button" data-download="soul">Download Technical Ally SOUL</button></div></section><div class="quiz-actions"><button class="btn btn-secondary" type="button" data-nav="back">← Review answers</button><button class="btn btn-quiet" type="button" data-action="restart">Start a new ally profile</button><a class="btn btn-primary" href="../post-setup/#choose-role">Nurse Manager downloads →</a></div></div>`;
}

function collectStep(form, step) {
  if (step === 0) {
    state.identity.displayName = form.elements['display-name'].value.trim();
    for (const key of Object.keys(state.safety)) state.safety[key] = form.elements[`safety-${key}`].checked;
  } else if (step === 1) {
    state.identity.backgrounds = checkedValues(form, 'background');
    state.identity.experience = form.elements.experience.value;
    state.identity.relationship = form.elements.relationship.value;
  } else if (step === 2) {
    state.collaboration.contributionAreas = checkedValues(form, 'contribution');
    state.collaboration.managerNeeds = checkedValues(form, 'manager-needs');
  } else if (step === 3) {
    state.venture.businessStage = form.elements['business-stage'].value;
    state.venture.businessModel = form.elements['business-model'].value;
    state.venture.businessBoundary = form.elements['business-boundary'].value.trim();
    for (const key of ['nurseParticipation', 'attributionCompensation', 'evidenceBeforeClaims', 'conflictDisclosure']) state.venture[key] = form.elements[`venture-${key}`].checked;
  } else if (step === 4) {
    state.collaboration.firstOutcome = form.elements['first-outcome'].value;
    state.collaboration.outcomeDetail = form.elements['outcome-detail'].value.trim();
    state.collaboration.allyResponsibility = form.elements['ally-responsibility'].value.trim();
    state.collaboration.nurseDecisionRights = form.elements['nurse-rights'].value.trim();
    state.collaboration.successSignal = form.elements['success-signal'].value.trim();
    state.collaboration.reviewCadence = form.elements['review-cadence'].value;
    state.collaboration.stopConditions = checkedValues(form, 'stop-condition');
  }
}

function showError(message) {
  const error = document.getElementById('form-error');
  if (!error) return;
  error.textContent = message;
  error.hidden = false;
  error.focus();
  announce(message, true);
}

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function handleDownload(kind, button) {
  button.disabled = true;
  try {
    const generatedAt = new Date().toISOString();
    if (kind === 'profile') {
      downloadBlob('technical-ally-soul-profile.json', new Blob([`${JSON.stringify(buildProfile(state, generatedAt), null, 2)}\n`], { type: 'application/json' }));
      announce('JSON profile downloaded. Review it before sharing or importing.');
    } else if (kind === 'soul') {
      downloadBlob('TECHNICAL-ALLY-SOUL.md', new Blob([buildSoulMarkdown(state, generatedAt)], { type: 'text/markdown' }));
      announce('Technical Ally SOUL downloaded. Keep it under your control.');
    } else {
      announce('Building the local results and dashboard package…');
      const pkg = await buildPackageZip(state, generatedAt);
      downloadBlob(PACKAGE_FILENAME, new Blob([pkg.bytes], { type: 'application/zip' }));
      announce('Results and manager dashboard ZIP downloaded. Opening it installs and activates nothing.');
    }
  } catch (error) {
    announce(error instanceof Error ? error.message : 'The download could not be created.', true);
  } finally {
    button.disabled = false;
  }
}

function updateProgress() {
  const percent = Math.round(((state.step + 1) / 6) * 100);
  progress.style.width = `${percent}%`;
  progress.parentElement.setAttribute('aria-valuenow', String(percent));
  progressLabel.textContent = `Step ${state.step + 1} of 6 · ${STEP_TITLES[state.step]}`;
}

function bindView() {
  const form = document.getElementById('ally-form');
  if (form) {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      collectStep(form, state.step);
      const error = validateStep(state, state.step);
      if (error) return showError(error);
      state.step += 1;
      saveState('Step completed. Draft remains in this tab only.');
      render();
    });
    form.querySelector('[data-action="save"]')?.addEventListener('click', () => {
      collectStep(form, state.step);
      const normalized = normalizeState(state);
      if (!normalized) return showError('Remove identifiers, contact information, markup, credentials, or secrets before saving.');
      state = normalized;
      saveState();
    });
  }
  app.querySelector('[data-nav="back"]')?.addEventListener('click', () => {
    if (form) collectStep(form, state.step);
    const normalized = normalizeState(state);
    if (!normalized) return showError('Remove identifiers, contact information, markup, credentials, or secrets before leaving this step.');
    state = normalized;
    state.step = Math.max(0, state.step - 1);
    saveState('Returned to the prior step. Draft remains in this tab only.');
    render();
  });
  app.querySelector('[data-action="restart"]')?.addEventListener('click', () => {
    if (!window.confirm('Start a new Technical Ally profile and remove this tab’s working draft? Download anything you want to keep first.')) return;
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* status below remains truthful */ }
    state = createInitialState();
    announce('New local profile started.');
    render();
  });
  for (const button of app.querySelectorAll('[data-download]')) button.addEventListener('click', () => handleDownload(button.dataset.download, button));
}

function render() {
  if (state.step === 0) app.innerHTML = safetyView();
  else if (state.step === 1) app.innerHTML = identityView();
  else if (state.step === 2) app.innerHTML = collaborationView();
  else if (state.step === 3) app.innerHTML = ventureView();
  else if (state.step === 4) app.innerHTML = contractView();
  else app.innerHTML = resultsView();
  updateProgress();
  bindView();
  requestAnimationFrame(() => {
    const heading = app.querySelector('h2');
    if (heading) heading.focus({ preventScroll: true });
  });
}

resetButton.addEventListener('click', () => {
  if (!window.confirm('Reset this tab and remove the Technical Ally quiz draft? Download anything you want to keep first.')) return;
  try { sessionStorage.removeItem(STORAGE_KEY); } catch { announce('The browser could not remove saved data. Use browser site-data controls.', true); return; }
  state = createInitialState();
  announce('This tab was reset.');
  render();
});

render();
if (storageWarning) announce(storageWarning, true);
