import {
  STORAGE_KEY,
  IDENTITY_ROLES,
  POST_SETUP_LANES,
  ERROR_CODES,
  createInitialState,
  normalizeSavedState,
  determineRoute,
  getFlow,
  validateStage,
  safeTaskForLane,
  buildSupportSummary,
  completionSummary
} from './setup-helper-model.mjs';

const content = document.querySelector('#chat-content');
const nextButton = document.querySelector('#next-button');
const backButton = document.querySelector('#back-button');
const issueButton = document.querySelector('#issue-button');
const resetButton = document.querySelector('#reset-button');
const progressFill = document.querySelector('#progress-fill');
const progressBar = document.querySelector('[role="progressbar"]');
const progressPercent = document.querySelector('#progress-percent');
const stageItems = [...document.querySelectorAll('#stage-list li')];
const validationMessage = document.querySelector('#validation-message');
const announcement = document.querySelector('#announcement');
const resumeBanner = document.querySelector('#resume-banner');
const resumeButton = document.querySelector('#resume-button');
const issueDialog = document.querySelector('#issue-dialog');
const issueCode = document.querySelector('#issue-code');
const issueGuidance = document.querySelector('#issue-guidance');
const supportSafe = document.querySelector('#support-safe');
const supportSummary = document.querySelector('#support-summary');
const copySummary = document.querySelector('#copy-summary');
const copyStatus = document.querySelector('#copy-status');

const STAGE_NAMES = ['Safety boundary', 'Choose a door', 'Your environment', 'Identity and lane', 'Readiness', 'Guided setup', 'First safe success'];
const ISSUE_GUIDANCE = {
  download_missing: 'Check the browser download indicator and your Downloads folder. Do not download copies from unofficial mirrors.',
  soul_export_missing: 'Return to the final SOUL Quiz screen and export again. Do not add patient, credential, or employer-confidential information.',
  hermes_command_missing: 'Close and reopen Terminal after installation, then use the official installation guide. Do not invent a PATH command from an unknown forum.',
  hermes_doctor_failed: 'Do not continue past the health check. Use the official Hermes docs or send the sanitized error category to a human.',
  desktop_did_not_open: 'Run hermes doctor first. Then check the official Desktop/quick-start guide. Do not change macOS security settings broadly.',
  permission_or_managed_device: 'Stop the local installation. Use Browser-first unless the device owner or organization explicitly authorizes installation.',
  unknown: 'Stop rather than guess. Copy the sanitized summary and ask a human. Share only the minimum non-sensitive error category.'
};

let hadSavedState = false;
let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    const parsed = JSON.parse(raw);
    const normalized = normalizeSavedState(parsed);
    if (!normalized) {
      localStorage.removeItem(STORAGE_KEY);
      return createInitialState();
    }
    hadSavedState = true;
    return normalized;
  } catch {
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    return createInitialState();
  }
}

function persist() {
  state.updatedAt = new Date().toISOString();
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* private browsing may block storage */ }
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));
}

function choice(name, value, label, detail = '', checked = false) {
  const id = `${name}-${value}`;
  return `<div class="choice"><input type="radio" id="${id}" name="${name}" value="${value}" ${checked ? 'checked' : ''}><label for="${id}"><strong>${escapeHtml(label)}</strong>${detail ? `<span>${escapeHtml(detail)}</span>` : ''}</label></div>`;
}

function checkbox(path, label, checked = false) {
  return `<label class="check-row"><input type="checkbox" data-path="${path}" ${checked ? 'checked' : ''}><span>${escapeHtml(label)}</span></label>`;
}

function assistantMessage(title, body) {
  return `<div class="message"><div class="agent-avatar" aria-hidden="true">🕯️</div><div class="message-bubble"><h2 id="stage-heading" tabindex="-1">${escapeHtml(title)}</h2>${body}</div></div>`;
}

