import { normalizeSavedState as normalizeLegacySetupState } from '../setup-helper/setup-helper-model.mjs';
import roleRegistryData from './data/role-registry.json' with { type: 'json' };

export const STORAGE_KEY = 'naio.switchboard.preview.v2';
export const LEGACY_SETUP_KEY = 'naio.setup-helper.phase1.v1';
export const LEGACY_DISMISS_KEY = 'naio.switchboard.legacy-dismissed.v1';
export const SCHEMA_VERSION = 2;

export const CONTEXTS = Object.freeze([
  { value: 'personal', label: 'Personal / learning' },
  { value: 'facility-a', label: 'Facility A' },
  { value: 'facility-b', label: 'Facility B' },
  { value: 'school-a', label: 'School A' },
  { value: 'clinic-a', label: 'Clinic A' },
  { value: 'committee-a', label: 'Committee A' },
  { value: 'community-a', label: 'Community A' },
  { value: 'association-a', label: 'Professional association A' }
]);

export const DEPARTMENTS = Object.freeze([
  { value: 'personal-learning', label: 'Personal learning' },
  { value: 'bedside', label: 'Bedside / direct care' },
  { value: 'critical-care', label: 'Critical care' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'administration', label: 'Administration' },
  { value: 'education', label: 'Education' },
  { value: 'informatics', label: 'Informatics' },
  { value: 'quality', label: 'Quality / improvement' },
  { value: 'research', label: 'Research / innovation' },
  { value: 'committee', label: 'Committee / shared governance' },
  { value: 'community', label: 'Community / organizing' },
  { value: 'legal-consulting', label: 'Medico-legal / consulting' },
  { value: 'other', label: 'Other bounded context' }
]);

export const ASSIGNMENT_STATUSES = Object.freeze([
  { value: 'self-declared', label: 'Self-declared · not independently verified' },
  { value: 'organization-assigned-unverified', label: 'Organization-assigned · not verified by this preview' },
  { value: 'education-enrolled-unverified', label: 'Education/enrollment context · not verified by this preview' },
  { value: 'community-assigned-unverified', label: 'Community assignment · not verified by this preview' },
  { value: 'not-current', label: 'Not a current assignment' }
]);

export const SHIFT_WINDOWS = Object.freeze([
  { value: 'session', label: 'Until this page is closed or reloaded' },
  { value: '8-hours', label: 'Eight-hour assignment window' },
  { value: '12-hours', label: 'Twelve-hour assignment window' },
  { value: 'not-current', label: 'No active shift or assignment' }
]);

function runtimeRegistryEntry(entry) {
  return Object.freeze({
    ...entry,
    contexts: Object.freeze([...entry.contexts]),
    compatibleCapabilities: Object.freeze([...entry.compatibleCapabilities]),
    allowed: Object.freeze([...entry.allowed]),
    prohibited: Object.freeze([...entry.prohibited]),
    review: Object.freeze({ ...entry.review }),
    capabilities: Object.freeze([...entry.compatibleCapabilities]),
    ceiling: entry.autonomyCeiling,
    boundary: `${entry.credentialPosture} ${entry.authoritySource}`
  });
}

export const ROLE_REGISTRY = Object.freeze(roleRegistryData.entries.filter((entry) => entry.kind !== 'capability').map(runtimeRegistryEntry));
export const CAPABILITY_REGISTRY = Object.freeze(roleRegistryData.entries.filter((entry) => entry.kind === 'capability').map(runtimeRegistryEntry));

const ROLE_IDS = new Set(ROLE_REGISTRY.map((item) => item.id));
const CAPABILITY_IDS = new Set(CAPABILITY_REGISTRY.map((item) => item.id));
const CONTEXT_IDS = new Set(CONTEXTS.map((item) => item.value));
const DEPARTMENT_IDS = new Set(DEPARTMENTS.map((item) => item.value));
const ASSIGNMENT_IDS = new Set(ASSIGNMENT_STATUSES.map((item) => item.value));
const SHIFT_IDS = new Set(SHIFT_WINDOWS.map((item) => item.value));
const LOCAL_ROLE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9 &/()'’\-]{1,59}$/;
const PROHIBITED_TITLE_PATTERN = /\b(?:patient|mrn|medical record|record number|patient id|patient identifier|dob|date of birth|ssn|social security|case number|employee id|student id)\b/i;
const ID_PATTERN = /^[a-z0-9][a-z0-9-]{0,79}$/;

