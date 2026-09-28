// @ts-check
// Renderer shell: routing, data source, focus, announcements, theme (build step 3.5).
//
// The renderer owns view state only. It reads through a Source, so the
// Hermes desktop host can later replace the development HTTP source with
// its own validated IPC without touching any view.

import {
  renderAssistant, renderBoard, renderBrief, renderError, renderMission, renderOnboarding, renderProject, renderTable,
} from './views.mjs';

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Command} Command */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Envelope} Envelope */
/** @typedef {import('./views.mjs').TableColumn} TableColumn */
/** @typedef {import('./views.mjs').SortDirection} SortDirection */
/**
 * @typedef {object} AppStatus
 * @property {string} app
 * @property {string} version
 * @property {boolean} has_workspace
 * @property {number} idle_timeout_seconds
 */
/**
 * A data source. Only `call` is required; the local app adds the rest.
 * @typedef {object} Source
 * @property {(command: ReadCommand | 'assistant-preview', params?: Record<string, string>) => Promise<Envelope>} call
 * @property {() => Promise<AppStatus | null>} [status] null means a read-only development host
 * @property {(command: WriteCommand, body: Record<string, string>) => Promise<Envelope>} [send]
 * @property {() => Promise<void>} [heartbeat]
 * @property {() => Promise<void>} [quit]
 */

const CONTRACT = 'nurse-manager-ipc@1';
const TOKEN_KEY = 'nm-token';

/**
 * Take the launch token from "#token=…", keep it for this tab only, and
 * clear it from the address bar so it is never bookmarked or shared.
 * @param {Window} win
 * @returns {string}
 */
