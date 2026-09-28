// @ts-check
// Renderer shell: routing, data source, focus, announcements, theme (build step 3.5).
//
// The renderer owns view state only. It reads through a Source, so the
// Hermes desktop host can later replace the development HTTP source with
// its own validated IPC without touching any view.

import { renderBoard, renderError, renderMission, renderTable } from './views.mjs';

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Command} Command */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Envelope} Envelope */
/** @typedef {import('./views.mjs').TableColumn} TableColumn */
/** @typedef {import('./views.mjs').SortDirection} SortDirection */
/** @typedef {{ call: (command: 'mission' | 'board' | 'table', params?: Record<string, string>) => Promise<Envelope> }} Source */

const CONTRACT = 'nurse-manager-ipc@1';

/**
 * Development source: read-only calls to the loopback dev host.
 * @returns {Source}
 */
export function httpSource() {
  return {
    async call(command, params = {}) {
      const query = new URLSearchParams(params).toString();
      const response = await fetch(`/ipc/${command}${query ? `?${query}` : ''}`, {
        headers: { accept: 'application/json' },
      });
      if (!response.ok) throw new Error(`The workspace host answered ${response.status}.`);
      const envelope = /** @type {Envelope} */ (await response.json());
      if (envelope.contract !== CONTRACT) {
        throw new Error(`This screen understands ${CONTRACT}; the workspace sent ${String(envelope.contract)}.`);
      }
      return envelope;
    },
  };
}

/** @type {Record<string, { title: string, command: 'mission' | 'board' | 'table' }>} */
const ROUTES = {
  mission: { title: 'Mission Control', command: 'mission' },
  board: { title: 'Board', command: 'board' },
  table: { title: 'Tasks', command: 'table' },
};

/**
 * @param {Document} doc
 * @param {Source} source
 */
export function start(doc, source) {
  const main = /** @type {HTMLElement} */ (doc.getElementById('main'));
  const announcer = /** @type {HTMLElement} */ (doc.getElementById('announcer'));
  const workspaceName = /** @type {HTMLElement} */ (doc.getElementById('workspace-name'));
  const sampleBanner = /** @type {HTMLElement} */ (doc.getElementById('sample-banner'));
  /** @type {{ column: TableColumn, direction: SortDirection }} */
  let sort = { column: 'due_date', direction: 'ascending' };
  let generation = 0;

  /** @param {string} message */
  const announce = (message) => {
    announcer.textContent = '';
    // A fresh text node after clearing makes screen readers repeat identical messages.
    setTimeout(() => { announcer.textContent = message; }, 50);
  };

  const routeName = () => {
    const name = (doc.defaultView?.location.hash || '').replace(/^#\/?/, '');
    return name in ROUTES ? name : 'mission';
  };

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

  /** @param {boolean} moveFocus */
  const render = async (moveFocus) => {
    const name = routeName();
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
      envelope = await source.call(route.command);
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
    } else if (envelope.command === 'board') {
      show(renderBoard(doc, /** @type {import('../contracts/ipc/nurse-manager-ipc').Board} */ (data)), moveFocus);
      announce('Board loaded.');
    } else {
      const table = /** @type {import('../contracts/ipc/nurse-manager-ipc').Table} */ (data);
      /** @param {TableColumn} column */
      const onSort = (column) => {
        sort = {
          column,
          direction: sort.column === column && sort.direction === 'ascending' ? 'descending' : 'ascending',
        };
        const view = renderTable(doc, table, sort, onSort);
        main.replaceChildren(view);
        const again = view.querySelector(`[data-column="${column}"]`);
        if (again instanceof HTMLElement) again.focus();
        announce(`Sorted by ${column.replace('_', ' ')}, ${sort.direction}.`);
      };
      show(renderTable(doc, table, sort, onSort), moveFocus);
      announce(`Tasks loaded: ${table.rows.length}.`);
    }
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
  if (routeName() !== 'mission') {
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
  render(false);
}

if (typeof document !== 'undefined' && document.getElementById('main')) {
  start(document, httpSource());
}