const LEGACY_LANE_MAP = Object.freeze({
  student_nurse: { role: 'student-learner', capabilities: ['future'], department: 'personal-learning' },
  staff_nurse: { role: 'staff-nurse', capabilities: ['shift'], department: 'bedside' },
  nurse_leader_manager: { role: 'nurse-leader-manager', capabilities: ['lead'], department: 'administration' },
  nurse_educator: { role: 'nurse-educator', capabilities: ['teach'], department: 'education' },
  nurse_connected_ally: { role: 'nurse-connected-ally', capabilities: [], department: 'other' },
  nurse_practitioner_usa: { role: 'nurse-practitioner-usa', capabilities: ['np-wings'], department: 'personal-learning' }
});
const LEGACY_STATE_KEYS = new Set(['schemaVersion','stage','safety','door','environment','identityRole','postSetupLane','readiness','route','flowIndex','completedFlowIds','issueCode','updatedAt']);
const LEGACY_SAFETY_KEYS = new Set(['noPhi','noClinical','noSecrets','guideOnly']);
const LEGACY_ENVIRONMENT_KEYS = new Set(['device','ownership','admin','browser','hermesStatus']);
const LEGACY_READINESS_KEYS = new Set(['time','folder','recovery','boundaries']);

function isRecord(value) { return Boolean(value) && typeof value === 'object' && !Array.isArray(value); }
function hasOnlyKeys(value, allowed) { return Object.keys(value).every((key) => allowed.has(key)); }
function validIso(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)) return false;
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString() === value;
}
function uniqueStrings(value, max) { return Array.isArray(value) && value.length <= max && value.every((item) => typeof item === 'string') && new Set(value).size === value.length; }
function nowIso(now) { const date = now ? new Date(now) : new Date(); return Number.isFinite(date.getTime()) ? date.toISOString() : new Date().toISOString(); }
function slug(value) { return String(value).toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48); }
function hasExactLegacyShape(value) {
  return isRecord(value) && hasOnlyKeys(value, LEGACY_STATE_KEYS) && Object.keys(value).length === LEGACY_STATE_KEYS.size &&
    isRecord(value.safety) && hasOnlyKeys(value.safety, LEGACY_SAFETY_KEYS) && Object.keys(value.safety).length === LEGACY_SAFETY_KEYS.size &&
    isRecord(value.environment) && hasOnlyKeys(value.environment, LEGACY_ENVIRONMENT_KEYS) && Object.keys(value.environment).length === LEGACY_ENVIRONMENT_KEYS.size &&
    isRecord(value.readiness) && hasOnlyKeys(value.readiness, LEGACY_READINESS_KEYS) && Object.keys(value.readiness).length === LEGACY_READINESS_KEYS.size;
}

export function createInitialState(now) {
  return { schemaVersion: SCHEMA_VERSION, activeDashboardId: null, dashboards: [], localRoles: [], updatedAt: nowIso(now) };
}

export function makeId(prefix = 'dashboard', random = '') {
  const suffix = slug(random) || Math.random().toString(36).slice(2, 10);
  return `${slug(prefix) || 'item'}-${suffix}`.slice(0, 80);
}

export function roleById(id, state = null) {
  const builtIn = ROLE_REGISTRY.find((item) => item.id === id);
  if (builtIn) return builtIn;
  const local = state?.localRoles?.find((item) => item.id === id);
  return local && ['professional-community-role','functional-assignment'].includes(local.kind) ? { ...local, boundary: 'Local Draft · Not NAIO-reviewed. No credential, assignment, organizational, community, or institutional authority is verified.', capabilities: [], contexts: CONTEXTS.map((item) => item.value), ceiling: 'A0' } : null;
}

export function capabilityById(id, state = null) {
  const builtIn = CAPABILITY_REGISTRY.find((item) => item.id === id);
  if (builtIn) return builtIn;
  return null;
}
export function labelFor(collection, value) { return collection.find((item) => item.value === value)?.label || value; }

