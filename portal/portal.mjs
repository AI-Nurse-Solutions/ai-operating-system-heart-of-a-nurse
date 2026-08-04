/*
 * Nurse AI OS Client Care Portal — UI.
 * Hash-routed single-page app over portal-data.mjs. All rendering happens
 * after sign-in; the static page carries no client records.
 */

import {
  LIFECYCLE_STAGES, ACTION_CATEGORIES, ACTION_STATUSES, ACTION_PRIORITIES,
  CONVERSATION_CATEGORIES, CONVERSATION_STATUSES,
  NO_PHI_WARNING, labelFor, computeProgress, sortActions, topActions,
  openConversations, isOverdue, screenSubmission
} from './portal-model.mjs';
import { createStore } from './portal-data.mjs';

const app = document.getElementById('portal-app');
const navEl = document.getElementById('portal-nav');

let store = null;
let notice = null; // { kind: 'info' | 'error', text }

const esc = (value) => String(value ?? '')
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

/* Only http(s), relative paths, and fragments may render as hrefs. */
const safeHref = (value) => {
  const raw = String(value || '').trim();
  return /^(https?:|\/|\.\/|\.\.\/|#)/i.test(raw) ? raw : '';
};

const todayIso = () => new Date().toISOString().slice(0, 10);

/* Store writes can fail in Supabase mode (network, RLS). Funnel every write
 * through here so failures surface as a notice instead of a silent success. */
async function tryStore(fn) {
  try {
    return await fn();
  } catch (err) {
    setNotice('error', `That didn't save: ${err.message}`);
    render();
    return null;
  }
}

function setNotice(kind, text) {
  notice = text ? { kind, text } : null;
}

function noticeHtml() {
  if (!notice) return '';
  const kind = notice.kind === 'error' ? 'portal-alert-error' : 'portal-alert-info';
  return `<div class="portal-alert ${kind}" role="status">${esc(notice.text)}</div>`;
}

function badge(kindClass, label) {
  return `<span class="badge ${kindClass}">${esc(label)}</span>`;
}

function options(list, selected) {
  return list.map((item) =>
    `<option value="${esc(item.value)}"${item.value === selected ? ' selected' : ''}>${esc(item.label)}</option>`
  ).join('');
}

function noPhiCallout() {
  return `<p class="no-phi-callout"><strong>Before you type:</strong> ${esc(NO_PHI_WARNING)}</p>`;
}

function formatDate(value) {
  if (!value) return '—';
  return String(value).slice(0, 10);
}

/* ---------- Routing ---------- */

function route() {
  const raw = location.hash.replace(/^#\/?/, '');
  const parts = raw.split('/').filter(Boolean);
  return { parts, raw };
}

function go(hash) {
  if (location.hash === hash) render();
  else location.hash = hash;
}

function homeHash(user) {
  return user.role === 'admin' ? '#/admin' : '#/home';
}

/* ---------- Boot ---------- */

async function init() {
  app.innerHTML = '<div class="portal-card"><p>Loading the Care Portal…</p></div>';
  try {
    store = await createStore();
  } catch (err) {
    app.innerHTML = `<div class="portal-card"><h1>Portal unavailable</h1><p>${esc(err.message)}</p></div>`;
    return;
  }
  window.addEventListener('hashchange', () => render());
  render();
}

function session() {
  return store ? store.session() : null;
}

/* ---------- Navigation ---------- */

function renderNav() {
  const current = session();
  if (!current) {
    navEl.innerHTML = '<a href="../index.html">Back to nurse-ai-os.org</a>';
    return;
  }
  const { user } = current;
  const links = user.role === 'admin'
    ? [['#/admin', 'Clients']]
    : [
        ['#/home', 'Home'],
        ['#/reports', 'Reports'],
        ['#/actions', 'Action plan'],
        ['#/messages', 'Messages'],
        ['#/profile', 'Profile']
      ];
  const activeHash = `#/${route().parts[0] || ''}`;
  navEl.innerHTML = links.map(([hash, label]) =>
    `<a href="${hash}"${hash === activeHash ? ' aria-current="page"' : ''}>${esc(label)}</a>`
  ).join('') +
  `<span class="portal-nav-user">${esc(user.name)}</span>` +
  '<button type="button" data-signout>Sign out</button>';
  navEl.querySelector('[data-signout]').addEventListener('click', async () => {
    await store.signOut();
    setNotice('info', 'You are signed out.');
    go('#/signin');
  });
}

/* ---------- Render dispatcher ---------- */

async function render() {
  renderNav();
  const current = session();
  const { parts } = route();
  const view = parts[0] || '';

  if (!current) {
    renderSignIn();
    return;
  }
  const { user } = current;

  try {
    if (!view || view === 'signin') return go(homeHash(user));
    if (user.role === 'admin') {
      if (view === 'admin' && parts[1] === 'client' && parts[2]) return await renderAdminClient(parts[2]);
      if (view === 'admin') return await renderAdminList();
      if (view === 'conversation' && parts[1]) return await renderConversation(parts[1]);
      return go('#/admin');
    }
    const clientId = user.clientId;
    if (!clientId) {
      app.innerHTML = '<div class="portal-card"><h1>No workspace yet</h1><p>Your account is not linked to a client workspace. Contact support@nurse-ai-os.org.</p></div>';
      return;
    }
    if (view === 'home') return await renderHome(clientId, user);
    if (view === 'reports') return await renderReports(clientId);
    if (view === 'actions') return await renderActions(clientId);
    if (view === 'messages' && parts[1] === 'new') return await renderNewQuestion(clientId, parts.slice(2).join('/'));
    if (view === 'messages') return await renderMessages(clientId);
    if (view === 'conversation' && parts[1]) return await renderConversation(parts[1]);
    if (view === 'profile') return await renderProfile(clientId, user);
    return go('#/home');
  } catch (err) {
    app.innerHTML = `<div class="portal-card"><h1>Something went wrong</h1><p>${esc(err.message)}</p>
      <p><a class="btn btn-secondary" href="${homeHash(user)}">Back to your home screen</a></p></div>`;
  }
}

/* ---------- Demo ribbon ---------- */

function demoRibbon() {
  if (!store || store.mode !== 'demo') return '';
  return `<div class="demo-ribbon"><span><strong>Demo workspace.</strong> Fictional data, saved only in this browser. No backend is connected.</span>
    <span class="portal-actions-row">
      <button type="button" data-demo-role="client">View as client</button>
      <button type="button" data-demo-role="admin">View as Robert (admin)</button>
      <button type="button" data-demo-reset>Reset demo</button>
    </span></div>`;
}

function bindDemoRibbon() {
  app.querySelectorAll('[data-demo-role]').forEach((btn) => btn.addEventListener('click', async () => {
    const { user } = await store.signInAs(btn.dataset.demoRole);
    setNotice('info', `Now viewing as ${user.name} (${user.role}).`);
    go(homeHash(user));
  }));
  const reset = app.querySelector('[data-demo-reset]');
  if (reset) reset.addEventListener('click', () => {
    store.reset();
    setNotice('info', 'Demo workspace reset.');
    go('#/signin');
  });
}

/* ---------- Sign in ---------- */

function renderSignIn() {
  if (store.mode === 'demo') {
    app.innerHTML = `${noticeHtml()}
      <div class="portal-card">
        <p class="eyebrow">Client Care Portal</p>
        <h1>Preview the portal</h1>
        <p>No backend is configured on this deployment, so the portal runs as a <strong>browser-local demo</strong> with fictional data. Pick a seat to explore both sides of the experience.</p>
        <div class="portal-actions-row">
          <button class="btn btn-primary" type="button" data-demo-role="client">Enter as demo client →</button>
          <button class="btn btn-secondary" type="button" data-demo-role="admin">Enter as Robert (admin)</button>
        </div>
        <p class="portal-muted" style="margin-top:1rem">On the production deployment this screen is a passwordless email sign-in: you enter your invited email address and receive a secure one-time link. See <code>portal/README.md</code> for setup.</p>
      </div>`;
    app.querySelectorAll('[data-demo-role]').forEach((btn) => btn.addEventListener('click', async () => {
      const { user } = await store.signInAs(btn.dataset.demoRole);
      setNotice('info', `Signed in as ${user.name} (${user.role}) — demo data only.`);
      go(homeHash(user));
    }));
    notice = null;
    return;
  }

  app.innerHTML = `${noticeHtml()}
    <div class="portal-card" style="max-width:32rem;margin:2rem auto;">
      <p class="eyebrow">Client Care Portal</p>
      <h1>Sign in</h1>
      <p>Enter the email address your Nurse AI OS workspace invitation was sent to. We'll email you a secure one-time sign-in link — no password to remember.</p>
      <form class="portal-form" id="signin-form">
        <label>Email address
          <input type="email" name="email" required autocomplete="email" placeholder="you@organization.org">
        </label>
        <div class="portal-actions-row">
          <button class="btn btn-primary" type="submit">Email me a sign-in link →</button>
        </div>
      </form>
      <p class="portal-muted" style="margin-top:1rem">Access is by invitation. If you need an account, write to <a href="mailto:robert@nurse-ai-os.org">robert@nurse-ai-os.org</a>.</p>
    </div>`;
  notice = null;
  const form = app.querySelector('#signin-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const email = form.elements.email.value.trim();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      await store.signInWithEmail(email);
      setNotice('info', `Check ${email} for your sign-in link. It expires shortly, so use it soon.`);
    } catch (err) {
      setNotice('error', `Could not send the link: ${err.message}`);
    }
    render();
  });
}

