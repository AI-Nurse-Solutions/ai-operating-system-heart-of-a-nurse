/*
 * Nurse AI OS Client Care Portal — pure model.
 * No DOM, no network, no storage: everything here is deterministic and
 * testable from Node. The UI (portal.mjs) and data layer (portal-data.mjs)
 * consume these constants and functions.
 */

export const SCHEMA_VERSION = 1;
export const DEMO_STORAGE_KEY = 'naio.portal.demo.v1';

/* ---------- Vocabulary (PRD §5.2, §5.4, §5.5) ---------- */

export const LIFECYCLE_STAGES = Object.freeze([
  { value: 'getting-started', label: 'Getting Started' },
  { value: 'configuring', label: 'Configuring' },
  { value: 'operational', label: 'Operational' },
  { value: 'optimizing', label: 'Optimizing' }
]);

export const ACTION_CATEGORIES = Object.freeze([
  { value: 'maintain', label: 'Maintain', blurb: 'Updates, backups, permissions review, knowledge refresh, and system health checks.' },
  { value: 'improve', label: 'Improve', blurb: 'New workflows, skills, agents, dashboards, or integrations to consider.' },
  { value: 'learn', label: 'Learn', blurb: 'Education, practice exercises, and governance refreshers.' },
  { value: 'review', label: 'Review', blurb: 'Decisions or approvals required from you.' }
]);

export const ACTION_STATUSES = Object.freeze([
  { value: 'not-started', label: 'Not started' },
  { value: 'started', label: 'Started' },
  { value: 'complete', label: 'Complete' }
]);

export const ACTION_PRIORITIES = Object.freeze([
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' }
]);

export const CONVERSATION_CATEGORIES = Object.freeze([
  { value: 'setup', label: 'Setup' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'improvement', label: 'Improvement' },
  { value: 'training', label: 'Training' },
  { value: 'governance', label: 'Governance' },
  { value: 'other', label: 'Other' }
]);

export const CONVERSATION_STATUSES = Object.freeze([
  { value: 'new', label: 'New' },
  { value: 'in-review', label: 'In Review' },
  { value: 'waiting-for-client', label: 'Waiting for Client' },
  { value: 'answered', label: 'Answered' },
  { value: 'closed', label: 'Closed' }
]);

export const ROLES = Object.freeze(['client', 'admin', 'specialist']);

/* ---------- Governance text (PRD §10) ---------- */

export const TRANSPARENT_LIMITS_NOTICE =
  'For Nurse AI OS setup, education, maintenance, and improvement support only. ' +
  'Do not enter patient information or use this portal for urgent clinical or operational matters.';

export const NO_PHI_WARNING =
  'No patient information. Do not include patient names, dates of birth, medical record ' +
  'numbers, clinical notes, or anything that identifies a patient. Do not paste passwords, ' +
  'API keys, recovery codes, or authentication tokens. Browser checks are not exhaustive — ' +
  'you remain responsible for what you submit.';

export function labelFor(list, value) {
  const entry = list.find((item) => item.value === value);
  return entry ? entry.label : value;
}

/* ---------- Progress (PRD §5.2) ---------- */

export function computeProgress(milestones) {
  const items = (milestones || []).filter(Boolean);
  if (!items.length) return 0;
  const done = items.filter((m) => m.status === 'complete').length;
  return Math.round((done / items.length) * 100);
}

const PRIORITY_RANK = { high: 0, medium: 1, low: 2 };
const STATUS_RANK = { 'not-started': 0, started: 1, complete: 2 };

export function sortActions(actions) {
  return [...(actions || [])].sort((a, b) => {
    const statusDelta = (STATUS_RANK[a.status] ?? 0) - (STATUS_RANK[b.status] ?? 0);
    if (statusDelta) return statusDelta;
    const priorityDelta = (PRIORITY_RANK[a.priority] ?? 1) - (PRIORITY_RANK[b.priority] ?? 1);
    if (priorityDelta) return priorityDelta;
    const aDue = a.dueDate || '9999-12-31';
    const bDue = b.dueDate || '9999-12-31';
    return aDue < bDue ? -1 : aDue > bDue ? 1 : 0;
  });
}

export function topActions(actions, count = 3) {
  return sortActions((actions || []).filter((a) => a.status !== 'complete')).slice(0, count);
}