function normalizeLocalRole(candidate) {
  if (!isRecord(candidate) || !ID_PATTERN.test(candidate.id || '') || !LOCAL_ROLE_PATTERN.test(candidate.displayName || '') || PROHIBITED_TITLE_PATTERN.test(candidate.displayName || '')) return null;
  if (!hasOnlyKeys(candidate, new Set(['id','displayName','kind','status','createdAt']))) return null;
  if (!['professional-community-role','functional-assignment'].includes(candidate.kind)) return null;
  if (candidate.status !== 'local-draft-not-reviewed' || !validIso(candidate.createdAt)) return null;
  return { id: candidate.id, displayName: candidate.displayName, kind: candidate.kind, status: candidate.status, createdAt: new Date(candidate.createdAt).toISOString() };
}

function assignmentWindowIsValid(candidate) {
  const inactive = candidate.assignmentStatus === 'not-current' || candidate.shiftWindow === 'not-current';
  if (inactive) return candidate.assignmentStatus === 'not-current' && candidate.shiftWindow === 'not-current' && candidate.assignmentStartedAt === null && candidate.assignmentExpiresAt === null;
  if (!validIso(candidate.assignmentStartedAt)) return false;
  if (candidate.shiftWindow === 'session') return candidate.assignmentExpiresAt === null;
  if (!validIso(candidate.assignmentExpiresAt)) return false;
  const expectedHours = candidate.shiftWindow === '8-hours' ? 8 : candidate.shiftWindow === '12-hours' ? 12 : 0;
  if (!expectedHours) return false;
  return new Date(candidate.assignmentExpiresAt).getTime() - new Date(candidate.assignmentStartedAt).getTime() === expectedHours * 60 * 60 * 1000;
}

function normalizeDashboard(candidate, lookupState) {
  if (!isRecord(candidate) || !ID_PATTERN.test(candidate.id || '')) return null;
  if (!hasOnlyKeys(candidate, new Set(['id','contextKey','departmentKey','primaryRoleId','supportingRoleIds','capabilityIds','assignmentStatus','shiftWindow','assignmentStartedAt','assignmentExpiresAt','createdAt','updatedAt']))) return null;
  if (!CONTEXT_IDS.has(candidate.contextKey) || !DEPARTMENT_IDS.has(candidate.departmentKey)) return null;
  const role = roleById(candidate.primaryRoleId, lookupState);
  if (!role || !role.contexts.includes(candidate.contextKey)) return null;
  if (!uniqueStrings(candidate.supportingRoleIds, 0)) return null;
  if (!uniqueStrings(candidate.capabilityIds, 10) || candidate.capabilityIds.some((id) => !capabilityById(id, lookupState) || !role.capabilities.includes(id))) return null;
  if (!ASSIGNMENT_IDS.has(candidate.assignmentStatus) || !SHIFT_IDS.has(candidate.shiftWindow)) return null;
  if (!assignmentWindowIsValid(candidate)) return null;
  if (!validIso(candidate.createdAt) || !validIso(candidate.updatedAt)) return null;
  return {
    id: candidate.id,
    contextKey: candidate.contextKey,
    departmentKey: candidate.departmentKey,
    primaryRoleId: candidate.primaryRoleId,
    supportingRoleIds: [...candidate.supportingRoleIds],
    capabilityIds: [...candidate.capabilityIds],
    assignmentStatus: candidate.assignmentStatus,
    shiftWindow: candidate.shiftWindow,
    assignmentStartedAt: candidate.assignmentStartedAt ? new Date(candidate.assignmentStartedAt).toISOString() : null,
    assignmentExpiresAt: candidate.assignmentExpiresAt ? new Date(candidate.assignmentExpiresAt).toISOString() : null,
    createdAt: new Date(candidate.createdAt).toISOString(),
    updatedAt: new Date(candidate.updatedAt).toISOString()
  };
}