/* ---------- Client: home ---------- */

async function renderHome(clientId, user) {
  const ws = await store.getWorkspace(clientId);
  const progress = computeProgress(ws.milestones);
  const next = topActions(ws.actions, 3);
  const open = openConversations(ws.conversations);
  const answered = ws.conversations.filter((c) => c.status === 'answered').slice(0, 3);

  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head">
      <div>
        <p class="eyebrow">Welcome back, ${esc(String(user.name || '').split(' ')[0] || 'there')}</p>
        <h1>${esc(ws.client.organization)}</h1>
      </div>
      ${badge('badge-stage', labelFor(LIFECYCLE_STAGES, ws.client.stage))}
    </div>
    <div class="portal-grid">
      <section class="portal-card" aria-labelledby="setup-health-title">
        <h2 id="setup-health-title">Setup health</h2>
        <p class="portal-muted">${esc(ws.client.configLabel || 'Nurse AI OS')}</p>
        <div class="progress-meter" role="img" aria-label="Setup progress ${progress} percent">
          <span style="width:${progress}%"></span>
        </div>
        <p><strong>${progress}%</strong> of milestones complete</p>
        <ul class="portal-list">
          ${ws.milestones.map((m) => `<li class="portal-list-row"><span>${esc(m.title)}</span>${badge(`badge-action-${esc(m.status)}`, labelFor(ACTION_STATUSES, m.status))}</li>`).join('') || '<li class="portal-empty">No milestones yet.</li>'}
        </ul>
        <p class="portal-list-meta">
          <span>Last review: ${esc(formatDate(ws.client.lastReview))}</span>
          <span>Next review: ${esc(formatDate(ws.client.nextReview))}</span>
          ${ws.client.governanceTier ? `<span>Governance: ${esc(ws.client.governanceTier)}</span>` : ''}
        </p>
      </section>
      <section class="portal-card" aria-labelledby="next-actions-title">
        <h2 id="next-actions-title">Recommended next actions</h2>
        <ul class="portal-list">
          ${next.map((a) => `<li>
              <div class="portal-list-row"><h3>${esc(a.title)}</h3>${badge(`badge-priority-${esc(a.priority)}`, labelFor(ACTION_PRIORITIES, a.priority))}</div>
              <p class="portal-list-meta"><span>${esc(labelFor(ACTION_CATEGORIES, a.category))}</span><span>Due ${esc(formatDate(a.dueDate))}</span>${isOverdue(a, todayIso()) ? badge('badge-overdue', 'Overdue') : ''}</p>
            </li>`).join('') || '<li class="portal-empty">Nothing waiting on you — nicely done.</li>'}
        </ul>
        <p><a class="btn btn-secondary btn-sm" href="#/actions">Open the full action plan →</a></p>
      </section>
      <section class="portal-card" aria-labelledby="questions-title">
        <h2 id="questions-title">Questions &amp; answers</h2>
        <h3 style="font-size:.95rem">Open</h3>
        <ul class="portal-list">
          ${open.map((c) => `<li class="portal-list-row"><a href="#/conversation/${esc(c.id)}">${esc(c.subject)}</a>${badge(`badge-status-${esc(c.status)}`, labelFor(CONVERSATION_STATUSES, c.status))}</li>`).join('') || '<li class="portal-empty">No open questions.</li>'}
        </ul>
        <h3 style="font-size:.95rem">Recently answered</h3>
        <ul class="portal-list">
          ${answered.map((c) => `<li class="portal-list-row"><a href="#/conversation/${esc(c.id)}">${esc(c.subject)}</a>${badge('badge-status-answered', 'Answered')}</li>`).join('') || '<li class="portal-empty">Nothing answered yet.</li>'}
        </ul>
        <p><a class="btn btn-primary btn-sm" href="#/messages/new">Ask a question →</a></p>
      </section>
    </div>`;
  notice = null;
  bindDemoRibbon();
}

/* ---------- Client: reports ---------- */

function reportCard(report) {
  const list = (items) => (items || []).map((item) => `<li>${esc(item)}</li>`).join('');
  return `<article class="portal-card">
    <div class="portal-page-head"><h2>Progress report</h2><span class="portal-muted">${esc(formatDate(report.reportDate))}</span></div>
    <p>${esc(report.summary)}</p>
    ${report.accomplishments?.length ? `<h3>Accomplishments since last review</h3><ul>${list(report.accomplishments)}</ul>` : ''}
    ${report.capabilities?.length ? `<h3>Capabilities enabled</h3><ul>${list(report.capabilities)}</ul>` : ''}
    ${report.risks?.length ? `<h3>Gaps &amp; risks</h3><ul>${list(report.risks)}</ul>` : ''}
    ${report.nextPriorities?.length ? `<h3>Priorities for the next period</h3><ul>${list(report.nextPriorities)}</ul>` : ''}
    ${report.acknowledgeNote ? `<p class="no-phi-callout"><strong>Needs your acknowledgment:</strong> ${esc(report.acknowledgeNote)} <a href="#/messages/new">Reply in Messages →</a></p>` : ''}
  </article>`;
}

async function renderReports(clientId) {
  const ws = await store.getWorkspace(clientId);
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Progress reports</h1><span class="portal-muted">${ws.reports.length} published</span></div>
    ${ws.reports.map(reportCard).join('') || '<div class="portal-card portal-empty">No reports published yet. Your first report arrives after your kickoff review.</div>'}`;
  notice = null;
  bindDemoRibbon();
}