function renderSafety() {
  return assistantMessage('Before we begin: protect the person behind the data', `
    <p>I guide setup. I do not install software, execute commands, activate tools, or make clinical decisions.</p>
    <div class="stage-note"><strong>Time expectation:</strong> a careful SOUL first pass usually takes 30–45 minutes. macOS installation adds time. You can pause and resume on this device.</div>
    <div class="question-card"><fieldset><legend>Confirm all four boundaries</legend><div class="check-list">
      ${checkbox('safety.noPhi', 'I will not enter patient names, charts, screenshots, identifiers, dates, room numbers, or identifiable patient stories.', state.safety.noPhi)}
      ${checkbox('safety.noClinical', 'I will not use this setup for patient-specific care, clinical decisions, diagnosis, treatment, staffing, or live EHR work.', state.safety.noClinical)}
      ${checkbox('safety.noSecrets', 'I will not paste passwords, API keys, tokens, recovery codes, payment information, or employer-confidential material.', state.safety.noSecrets)}
      ${checkbox('safety.guideOnly', 'I understand this helper provides review-first guidance; I remain responsible for every action and approval.', state.safety.guideOnly)}
    </div></fieldset></div>`);
}

function renderDoor() {
  return assistantMessage('Which door fits today?', `
    <p>Both doors serve the same no-PHI Nurse AI OS. Browser-first is the safest default when you are unsure.</p>
    <div class="question-card"><fieldset><legend>Choose one setup door</legend><div class="choice-grid">
      ${choice('door', 'browser', 'Door 1 · Browser-first', 'No software installation. Prove the workflow in a browser AI you already use.', state.door === 'browser')}
      ${choice('door', 'mac', 'Door 2 · macOS Hermes', 'For a personal or explicitly authorized Mac where you control installation.', state.door === 'mac')}
    </div></fieldset></div>`);
}

function renderEnvironment() {
  const env = state.environment;
  const routed = state.door === 'mac' && determineRoute(state) === 'browser' && env.device && env.ownership && env.admin;
  return assistantMessage('Tell me about the setup environment', `
    <p>These categories stay in your browser on this device. Do not enter a device name, employer name, username, email address, or serial number.</p>
    ${routed ? '<div class="route-warning"><strong>Safer route:</strong> this environment is not appropriate for Phase 1 macOS installation. I will route you to Browser-first. Nothing is installed.</div>' : ''}
    <div class="question-card">
      <fieldset><legend>Device category</legend><div class="choice-grid">
        ${choice('device', 'mac', 'Mac', 'Personal or authorized macOS computer', env.device === 'mac')}
        ${choice('device', 'windows', 'Windows', 'Phase 1 routes this to Browser-first', env.device === 'windows')}
        ${choice('device', 'mobile', 'Phone / tablet / Chromebook', 'Browser-first only in Phase 1', env.device === 'mobile')}
        ${choice('device', 'other', 'Other / not sure', 'Browser-first is the safe default', env.device === 'other')}
      </div></fieldset>
      <fieldset><legend>Device ownership</legend><div class="choice-grid">
        ${choice('ownership', 'personal', 'Personal', 'You control storage and installation', env.ownership === 'personal')}
        ${choice('ownership', 'authorized', 'Explicitly authorized', 'The owner has approved this setup', env.ownership === 'authorized')}
        ${choice('ownership', 'employer', 'Employer-managed', 'Use Browser-first unless your organization approves', env.ownership === 'employer')}
        ${choice('ownership', 'shared', 'Shared', 'Use a separate personal account or Browser-first', env.ownership === 'shared')}
      </div></fieldset>
      <fieldset><legend>Can you install software?</legend><div class="choice-grid">
        ${choice('admin', 'yes', 'Yes', 'I control or am authorized to approve installation', env.admin === 'yes')}
        ${choice('admin', 'no', 'No / not sure', 'Browser-first is safer', env.admin === 'no')}
      </div></fieldset>
      <fieldset><legend>Browser</legend><div class="choice-grid">
        ${choice('browser', 'chrome', 'Chrome / Chromium', '', env.browser === 'chrome')}
        ${choice('browser', 'safari', 'Safari', '', env.browser === 'safari')}
        ${choice('browser', 'firefox', 'Firefox', '', env.browser === 'firefox')}
        ${choice('browser', 'other', 'Other / not sure', '', env.browser === 'other')}
      </div></fieldset>
      <fieldset><legend>Hermes status</legend><div class="choice-grid">
        ${choice('hermesStatus', 'not-installed', 'Not installed', '', env.hermesStatus === 'not-installed')}
        ${choice('hermesStatus', 'installed', 'Already installed', '', env.hermesStatus === 'installed')}
        ${choice('hermesStatus', 'not-sure', 'Not sure', '', env.hermesStatus === 'not-sure')}
      </div></fieldset>
    </div>`);
}