export function normalizeState(candidate) {
  if (!isRecord(candidate) || candidate.schemaVersion !== SCHEMA_VERSION) return null;
  if (!hasOnlyKeys(candidate, new Set(['schemaVersion','activeDashboardId','dashboards','localRoles','updatedAt']))) return null;
  if (!Array.isArray(candidate.localRoles) || candidate.localRoles.length > 24) return null;
  const localRoles = candidate.localRoles.map(normalizeLocalRole);
  if (localRoles.some((item) => !item)) return null;
  const localIds = localRoles.map((item) => item.id);
  if (new Set(localIds).size !== localIds.length || localIds.some((id) => ROLE_IDS.has(id) || CAPABILITY_IDS.has(id))) return null;
  const lookupState = { localRoles };
  if (!Array.isArray(candidate.dashboards) || candidate.dashboards.length > 24) return null;
  const dashboards = candidate.dashboards.map((item) => normalizeDashboard(item, lookupState));
  if (dashboards.some((item) => !item)) return null;
  const dashboardIds = dashboards.map((item) => item.id);
  if (new Set(dashboardIds).size !== dashboardIds.length) return null;
  if (candidate.activeDashboardId !== null && !dashboardIds.includes(candidate.activeDashboardId)) return null;
  if (!validIso(candidate.updatedAt)) return null;
  return { schemaVersion: SCHEMA_VERSION, activeDashboardId: candidate.activeDashboardId, dashboards, localRoles, updatedAt: new Date(candidate.updatedAt).toISOString() };
}

export function addLocalRole(state, input, now, idSuffix = '') {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Switchboard state is invalid.');
  if (normalized.localRoles.length >= 24) throw new Error('This preview supports up to 24 local draft extensions.');
  const displayName = String(input?.displayName || '').trim().replace(/\s+/g, ' ');
  if (!LOCAL_ROLE_PATTERN.test(displayName) || PROHIBITED_TITLE_PATTERN.test(displayName)) throw new Error('Use a generic role title only. Do not enter names, organizations, record identifiers, or narratives. Obvious identifier labels are blocked, but this is not exhaustive PHI detection.');
  const kind = input?.kind;
  if (!['professional-community-role','functional-assignment'].includes(kind)) throw new Error('Choose a valid role or assignment type.');
  const id = makeId('local-role', idSuffix || `${slug(displayName)}-${normalized.localRoles.length + 1}`);
  if (ROLE_IDS.has(id) || CAPABILITY_IDS.has(id) || normalized.localRoles.some((item) => item.id === id)) throw new Error('Extension identifier already exists.');
  normalized.localRoles.push({ id, displayName, kind, status: 'local-draft-not-reviewed', createdAt: nowIso(now) });
  normalized.updatedAt = nowIso(now);
  return { state: normalized, roleId: id };
}

export function removeLocalExtension(state, extensionId, now) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Switchboard state is invalid.');
  if (!normalized.localRoles.some((item) => item.id === extensionId)) throw new Error('Local extension was not found.');
  const inUse = normalized.dashboards.some((dashboard) => dashboard.primaryRoleId === extensionId || dashboard.supportingRoleIds.includes(extensionId) || dashboard.capabilityIds.includes(extensionId));
  if (inUse) throw new Error('Remove this extension from its dashboard before deleting the local draft.');
  normalized.localRoles = normalized.localRoles.filter((item) => item.id !== extensionId);
  normalized.updatedAt = nowIso(now);
  return normalized;
}

function computeExpiry(shiftWindow, startedAt) {
  if (shiftWindow === 'not-current') return null;
  if (shiftWindow === 'session') return null;
  const hours = shiftWindow === '8-hours' ? 8 : shiftWindow === '12-hours' ? 12 : 0;
  return hours ? new Date(new Date(startedAt).getTime() + hours * 60 * 60 * 1000).toISOString() : null;
}