/* ---------- Client: action plan ---------- */

function actionItem(action, editable) {
  const overdue = isOverdue(action, todayIso());
  return `<li data-action-id="${esc(action.id)}">
    <div class="portal-list-row">
      <h3>${esc(action.title)}</h3>
      <span class="portal-list-meta">
        ${badge(`badge-priority-${esc(action.priority)}`, labelFor(ACTION_PRIORITIES, action.priority))}
        ${badge(`badge-action-${esc(action.status)}`, labelFor(ACTION_STATUSES, action.status))}
        ${overdue ? badge('badge-overdue', 'Overdue') : ''}
      </span>
    </div>
    <p>${esc(action.instructions)}</p>
    <p class="portal-list-meta">
      <span>Owner: ${esc(action.owner)}</span>
      <span>Due ${esc(formatDate(action.dueDate))}</span>
      ${safeHref(action.link) ? `<a href="${esc(safeHref(action.link))}" rel="noopener noreferrer">Supporting link ↗</a>` : ''}
    </p>
    ${editable ? `<form class="portal-form" data-action-form>
        <div class="portal-form-row">
          <label>Status
            <select name="status">${options(ACTION_STATUSES, action.status)}</select>
          </label>
          <label>Comment <span class="portal-muted">(no patient information)</span>
            <input name="comment" value="${esc(action.comment || '')}" placeholder="Optional note for Robert">
          </label>
        </div>
        <div class="portal-actions-row"><button class="btn btn-secondary btn-sm" type="submit">Save update</button>
        <a class="btn btn-quiet btn-sm" href="#/messages/new/${esc(action.id)}">Ask about this →</a></div>
      </form>` : ''}
  </li>`;
}