function renderIdentity() {
  return assistantMessage('Choose identity and lane separately', `
    <p>Your broad identity helps me explain. Your post-setup lane routes content. Neither verifies licensure, enrollment, employment, faculty status, managerial authority, or institutional approval.</p>
    <div class="question-card">
      <fieldset><legend>Broad onboarding identity</legend><div class="choice-grid">${IDENTITY_ROLES.map((x) => choice('identityRole', x.value, x.label, '', state.identityRole === x.value)).join('')}</div></fieldset>
      <fieldset><legend>Post-setup lane</legend><div class="choice-grid">${POST_SETUP_LANES.map((x) => choice('postSetupLane', x.value, x.label, '', state.postSetupLane === x.value)).join('')}</div></fieldset>
    </div>`);
}

function renderReadiness() {
  const route = determineRoute(state);
  return assistantMessage('Readiness huddle', `
    <p>Your selected route is <strong>${route === 'mac' ? 'macOS Hermes' : 'Browser-first'}</strong>. Confirm each item before I show setup steps.</p>
    <div class="question-card"><fieldset><legend>Ready to proceed</legend><div class="check-list">
      ${checkbox('readiness.time', 'I can take my time, pause, and return rather than rush through permissions or boundaries.', state.readiness.time)}
      ${checkbox('readiness.folder', 'I have a personal Documents location that does not contain patient or employer-restricted files.', state.readiness.folder)}
      ${checkbox('readiness.recovery', 'I know I can stop, use the static guide, or ask a human instead of guessing.', state.readiness.recovery)}
      ${checkbox('readiness.boundaries', 'I will keep PHI, clinical decisions, credentials, and employer-confidential content out of setup.', state.readiness.boundaries)}
    </div></fieldset></div>`);
}

function renderFlow() {
  const route = state.route || determineRoute(state);
  const flow = getFlow(route);
  const index = Math.min(state.flowIndex, flow.length - 1);
  const step = flow[index];
  const verified = state.completedFlowIds.includes(step.id);
  const links = (step.links || []).map((link) => `<a class="btn btn-quiet btn-sm" href="${escapeHtml(link.href)}" ${link.external ? 'target="_blank" rel="noopener noreferrer"' : ''} ${link.download ? 'download' : ''}>${escapeHtml(link.label)} →</a>`).join('');
  const command = step.command ? `<div class="command-box"><code>${escapeHtml(step.command)}</code><button class="copy-command" type="button" data-command="${escapeHtml(step.command)}">Copy command</button></div>` : '';
  const task = step.id.endsWith('first-win') || step.id.endsWith('first-conversation') ? `<div class="task-box"><strong>Your lane-safe starter prompt</strong>\n${escapeHtml(safeTaskForLane(state.postSetupLane))}</div>` : '';
  return assistantMessage(`${route === 'mac' ? 'macOS Hermes' : 'Browser-first'} · Step ${index + 1} of ${flow.length}`, `
    <div class="flow-card"><div class="flow-meta"><span>${escapeHtml(step.time)}</span><span>${escapeHtml(step.risk)}</span></div><h3>${escapeHtml(step.title)}</h3><p><strong>Why:</strong> ${escapeHtml(step.why)}</p><ol>${step.actions.map((action) => `<li>${escapeHtml(action)}</li>`).join('')}</ol>${command}${links ? `<div class="flow-links">${links}</div>` : ''}${task}<label class="confirm-row" style="margin-top:1rem"><input id="flow-verified" type="checkbox" ${verified ? 'checked' : ''}><span><strong>Verify before continuing:</strong> ${escapeHtml(step.verify)}</span></label></div>`);
}

