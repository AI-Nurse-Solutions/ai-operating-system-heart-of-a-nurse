import {
  STORAGE_KEY,
  LEGACY_SETUP_KEY,
  LEGACY_DISMISS_KEY,
  CONTEXTS,
  DEPARTMENTS,
  ASSIGNMENT_STATUSES,
  SHIFT_WINDOWS,
  ROLE_REGISTRY,
  CAPABILITY_REGISTRY,
  createInitialState,
  createSyntheticDemoState,
  normalizeState,
  addLocalRole,
  removeLocalExtension,
  addDashboard,
  removeDashboard,
  activateDashboard,
  endDashboardSession,
  expireReloadBoundSessions,
  expireElapsedAssignments,
  roleById,
  capabilityById,
  dashboardTitle,
  configurationPosture,
  migrateLegacySetupState,
  exportState,
  importState,
  labelFor
} from './switchboard-model.mjs';

const dashboardDialog = document.querySelector('#dashboard-dialog');
const dashboardForm = document.querySelector('#dashboard-form');
const roleDialog = document.querySelector('#role-dialog');
const roleForm = document.querySelector('#role-form');
const bridgeDialog = document.querySelector('#bridge-dialog');
const dashboardList = document.querySelector('#dashboard-list');
const dashboardView = document.querySelector('#dashboard-view');
const dashboardCount = document.querySelector('#dashboard-count');
const localRoleCount = document.querySelector('#local-role-count');
const localRoleList = document.querySelector('#local-role-list');
const statusMessage = document.querySelector('#status-message');
const legacyBanner = document.querySelector('#legacy-banner');
const importInput = document.querySelector('#import-state');
const exportButton = document.querySelector('#export-state');
const resetButton = document.querySelector('#reset-state');

let initialStorageWarning = '';
let expiryTimer = null;
const dialogReturnFocus = new WeakMap();
const dialogInertState = new WeakMap();
const dialogA11yState = new WeakMap();
let state = loadState();
let legacyState = loadLegacyState();
let legacyMigrationAvailable = Boolean(legacyState && migrateLegacySetupState(legacyState, new Date().toISOString(), 'legacy-availability-check'));
const syntheticDemoState = createSyntheticDemoState();
let syntheticDemoDashboardId = syntheticDemoState.activeDashboardId;

function isSyntheticDemoMode() {
  return state.dashboards.length === 0;
}

function visibleState() {
  if (!isSyntheticDemoMode()) return state;
  syntheticDemoState.activeDashboardId = syntheticDemoDashboardId;
  return syntheticDemoState;
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return createInitialState();
    const normalized = normalizeState(JSON.parse(raw));
    if (normalized) return expireElapsedAssignments(expireReloadBoundSessions(normalized, new Date().toISOString()), new Date().toISOString());
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    try { localStorage.removeItem(STORAGE_KEY); }
    catch { initialStorageWarning = 'Stored Switchboard data could not be read or removed. Clear this site’s stored data in browser settings before relying on reset.'; }
  }
  return createInitialState();
}