async function renderActions(clientId) {
  const ws = await store.getWorkspace(clientId);
  const sorted = sortActions(ws.actions);
  const groups = ACTION_CATEGORIES.map((cat) => ({ cat, items: sorted.filter((a) => a.category === cat.value) }));
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Maintenance &amp; improvement plan</h1></div>
    ${groups.map(({ cat, items }) => `<section class="portal-card" aria-label="${esc(cat.label)} actions">
        <h2>${esc(cat.label)}</h2>
        <p class="portal-muted">${esc(cat.blurb)}</p>
        <ul class="portal-list">${items.map((a) => actionItem(a, true)).join('') || '<li class="portal-empty">Nothing here right now.</li>'}</ul>
      </section>`).join('')}`;
  notice = null;
  bindDemoRibbon();
  app.querySelectorAll('[data-action-form]').forEach((form) => form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const actionId = form.closest('[data-action-id]').dataset.actionId;
    const comment = form.elements.comment.value;
    if (!screenGate(form, comment)) return;
    const saved = await tryStore(() => store.updateActionStatus(actionId, form.elements.status.value, comment));
    if (!saved) return;
    setNotice('info', 'Action updated.');
    render();
  }));
}

/* The screening speed bump: a flagged submission is blocked once and shown a
 * warning; only re-submitting the *same* text passes. Editing the text after
 * the warning re-screens it from scratch. */
function screenGate(form, text) {
  const screen = screenSubmission(text);
  if (screen.ok) return true;
  if (form.dataset.confirmedFor === text) return true;
  form.dataset.confirmedFor = text;
  alertScreen(form, screen);
  return false;
}

function alertScreen(form, screen) {
  let warning = form.querySelector('.screen-warning');
  if (!warning) {
    warning = document.createElement('p');
    warning.className = 'screen-warning';
    warning.setAttribute('role', 'alert');
    form.prepend(warning);
  }
  warning.textContent =
    `Hold on — this text contains ${screen.flags.join(' and ')}. This portal must never hold patient information or secrets. ` +
    'Edit the text, or submit again to confirm it is safe.';
}

/* ---------- Client: messages ---------- */

async function renderMessages(clientId) {
  const ws = await store.getWorkspace(clientId);
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Messages</h1><a class="btn btn-primary btn-sm" href="#/messages/new">Ask a question →</a></div>
    <div class="portal-card">
      <ul class="portal-list">
        ${ws.conversations.map((c) => `<li>
            <div class="portal-list-row">
              <h3><a href="#/conversation/${esc(c.id)}">${esc(c.subject)}</a></h3>
              ${badge(`badge-status-${esc(c.status)}`, labelFor(CONVERSATION_STATUSES, c.status))}
            </div>
            <p class="portal-list-meta"><span>${esc(labelFor(CONVERSATION_CATEGORIES, c.category))}</span><span>Updated ${esc(formatDate(c.updatedAt))}</span></p>
          </li>`).join('') || '<li class="portal-empty">No conversations yet. Questions about setup, maintenance, training, or governance all belong here.</li>'}
      </ul>
    </div>`;
  notice = null;
  bindDemoRibbon();
}