export function openConversations(conversations) {
  return (conversations || []).filter((c) => c.status !== 'closed' && c.status !== 'answered');
}

export function isOverdue(action, todayIso) {
  if (!action || !action.dueDate || action.status === 'complete') return false;
  return action.dueDate < todayIso;
}

/* ---------- Submission screening (PRD §10 — soft, client-side) ----------
 * These checks are a courtesy speed bump, not DLP. They flag the obvious
 * cases so a person can reconsider before submitting; server-side policy
 * and human review remain the real controls.
 */

const SCREEN_PATTERNS = [
  { re: /\b(mrn|medical record number)\b/i, reason: 'a medical record number reference' },
  { re: /\b(date of birth|\bdob\b)\b/i, reason: 'a date of birth reference' },
  { re: /\bpatient\s+(name|id|record|chart)\b/i, reason: 'patient-identifying language' },
  { re: /\bsk-[a-z0-9-]{8,}/i, reason: 'what looks like an API key' },
  { re: /\b(password|passcode|recovery code)\s*[:=]/i, reason: 'what looks like a password or recovery code' },
  { re: /\beyJ[A-Za-z0-9_-]{20,}/, reason: 'what looks like an authentication token' }
];

export function screenSubmission(text) {
  const value = String(text || '');
  const flags = [];
  for (const { re, reason } of SCREEN_PATTERNS) {
    if (re.test(value)) flags.push(reason);
  }
  return { ok: flags.length === 0, flags };
}

/* ---------- Demo workspace seed ----------
 * Used when portal/config.mjs has no Supabase project configured, so the
 * portal is fully reviewable on GitHub Pages without a backend. All content
 * is fictional and non-clinical.
 */