export function addDashboard(state, input, now, idSuffix = '') {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Switchboard state is invalid.');
  if (normalized.dashboards.length >= 24) throw new Error('This preview supports up to 24 dashboards.');
  const role = roleById(input?.primaryRoleId, normalized);
  if (!role) throw new Error('Choose a valid primary role.');
  const supportingRoleIds = Array.isArray(input?.supportingRoleIds) ? [...new Set(input.supportingRoleIds)] : [];
  const capabilityIds = Array.isArray(input?.capabilityIds) ? [...new Set(input.capabilityIds)] : [];
  const timestamp = nowIso(now);
  const requestedStatus = input?.assignmentStatus || 'self-declared';
  const requestedWindow = input?.shiftWindow || 'session';
  const inactive = requestedStatus === 'not-current' || requestedWindow === 'not-current';
  const assignmentStatus = inactive ? 'not-current' : requestedStatus;
  const shiftWindow = inactive ? 'not-current' : requestedWindow;
  const id = makeId('dashboard', idSuffix || `${input?.contextKey}-${input?.departmentKey}-${role.id}-${normalized.dashboards.length + 1}`);
  if (normalized.dashboards.some((item) => item.id === id)) throw new Error('Dashboard identifier already exists.');
  const candidate = {
    id,
    contextKey: input?.contextKey,
    departmentKey: input?.departmentKey,
    primaryRoleId: role.id,
    supportingRoleIds,
    capabilityIds,
    assignmentStatus,
    shiftWindow,
    assignmentStartedAt: assignmentStatus === 'not-current' || shiftWindow === 'not-current' ? null : timestamp,
    assignmentExpiresAt: assignmentStatus === 'not-current' || shiftWindow === 'not-current' ? null : computeExpiry(shiftWindow, timestamp),
    createdAt: timestamp,
    updatedAt: timestamp
  };
  const dashboard = normalizeDashboard(candidate, normalized);
  if (!dashboard) throw new Error('Dashboard choices are invalid or incompatible.');
  normalized.dashboards.push(dashboard);
  normalized.activeDashboardId = dashboard.id;
  normalized.updatedAt = timestamp;
  return { state: normalized, dashboardId: dashboard.id };
}

export function removeDashboard(state, dashboardId, now) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Invalid Switchboard state');
  normalized.dashboards = normalized.dashboards.filter((item) => item.id !== dashboardId);
  if (normalized.activeDashboardId === dashboardId) normalized.activeDashboardId = normalized.dashboards[0]?.id || null;
  normalized.updatedAt = nowIso(now);
  return normalized;
}

export function activateDashboard(state, dashboardId, now) {
  const normalized = normalizeState(state);
  if (!normalized || !normalized.dashboards.some((item) => item.id === dashboardId)) throw new Error('Dashboard not found.');
  normalized.activeDashboardId = dashboardId;
  normalized.updatedAt = nowIso(now);
  return normalized;
}

export function endDashboardSession(state, dashboardId, now) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Invalid Switchboard state');
  const dashboard = normalized.dashboards.find((item) => item.id === dashboardId);
  if (!dashboard) throw new Error('Dashboard not found.');
  dashboard.assignmentStatus = 'not-current';
  dashboard.shiftWindow = 'not-current';
  dashboard.assignmentStartedAt = null;
  dashboard.assignmentExpiresAt = null;
  dashboard.updatedAt = nowIso(now);
  normalized.updatedAt = nowIso(now);
  return normalized;
}

export function expireReloadBoundSessions(state, now) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Invalid Switchboard state');
  let changed = false;
  for (const dashboard of normalized.dashboards) {
    if (dashboard.shiftWindow !== 'session') continue;
    dashboard.assignmentStatus = 'not-current';
    dashboard.shiftWindow = 'not-current';
    dashboard.assignmentStartedAt = null;
    dashboard.assignmentExpiresAt = null;
    dashboard.updatedAt = nowIso(now);
    changed = true;
  }
  if (changed) normalized.updatedAt = nowIso(now);
  return normalized;
}

export function expireElapsedAssignments(state, now) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Invalid Switchboard state');
  const timestamp = new Date(nowIso(now)).getTime();
  let changed = false;
  for (const dashboard of normalized.dashboards) {
    if (!['session', '8-hours', '12-hours'].includes(dashboard.shiftWindow)) continue;
    const startsInFuture = new Date(dashboard.assignmentStartedAt).getTime() > timestamp;
    const fixedWindowExpired = ['8-hours', '12-hours'].includes(dashboard.shiftWindow) && new Date(dashboard.assignmentExpiresAt).getTime() <= timestamp;
    if (!startsInFuture && !fixedWindowExpired) continue;
    dashboard.assignmentStatus = 'not-current';
    dashboard.shiftWindow = 'not-current';
    dashboard.assignmentStartedAt = null;
    dashboard.assignmentExpiresAt = null;
    dashboard.updatedAt = nowIso(now);
    changed = true;
  }
  if (changed) normalized.updatedAt = nowIso(now);
  return normalized;
}