async function renderNewQuestion(clientId, relatedId) {
  const ws = await store.getWorkspace(clientId);
  const openActions = ws.actions.filter((a) => a.status !== 'complete');
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Ask a question</h1><a class="btn btn-quiet btn-sm" href="#/messages">← Back to messages</a></div>
    <div class="portal-card">
      ${noPhiCallout()}
      <form class="portal-form" id="question-form" style="margin-top:.9rem">
        <label>Subject
          <input name="subject" required maxlength="200" placeholder="One line: what do you need?">
        </label>
        <div class="portal-form-row">
          <label>Category
            <select name="category">${options(CONVERSATION_CATEGORIES, 'setup')}</select>
          </label>
          <label>Related action <span class="portal-muted">(optional)</span>
            <select name="related">
              <option value="">None</option>
              ${openActions.map((a) => `<option value="${esc(a.id)}"${a.id === relatedId ? ' selected' : ''}>${esc(a.title)}</option>`).join('')}
            </select>
          </label>
        </div>
        <label>Your question
          <textarea name="body" required placeholder="Describe what you're trying to do, what happened, and what you expected. No patient information, no passwords or keys."></textarea>
        </label>
        <div class="portal-actions-row"><button class="btn btn-primary" type="submit">Submit question →</button></div>
      </form>
    </div>`;
  notice = null;
  bindDemoRibbon();
  const form = app.querySelector('#question-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const subject = form.elements.subject.value.trim();
    const body = form.elements.body.value.trim();
    if (!screenGate(form, `${subject}\n${body}`)) return;
    const conversation = await tryStore(() => store.createConversation({
      clientId, subject, body,
      category: form.elements.category.value,
      relatedId: form.elements.related.value || null
    }));
    if (!conversation) return;
    setNotice('info', 'Question submitted. You will see the reply here, in this thread.');
    go(`#/conversation/${conversation.id}`);
  });
}

/* ---------- Shared: conversation thread ---------- */

