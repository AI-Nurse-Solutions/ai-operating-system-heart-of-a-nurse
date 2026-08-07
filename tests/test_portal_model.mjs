#!/usr/bin/env node
// Deterministic tests for the Client Care Portal pure model.

import assert from 'node:assert/strict';
import {
  LIFECYCLE_STAGES, ACTION_CATEGORIES, ACTION_STATUSES,
  CONVERSATION_CATEGORIES, CONVERSATION_STATUSES,
  TRANSPARENT_LIMITS_NOTICE, NO_PHI_WARNING,
  computeProgress, sortActions, topActions, openConversations,
  isOverdue, labelFor, screenSubmission, demoSeed, demoDraft
} from '../portal/portal-model.mjs';
import { DemoStore } from '../portal/portal-data.mjs';

const checks = [];
function test(name, fn) { checks.push([name, fn]); }

/* ---- vocabulary matches the PRD ---- */

test('lifecycle stages are the four PRD statuses', () => {
  assert.deepEqual(LIFECYCLE_STAGES.map((s) => s.label),
    ['Getting Started', 'Configuring', 'Operational', 'Optimizing']);
});

test('action plan categories are maintain/improve/learn/review', () => {
  assert.deepEqual(ACTION_CATEGORIES.map((c) => c.value),
    ['maintain', 'improve', 'learn', 'review']);
});

test('conversation statuses match the PRD five', () => {
  assert.deepEqual(CONVERSATION_STATUSES.map((s) => s.label),
    ['New', 'In Review', 'Waiting for Client', 'Answered', 'Closed']);
});

test('conversation categories match the PRD six', () => {
  assert.equal(CONVERSATION_CATEGORIES.length, 6);
  assert.ok(CONVERSATION_CATEGORIES.some((c) => c.value === 'governance'));
});

test('governance notices carry the required language', () => {
  assert.match(TRANSPARENT_LIMITS_NOTICE, /Do not enter patient information/);
  assert.match(TRANSPARENT_LIMITS_NOTICE, /urgent clinical or operational matters/);
  assert.match(NO_PHI_WARNING, /No patient information/);
  assert.match(NO_PHI_WARNING, /API keys/);
});

/* ---- progress and sorting ---- */

test('computeProgress handles empty, partial, and full', () => {
  assert.equal(computeProgress([]), 0);
  assert.equal(computeProgress(null), 0);
  const ms = (statuses) => statuses.map((status, i) => ({ id: String(i), status }));
  assert.equal(computeProgress(ms(['complete', 'complete', 'not-started', 'started'])), 50);
  assert.equal(computeProgress(ms(['complete'])), 100);
});

test('sortActions orders by status, then priority, then due date', () => {
  const actions = [
    { id: 'a', status: 'complete', priority: 'high', dueDate: '2026-01-01' },
    { id: 'b', status: 'not-started', priority: 'low', dueDate: '2026-01-01' },
    { id: 'c', status: 'not-started', priority: 'high', dueDate: '2026-02-01' },
    { id: 'd', status: 'not-started', priority: 'high', dueDate: '2026-01-15' },
    { id: 'e', status: 'started', priority: 'high', dueDate: null }
  ];
  assert.deepEqual(sortActions(actions).map((a) => a.id), ['d', 'c', 'b', 'e', 'a']);
});

test('topActions returns at most three open items', () => {
  const seed = demoSeed();
  const top = topActions(seed.actions);
  assert.ok(top.length <= 3);
  assert.ok(top.every((a) => a.status !== 'complete'));
});

test('overdue detection ignores complete actions', () => {
  assert.equal(isOverdue({ dueDate: '2026-01-01', status: 'not-started' }, '2026-02-01'), true);
  assert.equal(isOverdue({ dueDate: '2026-01-01', status: 'complete' }, '2026-02-01'), false);
  assert.equal(isOverdue({ dueDate: null, status: 'not-started' }, '2026-02-01'), false);
});

test('openConversations excludes answered and closed', () => {
  const list = openConversations([
    { id: '1', status: 'new' }, { id: '2', status: 'answered' },
    { id: '3', status: 'closed' }, { id: '4', status: 'waiting-for-client' }
  ]);
  assert.deepEqual(list.map((c) => c.id), ['1', '4']);
});

test('labelFor falls back to the raw value', () => {
  assert.equal(labelFor(ACTION_STATUSES, 'started'), 'Started');
  assert.equal(labelFor(ACTION_STATUSES, 'mystery'), 'mystery');
});