export function dashboardTitle(dashboard, state) {
  const role = roleById(dashboard.primaryRoleId, state);
  return `${labelFor(CONTEXTS, dashboard.contextKey)} · ${labelFor(DEPARTMENTS, dashboard.departmentKey)} · ${role?.displayName || 'Unknown role'}`;
}

export function configurationPosture(dashboard, state, now) {
  const role = roleById(dashboard?.primaryRoleId, state);
  if (!role) return { disposition: 'Blocked', edena: 'Not evaluated', autonomy: 'A0 · no action', active: false, title: 'Unknown role', reasons: ['Unknown or removed role. Stop and review the dashboard.'], boundaries: ['No action is authorized.'] };
  const timestamp = new Date(nowIso(now)).getTime();
  const fixedWindow = ['8-hours', '12-hours'].includes(dashboard.shiftWindow);
  const malformedWindow = !assignmentWindowIsValid(dashboard);
  const notStarted = dashboard.assignmentStartedAt ? new Date(dashboard.assignmentStartedAt).getTime() > timestamp : false;
  const expired = fixedWindow && dashboard.assignmentExpiresAt ? new Date(dashboard.assignmentExpiresAt).getTime() <= timestamp : false;
  const inactive = malformedWindow || dashboard.assignmentStatus === 'not-current' || dashboard.shiftWindow === 'not-current' || notStarted || expired;
  const capabilities = dashboard.capabilityIds.map((id) => capabilityById(id, state)).filter(Boolean);
  const reasons = [
    inactive ? (malformedWindow ? 'The assignment window is inconsistent. The preview fails closed.' : notStarted ? 'The declared assignment window has not started. The preview fails closed.' : expired ? 'The declared assignment window expired.' : 'No current assignment is active.') : 'The assignment is self-declared or otherwise unverified by this preview.',
    'This is a configuration posture, not an EDENA assessment, credential check, or authority envelope.',
    'Role and capability selection personalize navigation; they do not create professional or institutional authority.',
    'This browser preview cannot install, connect, schedule, message, publish, or perform a clinical action.'
  ];
  const boundaries = [role.boundary, ...capabilities.map((item) => item.boundary), 'PHI and identifying records are prohibited. No patient-specific clinical decisions. Human review before external use.'];
  return {
    disposition: inactive ? 'Inactive' : 'Configured · review required',
    edena: 'Not evaluated',
    autonomy: 'A0 · no action',
    active: !inactive,
    title: dashboardTitle(dashboard, state),
    role: role.displayName,
    supporting: [],
    capabilities: capabilities.map((item) => item.displayName),
    assignment: labelFor(ASSIGNMENT_STATUSES, dashboard.assignmentStatus),
    reasons,
    boundaries: [...new Set(boundaries)]
  };
}

export function migrateLegacySetupState(legacy, now, idSuffix = 'legacy', currentState = null) {
  const normalizedLegacy = hasExactLegacyShape(legacy) ? normalizeLegacySetupState(legacy) : null;
  if (!normalizedLegacy || !validIso(normalizedLegacy.updatedAt) || !LEGACY_LANE_MAP[normalizedLegacy.postSetupLane]) return null;
  const mapping = LEGACY_LANE_MAP[normalizedLegacy.postSetupLane];
  const base = currentState === null ? createInitialState(now) : normalizeState(currentState);
  if (!base) return null;
  return addDashboard(base, {
    contextKey: 'personal',
    departmentKey: mapping.department,
    primaryRoleId: mapping.role,
    supportingRoleIds: [],
    capabilityIds: mapping.capabilities,
    assignmentStatus: 'not-current',
    shiftWindow: 'not-current'
  }, now, idSuffix).state;
}

export function exportState(state) {
  const normalized = normalizeState(state);
  if (!normalized) throw new Error('Cannot export invalid Switchboard state.');
  return JSON.stringify(normalized, null, 2) + '\n';
}

export function importState(text) {
  if (typeof text !== 'string' || text.length > 250000) throw new Error('Switchboard file is too large.');
  let parsed;
  try { parsed = JSON.parse(text); } catch { throw new Error('Choose a valid Nurse AI OS Switchboard JSON file.'); }
  const normalized = normalizeState(parsed);
  if (!normalized) throw new Error('The Switchboard file is invalid, outdated, or contains unsupported values.');
  return normalized;
}