async function renderConversation(conversationId) {
  const { user } = session();
  const isAdmin = user.role === 'admin';

  // Resolve the conversation through the viewer's workspace so access
  // control stays in the data layer.
  const clientId = isAdmin
    ? await store.getConversationClientId(conversationId)
    : user.clientId;
  const ws = await store.getWorkspace(clientId);
  const conversation = ws.conversations.find((c) => c.id === conversationId);
  if (!conversation) throw new Error('Conversation not found.');

  const thread = ws.messages
    .filter((m) => m.conversationId === conversationId)
    .sort((a, b) => (a.createdAt < b.createdAt ? -1 : 1));
  const related = conversation.relatedId ? ws.actions.find((a) => a.id === conversation.relatedId) : null;
  const backHash = isAdmin ? `#/admin/client/${ws.client.id}` : '#/messages';

  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head">
      <div>
        <p class="eyebrow">${esc(labelFor(CONVERSATION_CATEGORIES, conversation.category))}${related ? ` · about “${esc(related.title)}”` : ''}</p>
        <h1>${esc(conversation.subject)}</h1>
      </div>
      ${badge(`badge-status-${esc(conversation.status)}`, labelFor(CONVERSATION_STATUSES, conversation.status))}
    </div>
    <p><a class="btn btn-quiet btn-sm" href="${backHash}">← Back</a></p>
    <div class="portal-card">
      <div class="thread">
        ${thread.map((m) => {
          const sender = store.userName(m.senderId);
          const fromAdmin = isAdmin ? m.senderId === user.id : m.senderId !== user.id;
          return `<article class="thread-msg${fromAdmin ? ' is-admin' : ''}">
            <header><strong>${esc(sender)}</strong><span>${esc(formatDate(m.createdAt))}</span>${m.aiAssisted ? badge('badge-ai', 'AI-assisted · human approved') : ''}</header>
            <p>${esc(m.body)}</p>
          </article>`;
        }).join('') || '<p class="portal-empty">No messages yet.</p>'}
      </div>
      ${conversation.status === 'closed' ? '<p class="portal-muted">This conversation is closed. Open a new question if you need more help.</p>' : renderReplyForm(isAdmin, conversation)}
    </div>`;
  notice = null;
  bindDemoRibbon();
  bindReplyForm(conversation, isAdmin);
}

function renderReplyForm(isAdmin, conversation) {
  return `${noPhiCallout()}
    <form class="portal-form" id="reply-form" style="margin-top:.9rem">
      <label>${isAdmin ? 'Your reply (you approve and send — drafts are never sent automatically)' : 'Continue the thread'}
        <textarea name="body" required placeholder="${isAdmin ? 'Write or draft a response, then review before sending.' : 'Add details or follow up. No patient information.'}"></textarea>
      </label>
      ${isAdmin ? `<div class="portal-form-row">
          <label>Mark thread as
            <select name="status">${options(CONVERSATION_STATUSES.filter((s) => s.value !== 'new'), 'answered')}</select>
          </label>
          <label style="align-self:end"><span class="portal-actions-row"><input type="checkbox" name="aiAssisted" style="width:auto"> Label reply as AI-assisted</span></label>
        </div>` : ''}
      <div class="portal-actions-row">
        ${isAdmin ? '<button class="btn btn-secondary" type="button" data-draft-ai>Draft with AI</button>' : ''}
        <button class="btn btn-primary" type="submit">${isAdmin ? 'Approve &amp; send reply →' : 'Send →'}</button>
        <span class="portal-muted" data-draft-status></span>
      </div>
    </form>`;
}

function bindReplyForm(conversation, isAdmin) {
  const form = app.querySelector('#reply-form');
  if (!form) return;

  const draftButton = form.querySelector('[data-draft-ai]');
  if (draftButton) draftButton.addEventListener('click', async () => {
    const statusEl = form.querySelector('[data-draft-status]');
    draftButton.disabled = true;
    statusEl.textContent = 'Drafting…';
    try {
      const { draft } = await store.draftWithAi(conversation.id);
      form.elements.body.value = draft;
      form.elements.aiAssisted.checked = true;
      statusEl.textContent = 'Draft ready — review and edit before sending.';
    } catch (err) {
      statusEl.textContent = `Draft failed: ${err.message}`;
    }
    draftButton.disabled = false;
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = form.elements.body.value.trim();
    if (!screenGate(form, body)) return;
    const sent = await tryStore(async () => {
      const message = await store.addMessage(conversation.id, body, {
        aiAssisted: isAdmin ? form.elements.aiAssisted.checked : false
      });
      if (isAdmin) await store.setConversationStatus(conversation.id, form.elements.status.value);
      return message;
    });
    if (!sent) return;
    setNotice('info', isAdmin ? 'Reply sent to the client.' : 'Message sent.');
    render();
  });
}

/* ---------- Client: profile ---------- */

async function renderProfile(clientId, user) {
  const ws = await store.getWorkspace(clientId);
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Your profile</h1></div>
    <div class="portal-grid">
      <section class="portal-card">
        <h2>Account</h2>
        <ul class="portal-list">
          <li class="portal-list-row"><span>Name</span><strong>${esc(user.name)}</strong></li>
          <li class="portal-list-row"><span>Email</span><strong>${esc(user.email)}</strong></li>
          <li class="portal-list-row"><span>Role</span><strong>${esc(user.role)}</strong></li>
          <li class="portal-list-row"><span>Workspace</span><strong>${esc(ws.client.organization)}</strong></li>
        </ul>
        <p class="portal-muted">To change your name or email, ask in <a href="#/messages/new">Messages</a>.</p>
      </section>
      <section class="portal-card">
        <h2>Approved setup summary</h2>
        <p>${esc(ws.client.setupProfile || 'No setup summary recorded yet.')}</p>
        <p class="portal-muted">This is the only context shared with the AI drafting assistant when Robert prepares an answer for you. It never includes patient data — the portal holds none.</p>
      </section>
    </div>`;
  notice = null;
  bindDemoRibbon();
}

/* ---------- Admin: client list ---------- */