function loadLegacyState() {
  try {
    if (localStorage.getItem(LEGACY_DISMISS_KEY) === '1') return null;
    const raw = localStorage.getItem(LEGACY_SETUP_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function persist(message = '') {
  state.updatedAt = new Date().toISOString();
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    if (localStorage.getItem(STORAGE_KEY) !== JSON.stringify(state)) throw new Error('Storage verification failed.');
    if (message) announce(message);
    return true;
  } catch {
    announce('Local storage is unavailable. Export JSON before leaving if you want to keep this configuration.', true);
    return false;
  }
}

function rememberLegacyDecision() {
  try {
    localStorage.setItem(LEGACY_DISMISS_KEY, '1');
    return localStorage.getItem(LEGACY_DISMISS_KEY) === '1';
  } catch {
    announce('This choice could not be saved. The Setup Helper prompt may return after reload.', true);
    return false;
  }
}

function announce(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle('error', isError);
}

function showDialog(dialog) {
  if (document.activeElement instanceof HTMLElement) dialogReturnFocus.set(dialog, document.activeElement);
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else {
    dialog.setAttribute('open', '');
    dialog.dataset.fallback = 'true';
    dialogA11yState.set(dialog, { role: dialog.getAttribute('role'), ariaModal: dialog.getAttribute('aria-modal') });
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    const siblings = [...document.body.children].filter((element) => element !== dialog);
    dialogInertState.set(dialog, siblings.map((element) => [element, element.inert]));
    siblings.forEach((element) => { element.inert = true; });
    dialog.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')?.focus();
  }
}

function closeDialog(dialog) {
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
  delete dialog.dataset.fallback;
  const inertState = dialogInertState.get(dialog) || [];
  inertState.forEach(([element, wasInert]) => { element.inert = wasInert; });
  dialogInertState.delete(dialog);
  const a11yState = dialogA11yState.get(dialog);
  if (a11yState) {
    if (a11yState.role === null) dialog.removeAttribute('role'); else dialog.setAttribute('role', a11yState.role);
    if (a11yState.ariaModal === null) dialog.removeAttribute('aria-modal'); else dialog.setAttribute('aria-modal', a11yState.ariaModal);
  }
  dialogA11yState.delete(dialog);
  const returnTarget = dialogReturnFocus.get(dialog);
  dialogReturnFocus.delete(dialog);
  if (returnTarget?.isConnected) returnTarget.focus();
}

function fallbackFocusable(dialog) {
  return [...dialog.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')];
}

function optionList(items, selected = '') {
  return items.map((item) => `<option value="${escapeHtml(item.value)}" ${item.value === selected ? 'selected' : ''}>${escapeHtml(item.label)}</option>`).join('');
}

function allRoles() {
  return [
    ...ROLE_REGISTRY,
    ...state.localRoles
      .filter((item) => ['professional-community-role', 'functional-assignment'].includes(item.kind))
      .map((item) => ({ ...item, boundary: 'Local Draft · Not NAIO-reviewed.', capabilities: [], contexts: CONTEXTS.map((context) => context.value) }))
  ];
}

function allCapabilities() {
  return [...CAPABILITY_REGISTRY];
}

function roleChoices(contextKey) {
  return allRoles().filter((item) => item.contexts?.includes(contextKey)).map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.displayName)}${item.status === 'local-draft-not-reviewed' ? ' · local draft' : ''}</option>`).join('');
}

function openDashboardForm() {
  dashboardForm.reset();
  document.querySelector('#dashboard-context').innerHTML = optionList(CONTEXTS, 'personal');
  document.querySelector('#dashboard-department').innerHTML = optionList(DEPARTMENTS, 'personal-learning');
  document.querySelector('#dashboard-role').innerHTML = roleChoices('personal');
  document.querySelector('#dashboard-assignment').innerHTML = optionList(ASSIGNMENT_STATUSES, 'self-declared');
  document.querySelector('#dashboard-shift').innerHTML = optionList(SHIFT_WINDOWS, 'session');
  renderFormChecks();
  document.querySelector('#dashboard-form-error').hidden = true;
  showDialog(dashboardDialog);
  setTimeout(() => document.querySelector('#dashboard-context')?.focus(), 0);
}

function renderFormChecks() {
  const selectedRole = document.querySelector('#dashboard-role').value;
  const primary = roleById(selectedRole, state);
  const recommended = new Set(primary?.capabilities || []);
  document.querySelector('#capability-options').innerHTML = allCapabilities()
    .filter((item) => recommended.has(item.id))
    .map((item) => `<label class="check-option"><input type="checkbox" name="capability" value="${escapeHtml(item.id)}" checked><span>${escapeHtml(item.displayName)}<small>Compatible with this role · still creates no authority</small></span></label>`).join('') || '<p class="rail-empty">Local draft roles have no reviewed capability compatibility yet.</p>';
}

function updateRoleChoicesForContext() {
  const roleSelect = document.querySelector('#dashboard-role');
  roleSelect.innerHTML = roleChoices(document.querySelector('#dashboard-context').value);
  renderFormChecks();
}

function randomSuffix() {
  try { return crypto.randomUUID(); } catch { return `${Date.now()}-${Math.random().toString(36).slice(2)}`; }
}

function render() {
  const demoMode = isSyntheticDemoMode();
  dashboardCount.textContent = String(visibleState().dashboards.length);
  exportButton.disabled = demoMode;
  exportButton.title = demoMode ? 'Create a local dashboard before exporting your own configuration.' : '';
  resetButton.textContent = demoMode ? 'Clear saved local data' : 'Clear local Switchboard';
  renderLegacyBanner();
  renderDashboardRail();
  renderLocalRegistry();
  renderDashboardView();
  scheduleExpiryRefresh();
}

function scheduleExpiryRefresh() {
  if (expiryTimer) clearTimeout(expiryTimer);
  const expiries = state.dashboards
    .filter((item) => ['8-hours', '12-hours'].includes(item.shiftWindow) && item.assignmentExpiresAt)
    .map((item) => new Date(item.assignmentExpiresAt).getTime())
    .filter((timestamp) => timestamp > Date.now());
  if (!expiries.length) return;
  const delay = Math.min(Math.max(0, Math.min(...expiries) - Date.now() + 50), 2147483647);
  expiryTimer = setTimeout(() => {
    state = expireElapsedAssignments(state, new Date().toISOString());
    persist('A declared assignment window expired and was marked not current.');
    render();
  }, delay);
}

function renderLegacyBanner() {
  legacyBanner.hidden = !legacyMigrationAvailable || state.dashboards.length > 0;
}

function renderDashboardRail() {
  const renderedState = visibleState();
  const demoMode = isSyntheticDemoMode();
  document.querySelector('.rail-heading strong').textContent = demoMode ? 'Synthetic examples' : 'My dashboards';
  dashboardList.innerHTML = renderedState.dashboards.map((dashboard) => {
    const role = roleById(dashboard.primaryRoleId, renderedState);
    const current = dashboard.id === renderedState.activeDashboardId;
    const dataAttribute = demoMode ? 'data-demo-dashboard-id' : 'data-dashboard-id';
    return `<button class="dashboard-link" type="button" ${dataAttribute}="${escapeHtml(dashboard.id)}" aria-pressed="${current ? 'true' : 'false'}"><strong>${escapeHtml(role?.displayName || 'Unknown role')}</strong><span>${escapeHtml(labelFor(CONTEXTS, dashboard.contextKey))} · ${escapeHtml(labelFor(DEPARTMENTS, dashboard.departmentKey))}</span>${demoMode ? '<small>Synthetic · review only</small>' : ''}</button>`;
  }).join('');
}

function renderLocalRegistry() {
  localRoleCount.textContent = String(state.localRoles.length);
  localRoleList.innerHTML = state.localRoles.length ? state.localRoles.map((item) => `<div class="local-role-item"><span><strong>${escapeHtml(item.displayName)}</strong><small>${escapeHtml(item.kind.replaceAll('-', ' '))} · not reviewed</small></span><button class="text-button" type="button" data-remove-local-role="${escapeHtml(item.id)}">Remove</button></div>`).join('') : '<p class="rail-empty">No local drafts.</p>';
}

function scopeList(items, emptyLabel) {
  return items?.length ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : `<p>${escapeHtml(emptyLabel)}</p>`;
}

function assessmentCard(item, label, open = false) {
  return `<details class="assessment-card" ${open ? 'open' : ''}><summary><span>${escapeHtml(label)}</span><strong>${escapeHtml(item?.displayName || 'Unknown')}</strong></summary><div class="assessment-card-body"><p>${escapeHtml(item?.description || item?.boundary || 'No reviewed description is available.')}</p><div class="assessment-limits"><div><h6>Preparation allowed</h6>${scopeList(item?.allowed, 'No reviewed allowed-use list.')}</div><div><h6>Not allowed</h6>${scopeList(item?.prohibited, 'No reviewed prohibited-use list.')}</div></div></div></details>`;
}

function renderDashboardView() {
  const renderedState = visibleState();
  const demoMode = isSyntheticDemoMode();
  const dashboard = renderedState.dashboards.find((item) => item.id === renderedState.activeDashboardId) || renderedState.dashboards[0];
  if (!dashboard) return;
  if (demoMode) syntheticDemoDashboardId = dashboard.id;
  else if (state.activeDashboardId !== dashboard.id) state.activeDashboardId = dashboard.id;
  const card = configurationPosture(dashboard, renderedState);
  const role = roleById(dashboard.primaryRoleId, renderedState);
  const capabilities = dashboard.capabilityIds.map((id) => capabilityById(id, renderedState)).filter(Boolean);
  const actions = demoMode
    ? '<button class="btn btn-quiet" type="button" data-action="bridge">Why sending is unavailable</button>'
    : `<button class="btn btn-quiet" type="button" data-action="bridge">Why sending is unavailable</button>${card.active ? '<button class="btn btn-quiet" type="button" data-action="end-session">End session</button>' : ''}<button class="text-button" type="button" data-action="remove-dashboard">Remove</button>`;
  dashboardView.innerHTML = `
    ${demoMode ? '<div class="demo-notice"><div><span>Synthetic demo · not saved</span><strong>Review a populated Switchboard before configuring anything.</strong><p>Switch the three examples in the left rail. Expand the role and capability cards below to inspect what is allowed and prohibited.</p></div><button class="btn btn-primary" type="button" data-action="create-dashboard">Create my own →</button></div>' : ''}
    <div class="dashboard-head">
      <div><p class="dashboard-kicker">${demoMode ? 'Synthetic working identity · review only' : `Working identity · ${escapeHtml(card.active ? 'declared window active' : 'inactive or expired')}`}</p><h3>${escapeHtml(dashboardTitle(dashboard, renderedState))}</h3><p>${escapeHtml(labelFor(ASSIGNMENT_STATUSES, dashboard.assignmentStatus))} · ${escapeHtml(labelFor(SHIFT_WINDOWS, dashboard.shiftWindow))}</p></div>
      <div class="dashboard-head-actions">${actions}</div>
    </div>
    <section class="authority-card ${card.active ? '' : 'inactive'}" aria-labelledby="configuration-posture-title">
      <div class="authority-card-head"><h4 id="configuration-posture-title">Dashboard Configuration Posture</h4><div class="authority-badges"><span>EDENA: ${escapeHtml(card.edena)}</span><span>${escapeHtml(card.autonomy)}</span><span>${escapeHtml(card.disposition)}</span></div></div>
      <div class="authority-body">
        <div class="authority-meta"><div><strong>Context</strong><span>${escapeHtml(labelFor(CONTEXTS, dashboard.contextKey))}</span></div><div><strong>Assignment</strong><span>${escapeHtml(card.assignment)}</span></div><div><strong>Primary role</strong><span>${escapeHtml(card.role)}</span></div></div>
        <div class="authority-columns"><div><h5>Why this posture applies</h5><ul>${card.reasons.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div><div><h5>Boundaries in force</h5><ul>${card.boundaries.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></div></div>
      </div>
    </section>
    <div class="dashboard-role-grid">
      <section class="dashboard-panel"><h4>Role</h4><div class="tag-list"><span class="tag">Primary · ${escapeHtml(role?.displayName || 'Unknown')}</span><span class="tag draft">One role per preview dashboard</span></div></section>
      <section class="dashboard-panel"><h4>Capability stack</h4><div class="tag-list">${capabilities.map((item) => `<span class="tag">${escapeHtml(item.displayName)}</span>`).join('') || '<span class="tag draft">No capabilities selected</span>'}</div></section>
    </div>
    <section class="assessment-panel" aria-labelledby="assessment-title">
      <div class="assessment-heading"><div><p class="dashboard-kicker">Assessment view</p><h4 id="assessment-title">Inspect what this configuration means</h4></div><p>These cards describe preparation boundaries, not executable tools or professional authority.</p></div>
      <div class="assessment-grid">${assessmentCard(role, 'Primary role', true)}${capabilities.map((item) => assessmentCard(item, 'Capability')).join('')}</div>
    </section>
    <section class="preview-functions" aria-labelledby="preview-functions-title"><h4 id="preview-functions-title">What works in this preview</h4><div><article><strong>Switch context</strong><span>Compare separate role dashboards without blending their metadata.</span></article><article><strong>Inspect boundaries</strong><span>Review allowed preparation, prohibited activity, and the A0 posture.</span></article><article><strong>Configure locally</strong><span>Create, export, import, end, or remove your own browser-local dashboards.</span></article></div></section>
    <div class="dashboard-boundary"><strong>Separate but linked:</strong> only dashboard configuration metadata shares this Switchboard. Opening another dashboard changes the visible working identity; it does not transfer or merge a work artifact, employer data, file, memory, connector, or permission. This preview performs no clinical, external, or Hermes action.</div>`;
}

function downloadJson() {
  try {
    const blob = new Blob([exportState(state)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'naio-switchboard.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    announce('Switchboard JSON exported. It contains your local configuration; review it before sharing.');
  } catch (error) { announce(error.message, true); }
}

async function importJson(file) {
  if (!file) return;
  try {
    if (file.size > 250000) throw new Error('Switchboard file is too large.');
    const text = await file.text();
    const now = new Date().toISOString();
    const imported = expireElapsedAssignments(expireReloadBoundSessions(importState(text), now), now);
    if ((state.dashboards.length || state.localRoles.length) && !window.confirm('Importing replaces every current local dashboard and draft role. Select Cancel and use Export JSON first if you need a backup. Continue with replacement?')) return announce('Import cancelled. Current local configuration was kept.');
    state = imported;
    persist('Switchboard JSON imported after strict validation.');
    render();
  } catch (error) { announce(error.message, true); }
  finally { importInput.value = ''; }
}

dashboardForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const errorBox = document.querySelector('#dashboard-form-error');
  try {
    const result = addDashboard(state, {
      contextKey: document.querySelector('#dashboard-context').value,
      departmentKey: document.querySelector('#dashboard-department').value,
      primaryRoleId: document.querySelector('#dashboard-role').value,
      supportingRoleIds: [],
      capabilityIds: [...dashboardForm.querySelectorAll('input[name="capability"]:checked')].map((input) => input.value),
      assignmentStatus: document.querySelector('#dashboard-assignment').value,
      shiftWindow: document.querySelector('#dashboard-shift').value
    }, new Date().toISOString(), randomSuffix());
    state = result.state;
    persist('Separate role dashboard created. Role selection did not verify credentials or grant authority.');
    closeDialog(dashboardDialog);
    render();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
});

roleForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const errorBox = document.querySelector('#role-form-error');
  try {
    const result = addLocalRole(state, {
      displayName: document.querySelector('#local-role-name').value,
      kind: document.querySelector('#local-role-kind').value
    }, new Date().toISOString(), randomSuffix());
    state = result.state;
    persist('Local draft added. It is not NAIO-reviewed and creates no authority.');
    closeDialog(roleDialog);
    render();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
});

dashboardList.addEventListener('click', (event) => {
  const demoButton = event.target.closest('[data-demo-dashboard-id]');
  if (demoButton) {
    syntheticDemoDashboardId = demoButton.dataset.demoDashboardId;
    render();
    dashboardView.focus();
    const selected = syntheticDemoState.dashboards.find((item) => item.id === syntheticDemoDashboardId);
    announce(`Synthetic example selected: ${dashboardTitle(selected, syntheticDemoState)}. Nothing was saved.`);
    return;
  }
  const button = event.target.closest('[data-dashboard-id]');
  if (!button) return;
  try {
    state = activateDashboard(state, button.dataset.dashboardId, new Date().toISOString());
    persist();
    render();
    dashboardView.focus();
    const selected = state.dashboards.find((item) => item.id === state.activeDashboardId);
    announce(`${dashboardTitle(selected, state)} selected.`);
  } catch (error) { announce(error.message, true); }
});

localRoleList.addEventListener('click', (event) => {
  const button = event.target.closest('[data-remove-local-role]');
  if (!button) return;
  if (!window.confirm('Remove this unused local draft role or assignment? Public registry entries and Role Packs are not changed.')) return;
  try {
    state = removeLocalExtension(state, button.dataset.removeLocalRole, new Date().toISOString());
    persist('Local draft removed. No dashboard or public registry entry was changed.');
    render();
  } catch (error) {
    announce(error.message, true);
  }
});

dashboardView.addEventListener('click', (event) => {
  const action = event.target.closest('[data-action]')?.dataset.action;
  const dashboard = state.dashboards.find((item) => item.id === state.activeDashboardId);
  if (action === 'create-dashboard') openDashboardForm();
  if (action === 'bridge') showDialog(bridgeDialog);
  if (action === 'end-session' && dashboard) {
    state = endDashboardSession(state, dashboard.id, new Date().toISOString());
    persist('Dashboard session ended. Its assignment is now marked not current.');
    render();
    dashboardView.focus();
  }
  if (action === 'remove-dashboard' && dashboard && window.confirm('Remove this local dashboard? This does not alter any Hermes profile or public role package.')) {
    state = removeDashboard(state, dashboard.id, new Date().toISOString());
    persist('Local dashboard removed.');
    render();
    dashboardView.focus();
  }
});

document.querySelector('#dashboard-context').addEventListener('change', updateRoleChoicesForContext);
document.querySelector('#dashboard-role').addEventListener('change', renderFormChecks);
document.querySelector('#dashboard-assignment').addEventListener('change', (event) => {
  if (event.target.value === 'not-current') document.querySelector('#dashboard-shift').value = 'not-current';
  else if (document.querySelector('#dashboard-shift').value === 'not-current') document.querySelector('#dashboard-shift').value = 'session';
});
document.querySelector('#dashboard-shift').addEventListener('change', (event) => {
  if (event.target.value === 'not-current') document.querySelector('#dashboard-assignment').value = 'not-current';
  else if (document.querySelector('#dashboard-assignment').value === 'not-current') document.querySelector('#dashboard-assignment').value = 'self-declared';
});
document.querySelector('#create-dashboard').addEventListener('click', openDashboardForm);
document.querySelector('#create-role').addEventListener('click', () => {
  roleForm.reset();
  document.querySelector('#role-form-error').hidden = true;
  showDialog(roleDialog);
  setTimeout(() => document.querySelector('#local-role-name')?.focus(), 0);
});
exportButton.addEventListener('click', downloadJson);
document.querySelector('#import-button').addEventListener('click', () => importInput.click());
importInput.addEventListener('change', () => importJson(importInput.files?.[0]));
document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-close-dialog]');
  if (!button) return;
  const dialog = document.getElementById(button.dataset.closeDialog);
  if (dialog) closeDialog(dialog);
});
document.addEventListener('keydown', (event) => {
  const dialog = document.querySelector('dialog[data-fallback="true"][open]');
  if (!dialog) return;
  if (event.key === 'Escape') {
    event.preventDefault();
    closeDialog(dialog);
    return;
  }
  if (event.key !== 'Tab') return;
  const focusable = fallbackFocusable(dialog);
  if (!focusable.length) return event.preventDefault();
  const first = focusable[0];
  const last = focusable.at(-1);
  if (!dialog.contains(document.activeElement)) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
resetButton.addEventListener('click', () => {
  if (!window.confirm('Clear every local Switchboard dashboard and local draft role from this browser?')) return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    if (localStorage.getItem(STORAGE_KEY) !== null) throw new Error('Storage verification failed.');
  } catch {
    return announce('Local storage could not be cleared. Use your browser’s stored-site-data settings before relying on reset.', true);
  }
  state = createInitialState();
  announce('Saved local Switchboard data cleared. Synthetic review examples remain visible; existing downloads and Hermes profiles were not changed.');
  render();
});
document.querySelector('#migrate-legacy').addEventListener('click', () => {
  const migrated = migrateLegacySetupState(legacyState, new Date().toISOString(), randomSuffix(), state);
  if (!migrated) return announce('The older Setup Helper lane could not be migrated.', true);
  state = migrated;
  const saved = persist('Inactive starter dashboard created from the older Setup Helper lane. Existing local drafts were preserved. Review it before use.');
  if (saved) rememberLegacyDecision();
  legacyState = null;
  legacyMigrationAvailable = false;
  render();
});
document.querySelector('#dismiss-legacy').addEventListener('click', () => {
  rememberLegacyDecision();
  legacyState = null;
  legacyMigrationAvailable = false;
  legacyBanner.hidden = true;
});

render();
if (initialStorageWarning) announce(initialStorageWarning, true);