function renderComplete() {
  const summary = completionSummary(state);
  return assistantMessage('Your Phase 1 setup path is complete', `
    <p>You reached a safe first success. This is a setup milestone—not clinical readiness, institutional approval, credential verification, or permission to use PHI.</p>
    <div class="completion-grid"><div><strong>Route</strong>${summary.route === 'mac' ? 'macOS Hermes' : 'Browser-first'}</div><div><strong>Broad identity</strong>${escapeHtml(summary.identity)}</div><div><strong>Post-setup lane</strong>${escapeHtml(summary.lane)}</div><div><strong>Governance posture</strong>Shadow / observe-only; human executes</div></div>
    <div class="task-box"><strong>Keep this first-task prompt</strong>\n${escapeHtml(summary.task)}</div>
    <div class="stage-note"><strong>Boundary:</strong> ${escapeHtml(summary.boundary)}<br><strong>Posture:</strong> ${escapeHtml(summary.posture)}</div>
    <p><a class="btn btn-primary" href="../post-setup/">Review the five post-setup lane packages →</a> <button id="print-summary" class="btn btn-quiet" type="button">Print this summary</button></p>
    <p><strong>Agents propose. Humans judge. Nurses steward.</strong></p>`);
}

function render() {
  hideValidation();
  const renderers = [renderSafety, renderDoor, renderEnvironment, renderIdentity, renderReadiness, renderFlow, renderComplete];
  content.innerHTML = renderers[state.stage]();
  bindStageInputs();
  updateProgress();
  updateButtons();
  announcement.textContent = `${STAGE_NAMES[state.stage]}. Step content updated.`;
}

function bindStageInputs() {
  content.querySelectorAll('input[data-path]').forEach((input) => input.addEventListener('change', () => {
    const [group, key] = input.dataset.path.split('.');
    state[group][key] = input.checked;
    persist();
  }));
  content.querySelectorAll('input[type="radio"]').forEach((input) => input.addEventListener('change', () => {
    const focusedId = input.id;
    const name = input.name;
    if (['device', 'ownership', 'admin', 'browser', 'hermesStatus'].includes(name)) state.environment[name] = input.value;
    else state[name] = input.value;
    persist();
    if (state.stage === 2) {
      render();
      document.getElementById(focusedId)?.focus();
    }
  }));
  const verified = content.querySelector('#flow-verified');
  if (verified) verified.addEventListener('change', () => {
    const flow = getFlow(state.route || determineRoute(state));
    const id = flow[state.flowIndex].id;
    if (verified.checked && !state.completedFlowIds.includes(id)) state.completedFlowIds.push(id);
    if (!verified.checked) state.completedFlowIds = state.completedFlowIds.filter((x) => x !== id);
    persist();
  });
  content.querySelectorAll('.copy-command').forEach((button) => {
    const original = button.textContent;
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(button.dataset.command); button.textContent = 'Copied'; }
      catch { button.textContent = 'Select and copy manually'; }
      setTimeout(() => { button.textContent = original; }, 1800);
    });
  });
  content.querySelector('#print-summary')?.addEventListener('click', () => window.print());
}

