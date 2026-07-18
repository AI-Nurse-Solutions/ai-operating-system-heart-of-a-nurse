import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import Ajv2020 from 'ajv/dist/2020.js';
import { addDashboard, addLocalRole, createInitialState, normalizeState } from '../switchboard/switchboard-model.mjs';

const readJson = async (path) => JSON.parse(await readFile(new URL(path, import.meta.url), 'utf8'));
const stateSchema = await readJson('../switchboard/schema/switchboard.schema.json');
const registrySchema = await readJson('../switchboard/schema/role-registry-entry.schema.json');
const registry = await readJson('../switchboard/data/role-registry.json');
const ajv = new Ajv2020({ allErrors: true, strict: true, formats: { 'date-time': true } });
const validateState = ajv.compile(stateSchema);
const validateRegistryEntry = ajv.compile(registrySchema);

for (const entry of registry.entries) {
  assert.equal(validateRegistryEntry(entry), true, `${entry.id}: ${ajv.errorsText(validateRegistryEntry.errors)}`);
}
const elevatedRegistryEntry = structuredClone(registry.entries[0]);
elevatedRegistryEntry.autonomyCeiling = 'A2';
assert.equal(validateRegistryEntry(elevatedRegistryEntry), false, 'preview registry schema must reject autonomy above A0');

let state = createInitialState('2026-07-17T00:00:00Z');
state = addDashboard(state, {
  contextKey: 'community-a',
  departmentKey: 'community',
  primaryRoleId: 'nurse-community-organizer-developer',
  supportingRoleIds: [],
  capabilityIds: ['organize', 'discover', 'future', 'build', 'communicate', 'govern'],
  assignmentStatus: 'community-assigned-unverified',
  shiftWindow: '12-hours'
}, '2026-07-17T00:00:00Z', 'community').state;
state = addLocalRole(state, { displayName: 'Local Navigation Steward', kind: 'professional-community-role' }, '2026-07-17T00:01:00Z', 'local').state;
assert.equal(validateState(state), true, ajv.errorsText(validateState.errors));

const invalidFixedWindow = structuredClone(state);
invalidFixedWindow.dashboards[0].assignmentExpiresAt = null;
assert.equal(validateState(invalidFixedWindow), false, 'schema must reject fixed windows without expiry');

const invalidSupportingRole = structuredClone(state);
invalidSupportingRole.dashboards[0].supportingRoleIds = ['staff-nurse'];
assert.equal(validateState(invalidSupportingRole), false, 'schema must reject supporting-role composition in the preview');

const wrongDuration = structuredClone(state);
wrongDuration.dashboards[0].assignmentExpiresAt = '2026-07-17T07:00:00.000Z';
assert.equal(validateState(wrongDuration), true, 'portable schema intentionally validates timestamp structure only');
assert.equal(normalizeState(wrongDuration), null, 'runtime must reject noncanonical fixed-window duration');

const danglingActiveDashboard = structuredClone(state);
danglingActiveDashboard.activeDashboardId = 'dashboard-does-not-exist';
assert.equal(validateState(danglingActiveDashboard), true, 'portable schema cannot express cross-array referential integrity');
assert.equal(normalizeState(danglingActiveDashboard), null, 'runtime must reject dangling active dashboard references');

const duplicateDashboardId = structuredClone(state);
const duplicate = structuredClone(duplicateDashboardId.dashboards[0]);
duplicate.updatedAt = '2026-07-17T00:02:00.000Z';
duplicateDashboardId.dashboards.push(duplicate);
assert.equal(validateState(duplicateDashboardId), true, 'portable schema uniqueItems compares complete objects, not one property');
assert.equal(normalizeState(duplicateDashboardId), null, 'runtime must reject duplicate dashboard identifiers');

console.log(`SWITCHBOARD_SCHEMA_OK entries=${registry.entries.length}`);