export function demoSeed() {
  return {
    schemaVersion: SCHEMA_VERSION,
    users: [
      { id: 'user-demo-client', name: 'Jordan Rivera', email: 'jordan@example.org', role: 'client', clientId: 'client-demo', active: true },
      { id: 'user-demo-admin', name: 'Robert Domondon', email: 'robert@example.org', role: 'admin', clientId: null, active: true }
    ],
    clients: [
      {
        id: 'client-demo',
        organization: 'Riverbend Nursing Education Cohort',
        stage: 'configuring',
        governanceTier: 'D0/D1 · Observe',
        configLabel: 'Nurse AI OS Community · browser-first',
        setupProfile:
          'Browser-first Community setup for a nurse-educator team. SOUL profiles completed. ' +
          'Starter Kit loaded. No local Hermes install yet. No PHI anywhere in scope.',
        lastReview: '2026-07-21',
        nextReview: '2026-08-18'
      }
    ],
    milestones: [
      { id: 'ms-1', clientId: 'client-demo', title: 'SOUL Quiz completed by core team', description: 'Each educator captured values, boundaries, and what stays human.', status: 'complete', completedAt: '2026-06-30', order: 1 },
      { id: 'ms-2', clientId: 'client-demo', title: 'Starter Kit loaded in browser AI', description: 'Team can run the safe lecture-notes workflow end to end.', status: 'complete', completedAt: '2026-07-14', order: 2 },
      { id: 'ms-3', clientId: 'client-demo', title: 'Governance boundaries agreed', description: 'No-PHI rule and review-every-result rule adopted in writing.', status: 'complete', completedAt: '2026-07-20', order: 3 },
      { id: 'ms-4', clientId: 'client-demo', title: 'First team workflow in weekly use', description: 'One bounded education workflow used in at least three sessions.', status: 'started', completedAt: null, order: 4 },
      { id: 'ms-5', clientId: 'client-demo', title: 'Optional Hermes decision', description: 'Decide whether the desktop Hermes path is worth adopting this term.', status: 'not-started', completedAt: null, order: 5 }
    ],
    reports: [
      {
        id: 'rep-1',
        clientId: 'client-demo',
        reportDate: '2026-07-21',
        summary: 'Setup is on track. The team moved from Getting Started to Configuring: profiles, Starter Kit, and governance boundaries are all in place. The next period is about habit, not new tools.',
        accomplishments: [
          'All five educators completed the SOUL Quiz and shared boundary summaries.',
          'Starter Kit loaded and verified in each person’s browser AI.',
          'Written no-PHI and human-review commitments adopted.'
        ],
        capabilities: ['Lecture-notes workflow', 'Case-free quiz-item drafting', 'Policy summary drafting'],
        risks: ['Weekly usage is uneven across the team; two educators have not run a workflow since setup week.'],
        nextPriorities: ['Run the lecture-notes workflow in every weekly prep session.', 'Nominate one workflow to standardize for the fall term.'],
        acknowledgeNote: 'Please confirm the fall-term pilot scope by the next review.',
        published: true
      }
    ],
    actions: [
      { id: 'act-1', clientId: 'client-demo', category: 'maintain', title: 'Monthly knowledge refresh', instructions: 'Re-read your SOUL summary and refresh the Starter Kit folder from the official download so drift does not accumulate.', priority: 'medium', owner: 'client', status: 'not-started', dueDate: '2026-08-11', link: '../starter-kit/', comment: '' },
      { id: 'act-2', clientId: 'client-demo', category: 'improve', title: 'Pilot the rubric-drafting workflow', instructions: 'Try the bounded rubric-drafting workflow on one non-clinical assignment and note where human judgment changed the output.', priority: 'high', owner: 'client', status: 'started', dueDate: '2026-08-08', link: '', comment: 'First run done with the pharmacology syllabus.' },
      { id: 'act-3', clientId: 'client-demo', category: 'learn', title: 'Governance refresher: five safety rules', instructions: 'Have each team member re-read the EDENA safety rules and bring one question to the next huddle.', priority: 'medium', owner: 'client', status: 'not-started', dueDate: '2026-08-15', link: '../start-here.html#safety', comment: '' },
      { id: 'act-4', clientId: 'client-demo', category: 'review', title: 'Approve fall-term pilot scope', instructions: 'Reply in the portal confirming which single workflow the team standardizes on for the fall term.', priority: 'high', owner: 'client', status: 'not-started', dueDate: '2026-08-18', link: '', comment: '' }
    ],
    conversations: [
      {
        id: 'conv-1',
        clientId: 'client-demo',
        subject: 'How should we phrase the no-PHI reminder for students?',
        category: 'governance',
        relatedId: 'act-3',
        status: 'answered',
        createdBy: 'user-demo-client',
        createdAt: '2026-07-24T15:04:00Z',
        updatedAt: '2026-07-25T13:30:00Z'
      }
    ],
    messages: [
      { id: 'msg-1', conversationId: 'conv-1', senderId: 'user-demo-client', body: 'We want a one-line reminder students see before any AI exercise. Is there approved wording?', aiAssisted: false, createdAt: '2026-07-24T15:04:00Z' },
      { id: 'msg-2', conversationId: 'conv-1', senderId: 'user-demo-admin', body: 'Yes — use the portal boundary line verbatim: no patient information, and a human reviews every result. Short, and it matches your governance kit. Happy to look at a draft slide if you post the text here.', aiAssisted: true, createdAt: '2026-07-25T13:30:00Z' }
    ],
    activity: [
      { id: 'evt-1', clientId: 'client-demo', actor: 'user-demo-admin', action: 'published progress report', recordType: 'report', recordId: 'rep-1', at: '2026-07-21T18:00:00Z' },
      { id: 'evt-2', clientId: 'client-demo', actor: 'user-demo-client', action: 'started action', recordType: 'action', recordId: 'act-2', at: '2026-07-28T16:12:00Z' }
    ]
  };
}

/* ---------- Demo AI draft ----------
 * Deterministic stand-in for the draft-with-ai edge function so the admin
 * flow is demonstrable without a backend or API key. Real drafting happens
 * server-side only (supabase/functions/draft-with-ai).
 */

export function demoDraft({ question, clientProfile }) {
  const firstLine = String(question || '').split('\n')[0].slice(0, 140);
  return [
    `Thanks for raising this — here is where I would start, given your current setup (${clientProfile || 'browser-first Community configuration'}).`,
    '',
    `On "${firstLine}": keep the change small and bounded. Pick one workflow, write down what success looks like, run it once with a human reviewing every result, and only then decide whether to standardize it.`,
    '',
    'Suggested next steps:',
    '1. Note the exact wording or workflow you want to change.',
    '2. Trial it once in a non-clinical context this week.',
    '3. Post the result in this thread so we can review it together.',
    '',
    'One clarifying question: do you want this to apply to the whole team, or just your own sessions for now?'
  ].join('\n');
}