/* ---- submission screening ---- */

test('screening passes ordinary support questions', () => {
  assert.ok(screenSubmission('How do I refresh the Starter Kit for my team?').ok);
});

test('screening flags PHI-shaped and secret-shaped text', () => {
  assert.equal(screenSubmission('Patient name: J. Smith, MRN 12345').ok, false);
  assert.equal(screenSubmission('here is my key sk-ant-abc123def456').ok, false);
  assert.equal(screenSubmission('password: hunter2').ok, false);
  const token = screenSubmission('bearer eyJ' + 'A'.repeat(30));
  assert.equal(token.ok, false);
});

/* ---- demo seed integrity ---- */

test('demo seed is internally consistent and non-clinical', () => {
  const seed = demoSeed();
  const clientIds = new Set(seed.clients.map((c) => c.id));
  for (const collection of [seed.milestones, seed.reports, seed.actions, seed.conversations, seed.activity]) {
    for (const row of collection) assert.ok(clientIds.has(row.clientId), `orphan row ${row.id}`);
  }
  const conversationIds = new Set(seed.conversations.map((c) => c.id));
  for (const message of seed.messages) assert.ok(conversationIds.has(message.conversationId));
  const text = JSON.stringify(seed);
  for (const forbidden of ['MRN', 'date of birth', 'diagnos']) {
    assert.ok(!text.toLowerCase().includes(forbidden.toLowerCase()), `seed contains ${forbidden}`);
  }
  assert.ok(seed.users.some((u) => u.role === 'admin'));
  assert.ok(seed.users.some((u) => u.role === 'client'));
});

test('demo draft references the question and stays a draft', () => {
  const draft = demoDraft({ question: 'How do we standardize the rubric workflow?', clientProfile: 'Browser-first' });
  assert.match(draft, /rubric workflow/);
  assert.match(draft, /clarifying question/i);
});

/* ---- demo store behavior (no localStorage in Node) ---- */

test('demo store enforces role boundaries', async () => {
  const store = new DemoStore({ getItem: () => null, setItem: () => {} });
  await store.init();
  assert.equal(store.session(), null);

  await store.signInAs('client');
  const ws = await store.getWorkspace('client-demo');
  assert.equal(ws.client.id, 'client-demo');
  await assert.rejects(store.listClients(), /Admin access required/);
  await assert.rejects(store.createAction('client-demo', { title: 'x' }), /Admin access required/);

  await store.signInAs('admin');
  const clients = await store.listClients();
  assert.ok(clients.length >= 1);
  assert.ok('openActions' in clients[0] && 'openQuestions' in clients[0]);
});

test('demo store client flow: update action, ask question, get admin answer', async () => {
  const store = new DemoStore({ getItem: () => null, setItem: () => {} });
  await store.init();
  await store.signInAs('client');

  const updated = await store.updateActionStatus('act-1', 'started', 'On it this week');
  assert.equal(updated.status, 'started');

  const conversation = await store.createConversation({
    clientId: 'client-demo', subject: 'Test question', category: 'setup', body: 'How do I begin?'
  });
  assert.equal(conversation.status, 'new');

  await store.signInAs('admin');
  const { draft } = await store.draftWithAi(conversation.id);
  assert.ok(draft.length > 50);
  await store.addMessage(conversation.id, draft, { aiAssisted: true });
  const ws = await store.getWorkspace('client-demo');
  const thread = ws.messages.filter((m) => m.conversationId === conversation.id);
  assert.equal(thread.length, 2);
  assert.equal(thread[1].aiAssisted, true);
  assert.equal(ws.conversations.find((c) => c.id === conversation.id).status, 'answered');
  assert.ok(ws.activity.length >= 3, 'activity events recorded');
});

test('clients cannot label their own messages AI-assisted', async () => {
  const store = new DemoStore({ getItem: () => null, setItem: () => {} });
  await store.init();
  await store.signInAs('client');
  const message = await store.addMessage('conv-1', 'Follow-up question', { aiAssisted: true });
  assert.equal(message.aiAssisted, false);
});

/* ---- runner ---- */

let failed = 0;
for (const [name, fn] of checks) {
  try {
    await fn();
    console.log(`ok    ${name}`);
  } catch (err) {
    failed += 1;
    console.error(`FAIL  ${name}\n      ${err.message}`);
  }
}
console.log(`\n${checks.length - failed}/${checks.length} portal model tests passed`);
if (failed) process.exit(1);