async function renderAdminList() {
  const clients = await store.listClients();
  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <div class="portal-page-head"><h1>Client portfolio</h1><span class="portal-muted">${clients.length} client${clients.length === 1 ? '' : 's'}</span></div>
    <div class="portal-card">
      <form class="portal-form-row" id="client-filter">
        <label class="portal-form" style="display:grid;gap:.25rem;font-weight:600;font-size:.93rem">Stage
          <select name="stage"><option value="">All stages</option>${options(LIFECYCLE_STAGES, '')}</select>
        </label>
        <label class="portal-form" style="display:grid;gap:.25rem;font-weight:600;font-size:.93rem">Search
          <input name="query" placeholder="Organization name">
        </label>
      </form>
      <ul class="portal-list" id="client-rows">
        ${clients.map((c) => `<li data-stage="${esc(c.stage)}" data-name="${esc(c.organization.toLowerCase())}">
            <div class="portal-list-row">
              <h3><a href="#/admin/client/${esc(c.id)}">${esc(c.organization)}</a></h3>
              ${badge('badge-stage', labelFor(LIFECYCLE_STAGES, c.stage))}
            </div>
            <p class="portal-list-meta">
              <span>${c.openActions} open action${c.openActions === 1 ? '' : 's'}</span>
              <span>${c.openQuestions} open question${c.openQuestions === 1 ? '' : 's'}</span>
              <span>Next review ${esc(formatDate(c.nextReview))}</span>
            </p>
          </li>`).join('') || '<li class="portal-empty">No clients yet — create the first one below.</li>'}
      </ul>
    </div>
    <div class="portal-card">
      <h2>New client</h2>
      <form class="portal-form" id="new-client-form">
        <div class="portal-form-row">
          <label>Organization or client name
            <input name="organization" required placeholder="e.g. Lakeside Nurse Residency">
          </label>
          <label>Stage
            <select name="stage">${options(LIFECYCLE_STAGES, 'getting-started')}</select>
          </label>
        </div>
        <div class="portal-actions-row"><button class="btn btn-primary" type="submit">Create client →</button></div>
      </form>
      <p class="portal-muted">Invite the client's user account from the Supabase dashboard (or your invite flow) and link it to this workspace; see <code>portal/README.md</code>.</p>
    </div>`;
  notice = null;
  bindDemoRibbon();

  const filter = app.querySelector('#client-filter');
  const applyFilter = () => {
    const stage = filter.elements.stage.value;
    const query = filter.elements.query.value.trim().toLowerCase();
    app.querySelectorAll('#client-rows > li').forEach((row) => {
      const show = (!stage || row.dataset.stage === stage) && (!query || row.dataset.name.includes(query));
      row.style.display = show ? '' : 'none';
    });
  };
  filter.addEventListener('input', applyFilter);
  filter.addEventListener('submit', (event) => event.preventDefault());

  app.querySelector('#new-client-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const client = await tryStore(() => store.createClient({
      organization: form.elements.organization.value.trim(),
      stage: form.elements.stage.value
    }));
    if (!client) return;
    setNotice('info', `Client “${client.organization}” created.`);
    go(`#/admin/client/${client.id}`);
  });
}

/* ---------- Admin: client workspace ---------- */