function showValidation(message) {
  validationMessage.textContent = message;
  validationMessage.hidden = false;
  validationMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
function hideValidation() { validationMessage.hidden = true; validationMessage.textContent = ''; }

function next() {
  if (state.stage <= 4 && !validateStage(state.stage, state)) {
    const messages = ['Confirm all four safety boundaries before continuing.', 'Choose one setup door.', 'Answer every environment question without entering identifying details.', 'Choose one broad identity and one separate post-setup lane.', 'Confirm all four readiness items.'];
    showValidation(messages[state.stage]);
    return;
  }
  if (state.stage === 2) state.route = determineRoute(state);
  if (state.stage === 5) {
    const flow = getFlow(state.route);
    const current = flow[state.flowIndex];
    if (!state.completedFlowIds.includes(current.id)) {
      showValidation('Check the verification statement only after you have confirmed the expected result.');
      return;
    }
    if (state.flowIndex < flow.length - 1) state.flowIndex += 1;
    else state.stage = 6;
  } else if (state.stage < 6) state.stage += 1;
  persist();
  render();
  document.querySelector('#helper-app').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function back() {
  if (state.stage === 5 && state.flowIndex > 0) state.flowIndex -= 1;
  else if (state.stage === 6) {
    state.stage = 5;
    state.flowIndex = Math.max(0, getFlow(state.route).length - 1);
  } else if (state.stage > 0) state.stage -= 1;
  persist();
  render();
}

function updateProgress() {
  let progress = (state.stage / 6) * 100;
  if (state.stage === 5) {
    const flow = getFlow(state.route || determineRoute(state));
    progress = 83 + ((state.flowIndex + (state.completedFlowIds.includes(flow[state.flowIndex]?.id) ? 1 : 0)) / flow.length) * 14;
  }
  if (state.stage === 6) progress = 100;
  const rounded = Math.min(100, Math.round(progress));
  progressFill.style.width = `${rounded}%`;
  progressBar.setAttribute('aria-valuenow', String(rounded));
  progressPercent.textContent = `${rounded}%`;
  stageItems.forEach((item, index) => {
    item.classList.toggle('current', index === state.stage);
    item.classList.toggle('done', index < state.stage);
    if (index === state.stage) item.setAttribute('aria-current', 'step'); else item.removeAttribute('aria-current');
  });
}

function updateButtons() {
  backButton.hidden = state.stage === 0;
  nextButton.hidden = state.stage === 6;
  issueButton.hidden = false;
  if (state.stage === 5) {
    const flow = getFlow(state.route || determineRoute(state));
    nextButton.textContent = state.flowIndex === flow.length - 1 ? 'Verify and finish →' : 'I verified this step →';
  } else nextButton.textContent = state.stage === 4 ? 'Begin guided setup →' : 'Continue →';
}

function reset() {
  if (!window.confirm('Clear Setup Helper progress stored in this browser and restart?')) return;
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
  state = createInitialState();
  hadSavedState = false;
  resumeBanner.hidden = true;
  render();
}

function openIssueDialog() {
  issueCode.innerHTML = ERROR_CODES.map((item) => `<option value="${item.value}">${escapeHtml(item.label)}</option>`).join('');
  issueCode.value = state.issueCode || 'download_missing';
  supportSafe.checked = false;
  copySummary.disabled = true;
  copyStatus.textContent = '';
  refreshIssue();
  if (typeof issueDialog.showModal === 'function') issueDialog.showModal();
  else issueDialog.setAttribute('open', '');
}

function refreshIssue() {
  state.issueCode = issueCode.value;
  persist();
  issueGuidance.textContent = ISSUE_GUIDANCE[issueCode.value];
  supportSummary.value = buildSupportSummary(state, issueCode.value);
}

issueCode.addEventListener('change', refreshIssue);
supportSafe.addEventListener('change', () => { copySummary.disabled = !supportSafe.checked; });
copySummary.addEventListener('click', async () => {
  if (!supportSafe.checked) return;
  try { await navigator.clipboard.writeText(supportSummary.value); copyStatus.textContent = 'Sanitized summary copied. Review it once more before sharing.'; }
  catch { supportSummary.focus(); supportSummary.select(); copyStatus.textContent = 'Copy was blocked. The summary is selected for manual copying.'; }
});
nextButton.addEventListener('click', next);
backButton.addEventListener('click', back);
issueButton.addEventListener('click', openIssueDialog);
resetButton.addEventListener('click', reset);
resumeButton.addEventListener('click', () => {
  resumeBanner.hidden = true;
  document.querySelector('#stage-heading')?.focus?.();
});

if (hadSavedState && (state.stage > 0 || Object.values(state.safety).some(Boolean))) resumeBanner.hidden = false;
render();