export function takeToken(win) {
  const match = /(?:^#|&)token=([A-Za-z0-9_-]{20,})/.exec(win.location.hash);
  if (match) {
    try { win.sessionStorage.setItem(TOKEN_KEY, match[1]); } catch { /* storage may be unavailable */ }
    win.history.replaceState(null, '', `${win.location.pathname}#/mission`);
    return match[1];
  }
  try { return win.sessionStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}

/**
 * HTTP source for the local app and the development host. The token, when
 * present, goes in a header on every data call.
 * @param {string} [token]
 * @returns {Source}
 */
export function httpSource(token = '') {
  /** @param {Record<string, string>} [extra] */
  const headers = (extra = {}) => ({
    accept: 'application/json',
    ...(token ? { authorization: `Bearer ${token}` } : {}),
    ...extra,
  });
  /** @param {Response} response */
  const failure = async (response) => {
    const text = (await response.text()).trim();
    return new Error(text && response.status < 500 ? text : `The workspace host answered ${response.status}.`);
  };
  /** @param {Response} response */
  const envelopeOf = async (response) => {
    if (!response.ok) throw await failure(response);
    const envelope = /** @type {Envelope} */ (await response.json());
    if (envelope.contract !== CONTRACT) {
      throw new Error(`This screen understands ${CONTRACT}; the workspace sent ${String(envelope.contract)}.`);
    }
    return envelope;
  };
  const post = (/** @type {string} */ path, /** @type {unknown} */ body) => fetch(path, {
    method: 'POST', headers: headers({ 'content-type': 'application/json' }), body: JSON.stringify(body),
  });
  return {
    async call(command, params = {}) {
      const query = new URLSearchParams(params).toString();
      return envelopeOf(await fetch(`/ipc/${command}${query ? `?${query}` : ''}`, { headers: headers() }));
    },
    async status() {
      const response = await fetch('/app/status', { headers: headers() });
      if (!response.ok) throw await failure(response);
      const status = /** @type {AppStatus} */ (await response.json());
      // Only the local app offers onboarding and Quit; the dev host is read-only.
      return status.app === 'nurse-ai-os' ? status : null;
    },
    async send(command, body) {
      return envelopeOf(await post(`/ipc/${command}`, body));
    },
    async heartbeat() {
      await post('/app/heartbeat', {});
    },
    async quit() {
      const response = await post('/app/quit', {});
      if (!response.ok) throw await failure(response);
    },
  };
}

/** @typedef {'mission' | 'project' | 'board' | 'table' | 'weekly' | 'assistant'} ReadCommand */
/** @typedef {'sample' | 'init' | 'brief' | 'accept' | 'assistant-local' | 'assistant-off' | 'assistant-brief'} WriteCommand */

/** @type {Record<string, { title: string, command: ReadCommand }>} */
const ROUTES = {
  mission: { title: 'Mission Control', command: 'mission' },
  project: { title: 'Project', command: 'project' },
  board: { title: 'Board', command: 'board' },
  table: { title: 'Tasks', command: 'table' },
  brief: { title: 'Weekly brief', command: 'weekly' },
  assistant: { title: 'AI assistance', command: 'assistant' },
};

const PROJECT_ID = /^prj-[0-9a-f]{12}$/;

/**
 * Parse "#/<route>" or "#/project/<id>". Anything else is Mission Control.
 * @param {string} hash
 * @returns {{ name: string, params: Record<string, string> }}
 */
export function parseRoute(hash) {
  const parts = hash.replace(/^#\/?/, '').split('/');
  if (parts[0] === 'project' && parts.length === 2) {
    const id = decodeURIComponent(parts[1]);
    // A malformed id still routes to the project view, which reports it honestly.
    return { name: 'project', params: { id: PROJECT_ID.test(id) ? id : id.slice(0, 64) } };
  }
  return { name: parts.length === 1 && parts[0] in ROUTES && parts[0] !== 'project' ? parts[0] : 'mission', params: {} };
}

/**
 * @param {Document} doc
 * @param {Source} source
 */
export function start(doc, source) {
  const main = /** @type {HTMLElement} */ (doc.getElementById('main'));
  const announcer = /** @type {HTMLElement} */ (doc.getElementById('announcer'));
  const workspaceName = /** @type {HTMLElement} */ (doc.getElementById('workspace-name'));
  const sampleBanner = /** @type {HTMLElement} */ (doc.getElementById('sample-banner'));
  /** @type {Record<'table' | 'project', { column: TableColumn, direction: SortDirection }>} */
  const sorts = {
    table: { column: 'due_date', direction: 'ascending' },
    project: { column: 'due_date', direction: 'ascending' },
  };
  let generation = 0;

  /** @param {string} message */
  const announce = (message) => {
    announcer.textContent = '';
    // A fresh text node after clearing makes screen readers repeat identical messages.
    setTimeout(() => { announcer.textContent = message; }, 50);
  };

  const currentRoute = () => parseRoute(doc.defaultView?.location.hash || '');

  /** @type {Element | null} */
  let focusAtNavigation = null;

  /** @param {HTMLElement} view @param {boolean} moveFocus */
  const show = (view, moveFocus) => {
    const active = doc.activeElement;
    // Only move focus if the manager has not put it somewhere else while
    // the view was loading: a late render must never steal focus.
    const untouched = active === focusAtNavigation || active === doc.body || main.contains(active);
    main.replaceChildren(view);
    main.setAttribute('aria-busy', 'false');
    const title = view.querySelector('h1');
    if (moveFocus && untouched && title instanceof HTMLElement) title.focus();
  };

  /**
   * A sortable view: re-render in place on sort, keep focus on the sort button.
   * @param {'table' | 'project'} key
   * @param {(sort: { column: TableColumn, direction: SortDirection }, onSort: (column: TableColumn) => void) => HTMLElement} build
   * @param {boolean} moveFocus
   */
  const showSortable = (key, build, moveFocus) => {
    /** @param {TableColumn} column */
    const onSort = (column) => {
      const sort = sorts[key];
      sorts[key] = {
        column,
        direction: sort.column === column && sort.direction === 'ascending' ? 'descending' : 'ascending',
      };
      const view = build(sorts[key], onSort);
      main.replaceChildren(view);
      const again = view.querySelector(`[data-column="${column}"]`);
      if (again instanceof HTMLElement) again.focus();
      announce(`Sorted by ${column.replace('_', ' ')}, ${sorts[key].direction}.`);
    };
    show(build(sorts[key], onSort), moveFocus);
  };

  /** @param {boolean} moveFocus */
  const render = async (moveFocus) => {
    const { name, params } = currentRoute();
    const route = ROUTES[name];
    const mine = ++generation;
    focusAtNavigation = doc.activeElement;
    doc.title = `${route.title} — Nurse AI OS`;
    for (const link of doc.querySelectorAll('[data-route]')) {
      if (link.getAttribute('data-route') === name) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    main.setAttribute('aria-busy', 'true');
    let envelope;
    try {
      envelope = await source.call(route.command, params);
    } catch (error) {
      if (mine !== generation) return;
      const message = error instanceof Error ? error.message : String(error);
      show(renderError(doc, route.title, { type: 'Unavailable', message }), moveFocus);
      announce(`${route.title} could not load.`);
      return;
    }
    if (mine !== generation) return; // a newer navigation won
    if (!envelope.ok) {
      show(renderError(doc, route.title, envelope.error), moveFocus);
      announce(`${route.title} could not load.`);
      return;
    }
    const data = envelope.data;
    if ('sample' in data) sampleBanner.hidden = !data.sample;
    if (envelope.command === 'mission' && 'workspace' in data && typeof data.workspace === 'string') {
      workspaceName.textContent = data.workspace;
    }
    if (envelope.command === 'mission') {
      show(renderMission(doc, /** @type {import('../contracts/ipc/nurse-manager-ipc').MissionControl} */ (data)), moveFocus);
      announce('Mission Control loaded.');
    } else if (envelope.command === 'project') {
      const dashboard = /** @type {import('../contracts/ipc/nurse-manager-ipc').ProjectDashboard} */ (data);
      doc.title = `${dashboard.project.title} — Nurse AI OS`;
      showSortable('project', (sort, onSort) => renderProject(doc, dashboard, sort, onSort), moveFocus);
      announce(`Project ${dashboard.project.title} loaded.`);
    } else if (envelope.command === 'weekly') {
      showBrief(/** @type {import('./views.mjs').WeeklyBrief} */ (data), {}, moveFocus);
      announce('Weekly brief loaded.');
    } else if (envelope.command === 'assistant') {
      showAssistant(/** @type {import('./views.mjs').AssistantStatus} */ (data), {}, moveFocus);
      announce('AI assistance loaded.');
    } else if (envelope.command === 'board') {
      show(renderBoard(doc, /** @type {import('../contracts/ipc/nurse-manager-ipc').Board} */ (data)), moveFocus);
      announce('Board loaded.');
    } else {
      const table = /** @type {import('../contracts/ipc/nurse-manager-ipc').Table} */ (data);
      showSortable('table', (sort, onSort) => renderTable(doc, table, sort, onSort), moveFocus);
      announce(`Tasks loaded: ${table.rows.length}.`);
    }
  };

  // --- Writes from the screens (local app only) --------------------------
  let writable = false;

  /**
   * Show a view after an action, putting focus on its notice when it has one.
   * @param {HTMLElement} view
   * @param {import('./views.mjs').Notice | undefined} notice
   * @param {string} [focusSelector]
   */
  const showAfterAction = (view, notice, focusSelector) => {
    main.replaceChildren(view);
    main.setAttribute('aria-busy', 'false');
    const target = focusSelector ? view.querySelector(focusSelector) : view.querySelector('.notice') || view.querySelector('h1');
    if (target instanceof HTMLElement) {
      if (!target.hasAttribute('tabindex')) target.tabIndex = -1;
      target.focus();
    }
    if (notice) announce(notice.text);
  };

  /**
   * Send one write and return its envelope, or a notice describing the failure.
   * @param {WriteCommand} command
   * @param {Record<string, string>} body
   * @returns {Promise<{ envelope?: Envelope, failure?: import('./views.mjs').Notice }>}
   */
  const write = async (command, body) => {
    if (!source.send) return { failure: { kind: 'error', text: 'This host is read-only.' } };
    try {
      const envelope = await source.send(command, body);
      if (!envelope.ok) return { failure: { kind: 'error', text: envelope.error.message } };
      return { envelope };
    } catch (error) {
      return { failure: { kind: 'error', text: error instanceof Error ? error.message : String(error) } };
    }
  };

  /**
   * Reload a view's data after an action, unless the manager has navigated away.
   * @param {'weekly' | 'assistant'} command
   * @param {number} mine
   */
  const reload = async (command, mine) => {
    try {
      const envelope = await source.call(command);
      if (mine !== generation) return null;
      if (!envelope.ok) {
        show(renderError(doc, ROUTES[command === 'weekly' ? 'brief' : 'assistant'].title, envelope.error), true);
        return null;
      }
      return envelope.data;
    } catch (error) {
      if (mine !== generation) return null;
      show(renderError(doc, 'this page', { type: 'Unavailable', message: error instanceof Error ? error.message : String(error) }), true);
      return null;
    }
  };

  /**
   * @param {import('./views.mjs').WeeklyBrief} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, preview?: import('./views.mjs').AssistantPreview | null }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showBrief = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    /** @param {import('./views.mjs').Notice} [notice] */
    const refresh = async (notice) => {
      const fresh = await reload('weekly', mine);
      if (fresh) showBrief(/** @type {import('./views.mjs').WeeklyBrief} */ (fresh), { notice }, true);
    };
    /** @param {Promise<void>} work */
    const busyWhile = (work) => {
      main.replaceChildren(renderBrief(doc, data, { ...handlers, ...state, busy: true }));
      main.setAttribute('aria-busy', 'true');
      return work;
    };
    const handlers = {
      writable,
      onRecords: () => busyWhile((async () => {
        const { failure } = await write('brief', {});
        await refresh(failure || { kind: 'ok', text: 'A new draft was composed from your records. Review it, then accept it.' });
      })()),
      onPreview: () => busyWhile((async () => {
        try {
          const envelope = await source.call('assistant-preview');
          if (mine !== generation) return;
          if (!envelope.ok) {
            showBrief(data, { notice: { kind: 'error', text: envelope.error.message } }, true);
            return;
          }
          const preview = /** @type {import('./views.mjs').AssistantPreview} */ (envelope.data);
          showBrief(data, { preview }, true, '#preview-heading');
          announce('Showing exactly what would be sent. Nothing has been sent yet.');
        } catch (error) {
          if (mine !== generation) return;
          showBrief(data, { notice: { kind: 'error', text: error instanceof Error ? error.message : String(error) } }, true);
        }
      })()),
      onSend: (/** @type {string} */ sha) => busyWhile((async () => {
        announce('Sending to the AI model. This can take a minute.');
        const { envelope, failure } = await write('assistant-brief', { prompt_sha256: sha });
        if (failure || !envelope || !envelope.ok) {
          await refresh(failure);
          return;
        }
        const result = /** @type {import('./views.mjs').AssistantDraft} */ (envelope.data);
        await refresh(result.drafted_by_model
          ? { kind: 'ok', text: 'The AI model drafted a new version. Check every line against your records before you accept it.' }
          : { kind: 'fallback', text: result.reason });
      })()),
      onCancel: () => showBrief(data, {}, true),
      onAccept: (/** @type {import('./views.mjs').Revision} */ revision) => busyWhile((async () => {
        const { failure } = await write('accept', { revision: revision.id, sha256: revision.sha256 });
        await refresh(failure || { kind: 'ok', text: `Version ${revision.revision_no} is accepted.` });
      })()),
    };
    const view = renderBrief(doc, data, { ...handlers, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
    else show(view, moveFocus);
  };

  /**
   * @param {import('./views.mjs').AssistantStatus} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice }} state
   * @param {boolean} moveFocus
   */
  const showAssistant = (data, state, moveFocus) => {
    const mine = generation;
    /** @param {WriteCommand} command @param {Record<string, string>} body @param {string} done */
    const act = async (command, body, done) => {
      main.replaceChildren(renderAssistant(doc, data, { ...options, busy: true }));
      const { failure } = await write(command, body);
      const fresh = await reload('assistant', mine);
      if (fresh) showAssistant(/** @type {import('./views.mjs').AssistantStatus} */ (fresh), { notice: failure || { kind: 'ok', text: done } }, true);
    };
    const options = {
      writable,
      onConnect: (/** @type {string} */ model, /** @type {string} */ endpoint) =>
        act('assistant-local', { model, endpoint }, `Connected to the AI model “${model}” on this computer.`),
      onDisconnect: () => act('assistant-off', {}, 'The AI model is disconnected. Nothing will be sent anywhere.'),
    };
    const view = renderAssistant(doc, data, { ...options, ...state });
    if (state.notice) showAfterAction(view, state.notice);
    else show(view, moveFocus);
  };

  const themeToggle = /** @type {HTMLButtonElement} */ (doc.getElementById('theme-toggle'));
  const root = doc.documentElement;
  /** @param {'day' | 'night'} theme */
  const applyTheme = (theme) => {
    root.setAttribute('data-theme', theme);
    themeToggle.setAttribute('aria-pressed', theme === 'night' ? 'true' : 'false');
    try { doc.defaultView?.localStorage.setItem('nm-theme', theme); } catch { /* storage may be unavailable */ }
  };
  let saved = null;
  try { saved = doc.defaultView?.localStorage.getItem('nm-theme'); } catch { /* ignore */ }
  const prefersDark = doc.defaultView?.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved === 'night' || saved === 'day' ? saved : prefersDark ? 'night' : 'day');
  themeToggle.addEventListener('click', () =>
    applyTheme(root.getAttribute('data-theme') === 'night' ? 'day' : 'night'));

  // Board and table data carry no workspace name, so the header asks
  // Mission Control once when the manager lands somewhere else first.
  if (currentRoute().name !== 'mission') {
    source.call('mission').then((envelope) => {
      if (envelope.ok && 'workspace' in envelope.data && typeof envelope.data.workspace === 'string') {
        workspaceName.textContent = envelope.data.workspace;
      }
    }).catch(() => { /* the view itself reports failures */ });
  }

  // The skip link moves focus without touching the URL, so it never
  // triggers a route change (the href stays for use without scripts).
  const skipLink = doc.querySelector('.skip-link');
  skipLink?.addEventListener('click', (event) => {
    event.preventDefault();
    main.focus();
  });

  // Only "#/<route>" fragments are routes; any other fragment is ignored.
  doc.defaultView?.addEventListener('hashchange', () => {
    const hash = doc.defaultView?.location.hash || '';
    if (hash === '' || hash.startsWith('#/')) render(true);
  });
  // --- Local app: onboarding, heartbeat, and quit (ADR 0003) -------------
  const footer = /** @type {HTMLElement} */ (doc.getElementById('app-footer'));
  const quitButton = /** @type {HTMLButtonElement} */ (doc.getElementById('quit-button'));

  /** @param {{ busy?: boolean, error?: string }} state @param {boolean} moveFocus */
  const showOnboarding = (state, moveFocus) => {
    const send = source.send;
    if (!send) return;
    doc.title = 'Welcome — Nurse AI OS';
    /** @param {Promise<Envelope>} pending */
    const finish = async (pending) => {
      showOnboarding({ busy: true }, false);
      let envelope;
      try {
        envelope = await pending;
      } catch (error) {
        showOnboarding({ error: error instanceof Error ? error.message : String(error) }, true);
        return;
      }
      if (!envelope.ok) {
        showOnboarding({ error: envelope.error.message }, true);
        return;
      }
      announce('Workspace ready.');
      focusAtNavigation = doc.activeElement;
      if (doc.defaultView && doc.defaultView.location.hash !== '#/mission') {
        doc.defaultView.location.hash = '#/mission'; // the hashchange handler renders
      } else {
        render(true);
      }
    };
    show(renderOnboarding(doc, {
      onSample: () => { finish(send('sample', {})); },
      onCreate: (name, owner) => { finish(send('init', { name, owner })); },
    }, state), moveFocus);
    if (state.error) announce(`Not created: ${state.error}`);
  };

  const showStopped = () => {
    const stopped = doc.createElement('div');
    stopped.className = 'view';
    const heading = doc.createElement('h1');
    heading.className = 'view-title';
    heading.tabIndex = -1;
    heading.textContent = 'Nurse AI OS has stopped';
    const note = doc.createElement('p');
    note.textContent = 'Your work is saved on this computer. You can close this tab and open Nurse AI OS again any time.';
    stopped.append(heading, note);
    main.replaceChildren(stopped);
    main.setAttribute('aria-busy', 'false');
    footer.hidden = true;
    heading.focus();
    announce('Nurse AI OS has stopped.');
  };

  const boot = async () => {
    let status = null;
    try {
      status = source.status ? await source.status() : null;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      show(renderError(doc, 'Nurse AI OS', { type: 'NotConnected', message }), false);
      return;
    }
    if (status) {
      writable = true;
      footer.hidden = false;
      const minutes = Math.round(status.idle_timeout_seconds / 60);
      const lifetime = doc.getElementById('app-lifetime');
      if (lifetime) {
        lifetime.textContent = `Nurse AI OS is running on this computer. It stops when you quit, or by itself after ${minutes} minutes with no page open.`;
      }
      const beat = () => { source.heartbeat?.().catch(() => { /* the next view load reports failures */ }); };
      doc.defaultView?.setInterval(beat, 60000);
      doc.addEventListener('visibilitychange', () => { if (doc.visibilityState === 'visible') beat(); });
      quitButton.addEventListener('click', async () => {
        quitButton.disabled = true;
        try { await source.quit?.(); } catch { /* it is stopping either way */ }
        showStopped();
      });
      if (!status.has_workspace) {
        showOnboarding({}, false);
        return;
      }
    }
    render(false);
  };
  boot();
}

if (typeof document !== 'undefined' && document.getElementById('main') && typeof window !== 'undefined') {
  start(document, httpSource(takeToken(window)));
}