async function renderAdminClient(clientId) {
  const ws = await store.getWorkspace(clientId);
  if (!ws.client) throw new Error('Client not found.');
  const progress = computeProgress(ws.milestones);

  app.innerHTML = `${demoRibbon()}${noticeHtml()}
    <p><a class="btn btn-quiet btn-sm" href="#/admin">← All clients</a></p>
    <div class="portal-page-head">
      <h1>${esc(ws.client.organization)}</h1>
      ${badge('badge-stage', labelFor(LIFECYCLE_STAGES, ws.client.stage))}
    </div>
    <div class="portal-grid">
      <section class="portal-card">
        <h2>Client record &amp; approved AI context</h2>
        <form class="portal-form" id="client-edit-form">
          <div class="portal-form-row">
            <label>Stage <select name="stage">${options(LIFECYCLE_STAGES, ws.client.stage)}</select></label>
            <label>Governance tier <input name="governanceTier" value="${esc(ws.client.governanceTier || '')}"></label>
          </div>
          <div class="portal-form-row">
            <label>Configuration label <input name="configLabel" value="${esc(ws.client.configLabel || '')}"></label>
            <label>Last review <input type="date" name="lastReview" value="${esc(ws.client.lastReview || '')}"></label>
            <label>Next review <input type="date" name="nextReview" value="${esc(ws.client.nextReview || '')}"></label>
          </div>
          <label>Approved setup profile <span class="portal-muted">(the only client context the AI draft assistant receives)</span>
            <textarea name="setupProfile">${esc(ws.client.setupProfile || '')}</textarea>
          </label>
          <div class="portal-actions-row"><button class="btn btn-secondary" type="submit">Save client record</button></div>
        </form>
      </section>
      <section class="portal-card">
        <h2>Milestones · ${progress}%</h2>
        <ul class="portal-list">
          ${ws.milestones.map((m) => `<li class="portal-list-row" data-milestone-id="${esc(m.id)}">
              <span>${esc(m.title)}</span>
              <select data-milestone-status>${options(ACTION_STATUSES, m.status)}</select>
            </li>`).join('') || '<li class="portal-empty">No milestones yet.</li>'}
        </ul>
        <form class="portal-form" id="new-milestone-form" style="margin-top:.8rem">
          <div class="portal-form-row">
            <label>New milestone <input name="title" required placeholder="e.g. First team workflow in weekly use"></label>
          </div>
          <div class="portal-actions-row"><button class="btn btn-quiet btn-sm" type="submit">Add milestone</button></div>
        </form>
      </section>
    </div>
    <div class="portal-grid">
      <section class="portal-card">
        <h2>Publish a progress report</h2>
        <form class="portal-form" id="report-form">
          <label>Executive summary <textarea name="summary" required></textarea></label>
          <div class="portal-form-row">
            <label>Accomplishments <span class="portal-muted">(one per line)</span><textarea name="accomplishments"></textarea></label>
            <label>Gaps &amp; risks <span class="portal-muted">(one per line)</span><textarea name="risks"></textarea></label>
          </div>
          <div class="portal-form-row">
            <label>Capabilities enabled <span class="portal-muted">(one per line)</span><textarea name="capabilities"></textarea></label>
            <label>Next priorities <span class="portal-muted">(one per line)</span><textarea name="nextPriorities"></textarea></label>
          </div>
          <label>Note requiring client acknowledgment <input name="acknowledgeNote"></label>
          <div class="portal-actions-row"><button class="btn btn-primary" type="submit">Publish report →</button></div>
        </form>
      </section>
      <section class="portal-card">
        <h2>Assign an action</h2>
        <form class="portal-form" id="action-form">
          <label>Title <input name="title" required></label>
          <label>Plain-language instructions <textarea name="instructions" required></textarea></label>
          <div class="portal-form-row">
            <label>Category <select name="category">${options(ACTION_CATEGORIES, 'maintain')}</select></label>
            <label>Priority <select name="priority">${options(ACTION_PRIORITIES, 'medium')}</select></label>
            <label>Due date <input type="date" name="dueDate"></label>
          </div>
          <label>Supporting link <span class="portal-muted">(optional)</span><input name="link" placeholder="https://…"></label>
          <div class="portal-actions-row"><button class="btn btn-secondary" type="submit">Assign action →</button></div>
        </form>
        <h3 style="margin-top:1.1rem">Current plan</h3>
        <ul class="portal-list">
          ${sortActions(ws.actions).map((a) => `<li class="portal-list-row">
              <span>${esc(a.title)}${a.comment ? ` — <em class="portal-muted">client: “${esc(a.comment)}”</em>` : ''}</span>
              ${badge(`badge-action-${esc(a.status)}`, labelFor(ACTION_STATUSES, a.status))}
            </li>`).join('') || '<li class="portal-empty">No actions assigned yet.</li>'}
        </ul>
      </section>
    </div>
    <div class="portal-grid">
      <section class="portal-card">
        <h2>Conversations</h2>
        <ul class="portal-list">
          ${ws.conversations.map((c) => `<li class="portal-list-row">
              <a href="#/conversation/${esc(c.id)}">${esc(c.subject)}</a>
              ${badge(`badge-status-${esc(c.status)}`, labelFor(CONVERSATION_STATUSES, c.status))}
            </li>`).join('') || '<li class="portal-empty">No conversations yet.</li>'}
        </ul>
      </section>
      <section class="portal-card">
        <h2>Recent activity</h2>
        <ul class="portal-list">
          ${(ws.activity || []).slice(0, 12).map((e) => `<li class="portal-list-row">
              <span>${esc(store.userName(e.actor))} ${esc(e.action)}</span>
              <span class="portal-muted">${esc(formatDate(e.at))}</span>
            </li>`).join('') || '<li class="portal-empty">No activity recorded yet.</li>'}
        </ul>
      </section>
    </div>`;
  notice = null;
  bindDemoRibbon();

  app.querySelector('#client-edit-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const saved = await tryStore(() => store.updateClient(clientId, {
      stage: form.elements.stage.value,
      governanceTier: form.elements.governanceTier.value,
      configLabel: form.elements.configLabel.value,
      setupProfile: form.elements.setupProfile.value,
      lastReview: form.elements.lastReview.value || null,
      nextReview: form.elements.nextReview.value || null
    }));
    if (!saved) return;
    setNotice('info', 'Client record saved.');
    render();
  });

  app.querySelectorAll('[data-milestone-status]').forEach((select) => select.addEventListener('change', async () => {
    const milestoneId = select.closest('[data-milestone-id]').dataset.milestoneId;
    // On failure, tryStore re-renders from the store, restoring the select.
    const saved = await tryStore(() => store.updateMilestone(milestoneId, select.value));
    if (!saved) return;
    setNotice('info', 'Milestone updated.');
    render();
  }));

  app.querySelector('#new-milestone-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = event.currentTarget.elements.title.value.trim();
    const created = await tryStore(() => store.createMilestone(clientId, { title }));
    if (!created) return;
    setNotice('info', 'Milestone added.');
    render();
  });

  const lines = (value) => value.split('\n').map((l) => l.trim()).filter(Boolean);
  app.querySelector('#report-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const published = await tryStore(() => store.publishReport(clientId, {
      summary: form.elements.summary.value.trim(),
      accomplishments: lines(form.elements.accomplishments.value),
      risks: lines(form.elements.risks.value),
      capabilities: lines(form.elements.capabilities.value),
      nextPriorities: lines(form.elements.nextPriorities.value),
      acknowledgeNote: form.elements.acknowledgeNote.value.trim()
    }));
    if (!published) return;
    setNotice('info', 'Progress report published — the client can see it now.');
    render();
  });

  app.querySelector('#action-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const created = await tryStore(() => store.createAction(clientId, {
      title: form.elements.title.value.trim(),
      instructions: form.elements.instructions.value.trim(),
      category: form.elements.category.value,
      priority: form.elements.priority.value,
      dueDate: form.elements.dueDate.value || null,
      link: form.elements.link.value.trim()
    }));
    if (!created) return;
    setNotice('info', 'Action assigned.');
    render();
  });
}

init();
