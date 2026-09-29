// @ts-check
// Renderer shell: routing, data source, focus, announcements, theme (build step 3.5).
//
// The renderer owns view state only. It reads through a Source, so the
// Hermes desktop host can later replace the development HTTP source with
// its own validated IPC without touching any view.

import {
  renderAssistant, renderBoard, renderBrief, renderContributions, renderError, renderMemory, typedContributions, typedMemory, typedSchedule, renderLearning, renderLibrary, renderMission, renderOnboarding,
  renderProject, renderTable, renderPacks, typedPacks, renderDocument, renderHelp, typedPilot,
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
 * @property {(command: ReadCommand | 'assistant-preview' | 'assistant-project-preview' | 'pilot-feedback-preview', params?: Record<string, string>) => Promise<Envelope>} call
 * @property {() => Promise<AppStatus | null>} [status] null means a read-only development host
 * @property {(command: WriteCommand, body: WriteBody) => Promise<Envelope>} [send]
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

/** @typedef {Record<string, string | number | boolean>} WriteBody */
/** @typedef {'mission' | 'project' | 'board' | 'table' | 'weekly' | 'assistant' | 'library' | 'learning' | 'contributions' | 'memory' | 'packs' | 'document' | 'pilot-feedback'} ReadCommand */
/** @typedef {'sample' | 'init' | 'brief' | 'accept' | 'assistant-local' | 'assistant-off' | 'assistant-brief' | 'assistant-project' | 'note-keep' | 'feedback-add' | 'feedback-address' | 'source-add'
 *   | 'learning-add' | 'learning-start' | 'learning-complete' | 'contribution-add' | 'contribution-verify' | 'brief-schedule-set'
 *   | 'memory-add' | 'memory-correct' | 'memory-exclude' | 'memory-include' | 'memory-delete'
 *   | 'assistants-stop' | 'assistants-resume' | 'pack-start' | 'document-save'
 *   | 'pilot-feedback-add' | 'pilot-feedback-delete' | 'pilot-feedback-export'} WriteCommand */

/** @type {Record<string, { title: string, command: ReadCommand }>} */
const ROUTES = {
  mission: { title: 'Mission Control', command: 'mission' },
  project: { title: 'Project', command: 'project' },
  board: { title: 'Board', command: 'board' },
  table: { title: 'Tasks', command: 'table' },
  brief: { title: 'Weekly brief', command: 'weekly' },
  library: { title: 'Library', command: 'library' },
  learning: { title: 'Learning and Growth', command: 'learning' },
  contributions: { title: 'Contributions', command: 'contributions' },
  memory: { title: 'Memory', command: 'memory' },
  packs: { title: 'Packs', command: 'packs' },
  document: { title: 'Document', command: 'document' },
  assistant: { title: 'AI assistance', command: 'assistant' },
  help: { title: 'Help and feedback', command: 'pilot-feedback' },
};

const PROJECT_ID = /^prj-[0-9a-f]{12}$/;
const DOCUMENT_ID = /^art-[0-9a-f]{12}$/;

/**
 * Parse "#/<route>" or "#/project/<id>". Anything else is Mission Control.
 * @param {string} hash
 * @returns {{ name: string, params: Record<string, string> }}
 */
export function parseRoute(hash) {
  const parts = hash.replace(/^#\/?/, '').split('/');
  if ((parts[0] === 'project' || parts[0] === 'document') && parts.length === 2) {
    let id;
    try {
      id = decodeURIComponent(parts[1]);
    } catch {
      id = parts[1]; // a broken escape is just a malformed id
    }
    // A malformed id still routes to its view, which reports it honestly.
    const valid = (parts[0] === 'project' ? PROJECT_ID : DOCUMENT_ID).test(id);
    return { name: parts[0], params: { id: valid ? id : id.slice(0, 64) } };
  }
  const single = parts.length === 1 && parts[0] in ROUTES && parts[0] !== 'project' && parts[0] !== 'document';
  return { name: single ? parts[0] : 'mission', params: {} };
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
   * @returns {(focusSelector?: string) => void} redraw in place, keeping the sort
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
    return (focusSelector) => {
      const view = build(sorts[key], onSort);
      main.replaceChildren(view);
      main.setAttribute('aria-busy', 'false');
      const target = focusSelector ? view.querySelector(focusSelector) : null;
      if (target instanceof HTMLElement) {
        if (!target.hasAttribute('tabindex')) target.tabIndex = -1;
        target.focus();
      }
    };
  };

  /** @param {boolean} moveFocus */
  const render = async (moveFocus) => {
    const { name, params } = currentRoute();
    const route = ROUTES[name];
    const mine = ++generation;
    focusAtNavigation = doc.activeElement;
    doc.title = `${route.title} — Nurse AI OS`;
    // A document opened from Packs keeps Packs marked as where the manager is.
    const section = name === 'document' ? 'packs' : name;
    for (const link of doc.querySelectorAll('[data-route]')) {
      if (link.getAttribute('data-route') === section) link.setAttribute('aria-current', 'page');
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
      showMission(/** @type {import('../contracts/ipc/nurse-manager-ipc').MissionControl} */ (data), {}, moveFocus);
      announce('Mission Control loaded.');
    } else if (envelope.command === 'project') {
      const dashboard = /** @type {import('../contracts/ipc/nurse-manager-ipc').ProjectDashboard} */ (data);
      doc.title = `${dashboard.project.title} — Nurse AI OS`;
      /** @type {Omit<import('./views.mjs').ThinkOptions, 'writable' | 'onPreview' | 'onSend' | 'onCancel'>} */
      let think = { question: '' };
      const thinkHandlers = {
        onPreview: (/** @type {string} */ question) => thinkAction({ question }, async () => {
          const envelope = await source.call('assistant-project-preview', { id: dashboard.project.id, question });
          if (!envelope.ok) return { notice: { kind: 'error', text: envelope.error.message } };
          announce('Showing exactly what would be sent. Nothing has been sent yet.');
          return { preview: /** @type {import('./views.mjs').ProjectQuestionPreview} */ (envelope.data) };
        }, '#think-preview-heading'),
        onSend: (/** @type {string} */ sha) => thinkAction({ sending: true }, async () => {
          announce('Sending to the AI model. This can take a minute. You can stop it.');
          const { envelope, failure } = await write('assistant-project', {
            id: dashboard.project.id, question: think.question ?? '', prompt_sha256: sha,
          });
          if (failure || !envelope || !envelope.ok) return { notice: failure };
          const answer = /** @type {import('./views.mjs').ProjectAnswer} */ (envelope.data);
          return answer.answered_by_model
            ? { answer, notice: { kind: 'ok', text: 'The AI model answered. It is a suggestion and is not saved.' } }
            : { notice: { kind: 'unanswered', text: answer.reason } };
        }),
        onCancel: () => { think = { question: think.question }; redraw('#think-question'); },
        onStop: stopAssistants,
        onKeep: async () => {
          const answer = think.answer;
          if (!answer) return;
          const mine2 = generation;
          think = { ...think, busy: true };
          redraw();
          const { failure } = await write('note-keep', {
            request_id: answer.request_id, project_id: dashboard.project.id,
            question: answer.question, answer: answer.answer,
          });
          if (mine2 !== generation) return;
          if (failure) {
            think = { question: think.question, answer, notice: failure };
            redraw('#think .notice');
            announce(failure.text);
            return;
          }
          await render(false); // reload the dashboard so the note shows from the records
          const heading = doc.getElementById('notes-heading');
          if (heading) heading.focus();
          announce('Kept as a project note.');
        },
        onEdit: (/** @type {string} */ question) => {
          think = { question };
          announce('The question changed. Preview it again before sending.');
        },
      };
      /** @type {{ busy?: boolean, notice?: import('./views.mjs').Notice, addressing?: string | null }} */
      let fb = {};
      /**
       * Write feedback, then reload the dashboard from the records.
       * @param {'feedback-add' | 'feedback-address'} command
       * @param {Record<string, string>} body
       * @param {string} done
       */
      const feedbackWrite = async (command, body, done) => {
        const mine2 = generation;
        fb = { ...fb, busy: true };
        redraw();
        const { failure } = await write(command, body);
        if (mine2 !== generation) return;
        if (failure) {
          fb = { addressing: fb.addressing, notice: failure };
          redraw('#feedback .notice');
          announce(failure.text);
          return;
        }
        await render(false);
        const heading = doc.getElementById('feedback-heading');
        if (heading) heading.focus();
        announce(done);
      };
      const feedbackHandlers = {
        onAdd: (/** @type {Record<string, string>} */ fields) => feedbackWrite(
          'feedback-add', { project_id: dashboard.project.id, ...fields }, 'Feedback added.'),
        onStartAddress: (/** @type {string} */ id) => {
          fb = { addressing: id };
          redraw(`#response-${id}`);
        },
        onCancelAddress: () => { fb = {}; redraw('#feedback-heading'); },
        onAddress: (/** @type {string} */ id, /** @type {string} */ response) => feedbackWrite(
          'feedback-address', { feedback_id: id, response }, 'Feedback marked addressed.'),
      };
      const build = (/** @type {{ column: TableColumn, direction: SortDirection }} */ sort, /** @type {(column: TableColumn) => void} */ onSort) =>
        renderProject(doc, dashboard, sort, onSort, { ...think, ...thinkHandlers, writable },
          { ...fb, ...feedbackHandlers, writable });
      const redraw = showSortable('project', build, moveFocus);
      /**
       * Run one "think" step: show it busy, then redraw with its result.
       * @param {Partial<typeof think>} start
       * @param {() => Promise<Partial<typeof think>>} work
       * @param {string} [focusSelector]
       */
      const thinkAction = async (start, work, focusSelector) => {
        const mine2 = generation;
        think = { question: think.question, ...start, busy: true };
        redraw();
        let next;
        try {
          next = await work();
        } catch (error) {
          next = { notice: { kind: /** @type {'error'} */ ('error'), text: error instanceof Error ? error.message : String(error) } };
        }
        if (mine2 !== generation) return;
        think = { question: think.question, ...next, busy: false };
        if (think.notice) announce(think.notice.text);
        redraw(think.notice ? '#think .notice' : focusSelector);
      };
      announce(`Project ${dashboard.project.title} loaded.`);
    } else if (envelope.command === 'weekly') {
      showBrief(/** @type {import('./views.mjs').WeeklyBrief} */ (data), {}, moveFocus);
      announce('Weekly brief loaded.');
    } else if (envelope.command === 'learning') {
      showLearning(/** @type {import('./views.mjs').Learning} */ (data), {}, moveFocus);
      announce('Learning and Growth loaded.');
    } else if (envelope.command === 'contributions') {
      showContributions(/** @type {import('./views.mjs').Contributions} */ (data), {}, moveFocus);
      announce('Contributions loaded.');
    } else if (envelope.command === 'pilot-feedback') {
      showHelp(/** @type {import('./views.mjs').PilotFeedback} */ (data), {}, moveFocus);
      announce('Help and feedback loaded.');
    } else if (envelope.command === 'packs') {
      showPacks(/** @type {import('./views.mjs').Packs} */ (data), {}, moveFocus);
      announce('Packs loaded.');
    } else if (envelope.command === 'document') {
      const view = /** @type {import('./views.mjs').PackDocumentView} */ (data);
      doc.title = `${view.document.title} — Nurse AI OS`;
      showDocument(view, {}, moveFocus);
      announce(`Document ${view.document.title} loaded.`);
    } else if (envelope.command === 'memory') {
      showMemory(/** @type {import('./views.mjs').Memory} */ (data), {}, moveFocus);
      announce('Memory loaded.');
    } else if (envelope.command === 'library') {
      showLibrary(/** @type {import('./views.mjs').Library} */ (data), {}, moveFocus);
      announce('Library loaded.');
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
   * @param {WriteBody} body
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
   * @param {'weekly' | 'assistant' | 'library' | 'learning' | 'contributions' | 'memory' | 'mission' | 'packs' | 'document' | 'pilot-feedback'} command
   * @param {number} mine
   * @param {Record<string, string>} [params]
   * @param {(message: string) => void} [onFail] handle a failed reload instead of showing the error page
   */
  const reload = async (command, mine, params = {}, onFail) => {
    try {
      const envelope = await source.call(command, params);
      if (mine !== generation) return null;
      if (!envelope.ok && onFail) {
        onFail(envelope.error.message);
        return null;
      }
      if (!envelope.ok) {
        const view = { weekly: 'brief', assistant: 'assistant', library: 'library', learning: 'learning', contributions: 'contributions', memory: 'memory', mission: 'mission', packs: 'packs', document: 'document', 'pilot-feedback': 'help' }[command];
        show(renderError(doc, ROUTES[view].title, envelope.error), true);
        return null;
      }
      return envelope.data;
    } catch (error) {
      if (mine !== generation) return null;
      if (onFail) {
        onFail(error instanceof Error ? error.message : String(error));
        return null;
      }
      show(renderError(doc, 'this page', { type: 'Unavailable', message: error instanceof Error ? error.message : String(error) }), true);
      return null;
    }
  };

  /**
   * Stop every assistant from where the work is waiting. The request that is
   * waiting returns by itself, within a second, saying it was stopped.
   * @returns {Promise<boolean>} whether the stop was saved
   */
  const stopAssistants = async () => {
    const { failure } = await write('assistants-stop', {});
    announce(failure ? `Not stopped: ${failure.text}. Try again.` : 'Stopped. Nothing more is sent, and its reply will be discarded.');
    return !failure;
  };

  /**
   * Packs: start a draft from a reviewed template, then open it.
   * @param {import('./views.mjs').Packs} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, typed?: Record<string, import('./views.mjs').PackChoice> }} state
   * @param {boolean} moveFocus
   */
  const showPacks = (data, state, moveFocus) => {
    const mine = generation;
    const options = {
      writable,
      onStart: async (/** @type {string} */ packId, /** @type {{ template: string, project_id: string }} */ choice) => {
        const typed = typedPacks(main, state.typed);
        main.replaceChildren(renderPacks(doc, data, { ...options, typed, busy: true }));
        main.setAttribute('aria-busy', 'true');
        const { envelope, failure } = await write('pack-start', { pack: packId, ...choice });
        if (mine !== generation) return;
        if (failure || !envelope || !envelope.ok) {
          showPacks(data, { notice: failure, typed }, true);
          return;
        }
        // The new draft opens straight away: the next step is to write it.
        const started = /** @type {import('./views.mjs').PackDocumentView} */ (envelope.data);
        const win = doc.defaultView;
        if (win) win.location.hash = `#/document/${encodeURIComponent(started.document.id)}`;
      },
    };
    const view = renderPacks(doc, data, { ...options, ...state });
    if (state.notice) showAfterAction(view, state.notice);
    else show(view, moveFocus);
  };

  /**
   * One pack document: edit as a new draft, accept exactly what was reviewed.
   * @param {import('./views.mjs').PackDocumentView} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, editing?: boolean, typed?: string }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showDocument = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    const typedNow = () => {
      const text = main.querySelector('#document-text');
      return text instanceof HTMLTextAreaElement ? text.value : state.typed;
    };
    /**
     * @param {WriteCommand} command
     * @param {WriteBody} body
     * @param {string} done
     * @param {boolean} editing whether the editor stays open if it fails
     */
    const act = async (command, body, done, editing) => {
      const typed = typedNow();
      main.replaceChildren(renderDocument(doc, data, { ...options, editing, typed, busy: true }));
      main.setAttribute('aria-busy', 'true');
      const { failure } = await write(command, body);
      if (mine !== generation) return;
      if (failure) {
        // Refused: the text stays as typed, to fix and save again.
        showDocument(data, { notice: failure, editing, typed }, true);
        return;
      }
      const fresh = await reload('document', mine, { id: data.document.id }, (message) => showDocument(data, {
        notice: { kind: 'error', text: `${done} The document could not be refreshed (${message}); open it again to see it.` },
      }, true));
      if (!fresh) return;
      showDocument(/** @type {import('./views.mjs').PackDocumentView} */ (fresh), { notice: { kind: 'ok', text: done } }, true);
    };
    const options = {
      writable,
      onEdit: () => showDocument(data, { editing: true }, true, '#document-text'),
      onCancelEdit: () => showDocument(data, {}, true, '#document-current-heading'),
      onSave: (/** @type {string} */ body, /** @type {string} */ base) => act('document-save',
        { document_id: data.document.id, body_markdown: body, base_sha256: base },
        'Saved as a new draft. Review it, then accept it.', true),
      onAccept: (/** @type {import('./views.mjs').Revision} */ revision) => act('accept',
        { revision: revision.id, sha256: revision.sha256 }, `Version ${revision.revision_no} is accepted.`, false),
    };
    const view = renderDocument(doc, data, { ...options, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
    else show(view, moveFocus);
  };

  /**
   * Mission Control, with the switch that stops every assistant (step 5.3).
   * @param {import('../contracts/ipc/nurse-manager-ipc').MissionControl} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice }} state
   * @param {boolean} moveFocus
   */
  const showMission = (data, state, moveFocus) => {
    const mine = generation;
    /** @param {'assistants-stop' | 'assistants-resume'} command @param {string} done */
    const act = async (command, done) => {
      main.replaceChildren(renderMission(doc, data, { ...options, busy: true }));
      main.setAttribute('aria-busy', 'true');
      const { failure } = await write(command, {});
      if (mine !== generation) return;
      if (failure) {
        showMission(data, { notice: failure }, true);
        return;
      }
      // Re-render from the fresh records, so the switch shows what is true now.
      const fresh = await reload('mission', mine, {}, (message) => showMission(data, {
        notice: { kind: 'error', text: `${done} Mission Control could not be refreshed (${message}); open it again to see it.` },
      }, true));
      if (!fresh) return;
      showMission(/** @type {import('../contracts/ipc/nurse-manager-ipc').MissionControl} */ (fresh), { notice: { kind: 'ok', text: done } }, true);
    };
    /** @type {import('./views.mjs').MissionOptions} */
    const options = {
      writable,
      onStop: () => act('assistants-stop', 'Assistants are stopped. Nothing is sent to an AI model until you let them work again.'),
      onResume: () => act('assistants-resume', 'Assistants can work again. Nothing that was stopped restarts by itself.'),
    };
    const view = renderMission(doc, data, { ...options, ...state });
    if (state.notice) showAfterAction(view, state.notice, '#assistants .notice');
    else show(view, moveFocus);
  };

  /**
   * @param {import('./views.mjs').WeeklyBrief} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, preview?: import('./views.mjs').AssistantPreview | null, scheduleDraft?: import('./views.mjs').ScheduleFields | null }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showBrief = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    // Every action stays on the week the page shows, even across a Monday.
    const week = data.week_of;
    // Unsaved "Every week" choices survive every re-render of this page.
    const scheduleDraft = () => typedSchedule(main) ?? state.scheduleDraft ?? null;
    /**
     * @param {import('./views.mjs').Notice} [notice]
     * @param {import('./views.mjs').ScheduleFields | null} [kept]
     */
    const refresh = async (notice, kept = scheduleDraft()) => {
      const fresh = await reload('weekly', mine, { week });
      if (fresh) showBrief(/** @type {import('./views.mjs').WeeklyBrief} */ (fresh), { notice, scheduleDraft: kept }, true);
    };
    /** @param {Promise<void>} work @param {boolean} [sending] a request is waiting for the model */
    const busyWhile = (work, sending = false) => {
      state = { ...state, scheduleDraft: scheduleDraft() };
      main.replaceChildren(renderBrief(doc, data, { ...handlers, ...state, busy: true, sending }));
      main.setAttribute('aria-busy', 'true');
      return work;
    };
    const handlers = {
      writable,
      onRecords: () => busyWhile((async () => {
        const { failure } = await write('brief', { week });
        await refresh(failure || { kind: 'ok', text: 'A new draft was composed from your records. Review it, then accept it.' });
      })()),
      onPreview: () => busyWhile((async () => {
        try {
          const envelope = await source.call('assistant-preview', { week });
          if (mine !== generation) return;
          if (!envelope.ok) {
            showBrief(data, { notice: { kind: 'error', text: envelope.error.message }, scheduleDraft: state.scheduleDraft }, true);
            return;
          }
          const preview = /** @type {import('./views.mjs').AssistantPreview} */ (envelope.data);
          showBrief(data, { preview, scheduleDraft: state.scheduleDraft }, true, '#preview-heading');
          announce('Showing exactly what would be sent. Nothing has been sent yet.');
        } catch (error) {
          if (mine !== generation) return;
          showBrief(data, { notice: { kind: 'error', text: error instanceof Error ? error.message : String(error) }, scheduleDraft: state.scheduleDraft }, true);
        }
      })()),
      onSend: (/** @type {string} */ sha) => busyWhile((async () => {
        announce('Sending to the AI model. This can take a minute. You can stop it.');
        const { envelope, failure } = await write('assistant-brief', { week, prompt_sha256: sha });
        if (failure || !envelope || !envelope.ok) {
          await refresh(failure);
          return;
        }
        const result = /** @type {import('./views.mjs').AssistantDraft} */ (envelope.data);
        await refresh(result.drafted_by_model
          ? { kind: 'ok', text: 'The AI model drafted a new version. Check every line against your records before you accept it.' }
          : { kind: 'fallback', text: result.reason });
      })(), true),
      onStop: stopAssistants,
      onCancel: () => showBrief(data, { scheduleDraft: scheduleDraft() }, true),
      onAccept: (/** @type {import('./views.mjs').Revision} */ revision) => busyWhile((async () => {
        const { failure } = await write('accept', { revision: revision.id, sha256: revision.sha256 });
        await refresh(failure || { kind: 'ok', text: `Version ${revision.revision_no} is accepted.` });
      })()),
      onSchedule: (/** @type {import('./views.mjs').ScheduleFields} */ fields) => busyWhile((async () => {
        const { failure } = await write('brief-schedule-set', fields);
        // Saved: show what was saved. Refused: keep the choices to fix them.
        await refresh(failure || { kind: 'ok', text: fields.enabled
          ? 'Saved. A draft from your records will be prepared every week while the app is open.'
          : 'Saved. The weekly draft is off.' }, failure ? fields : null);
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

  /**
   * @param {import('./views.mjs').Library} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice }} state
   * @param {boolean} moveFocus
   */
  const showLibrary = (data, state, moveFocus) => {
    const mine = generation;
    const options = {
      writable,
      onAdd: async (/** @type {Record<string, string>} */ fields) => {
        main.replaceChildren(renderLibrary(doc, data, { ...options, busy: true }));
        const { failure } = await write('source-add', fields);
        if (mine !== generation) return;
        if (failure) {
          showLibrary(data, { notice: failure }, true);
          return;
        }
        const fresh = await reload('library', mine);
        // Re-render from the fresh records, so the next action starts from them.
        if (fresh) {
          showLibrary(/** @type {import('./views.mjs').Library} */ (fresh),
            { notice: { kind: 'ok', text: `Added “${fields.title}” to the library.` } }, true);
        }
      },
    };
    const view = renderLibrary(doc, data, { ...options, ...state });
    if (state.notice) showAfterAction(view, state.notice);
    else show(view, moveFocus);
  };

  /**
   * @param {import('./views.mjs').Learning} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, completing?: string | null }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showLearning = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    /**
     * @param {WriteCommand} command
     * @param {Record<string, string>} body
     * @param {string} done
     */
    const act = async (command, body, done) => {
      main.replaceChildren(renderLearning(doc, data, { ...options, ...state, busy: true }));
      const { failure } = await write(command, body);
      if (mine !== generation) return;
      if (failure) {
        showLearning(data, { completing: state.completing, notice: failure }, true);
        return;
      }
      const fresh = await reload('learning', mine);
      // Re-render from the fresh records, so every button acts on them.
      if (fresh) showLearning(/** @type {import('./views.mjs').Learning} */ (fresh), { notice: { kind: 'ok', text: done } }, true);
    };
    /** @type {import('./views.mjs').LearningOptions} */
    const options = {
      writable,
      onAdd: (fields) => act('learning-add', fields, `Added “${fields.title}” to your plan.`),
      onStart: (id) => act('learning-start', { learning_id: id }, 'Started.'),
      onOpenComplete: (id) => showLearning(data, { completing: id }, true, `#takeaway-${id}`),
      onCancelComplete: () => showLearning(data, {}, true),
      onComplete: (id, fields) => act('learning-complete', { learning_id: id, ...fields }, 'Marked completed, with your takeaway.'),
    };
    const view = renderLearning(doc, data, { ...options, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
    else show(view, moveFocus);
  };

  /**
   * @param {import('./views.mjs').Contributions} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, verifying?: string | null, typed?: import('./views.mjs').ContributionTyped }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showContributions = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    // What is typed but unsaved, including evidence for drafts whose form is closed.
    const typedNow = () => typedContributions(main, state.typed);
    /** @param {Record<string, string>} evidence @param {string} id */
    const without = (evidence, id) => Object.fromEntries(Object.entries(evidence).filter(([key]) => key !== id));
    /**
     * @param {WriteCommand} command
     * @param {Record<string, string>} body
     * @param {string} done
     */
    const act = async (command, body, done) => {
      const before = typedNow();
      const saving = command === 'contribution-add' ? 'add' : body.contribution_id;
      main.replaceChildren(renderContributions(doc, data, { ...options, ...state, typed: before, busy: true, saving }));
      // The submitted form is read-only while it saves; the other stays editable,
      // so read the view again afterwards: nothing typed meanwhile is lost.
      const latest = () => typedContributions(main, before);
      const { failure } = await write(command, body);
      if (mine !== generation) return;
      if (failure) {
        showContributions(data, { verifying: state.verifying, notice: failure, typed: latest() }, true);
        return;
      }
      // The saved form starts empty; everything else keeps what was typed in it.
      const next = () => {
        const typed = latest();
        return command === 'contribution-add'
          ? { verifying: state.verifying, typed: { add: {}, evidence: typed.evidence } }
          : { typed: { add: typed.add, evidence: without(typed.evidence, body.contribution_id) } };
      };
      // If the save worked but the refresh fails, stay on this screen with the
      // unsaved text, rather than replacing it with the error page.
      const fresh = await reload('contributions', mine, {}, (message) => showContributions(data, {
        ...next(), notice: { kind: 'error', text: `${done} The list could not be refreshed (${message}); open Contributions again to see it.` },
      }, true));
      // Re-render from the fresh records, so every button acts on them.
      if (!fresh) return;
      showContributions(/** @type {import('./views.mjs').Contributions} */ (fresh), { ...next(), notice: { kind: 'ok', text: done } }, true);
    };
    /** @type {import('./views.mjs').ContributionsOptions} */
    const options = {
      writable,
      onAdd: (fields) => act('contribution-add', fields, `Saved “${fields.title}” as a draft. Verify it with evidence when you have it.`),
      // Switching to another draft keeps the first draft's evidence for when it is reopened.
      onOpenVerify: (id) => showContributions(data, { verifying: id, typed: typedNow() }, true, `#evidence-${id}`),
      // Cancel discards that draft's evidence, as asked; the add form keeps its text.
      onCancelVerify: () => {
        const typed = typedNow();
        showContributions(data, { typed: { add: typed.add, evidence: state.verifying ? without(typed.evidence, state.verifying) : typed.evidence } }, true);
      },
      onVerify: (id, fields) => act('contribution-verify', { contribution_id: id, ...fields }, 'Verified, with your evidence.'),
    };
    const view = renderContributions(doc, data, { ...options, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
    else show(view, moveFocus);
  };

  /**
   * Save text as a file through the browser. The app itself writes nothing:
   * the browser saves exactly the text the manager reviewed, and nothing is sent.
   * @param {string} filename
   * @param {string} text
   */
  const saveFile = (filename, text) => {
    const view = doc.defaultView;
    if (!view) return;
    const url = view.URL.createObjectURL(new view.Blob([text], { type: 'text/markdown;charset=utf-8' }));
    const link = doc.createElement('a');
    link.href = url;
    link.download = filename;
    link.hidden = true;
    doc.body.append(link);
    link.click();
    link.remove();
    view.setTimeout(() => view.URL.revokeObjectURL(url), 10000);
  };

  /**
   * Help and feedback: pilot feedback kept here, exported only as previewed.
   * @param {import('./views.mjs').PilotFeedback} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, deleting?: string | null, typed?: Record<string, string>,
   *   preview?: import('./views.mjs').PilotFeedbackPreview | null, exported?: import('./views.mjs').PilotFeedbackExport | null }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showHelp = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    /** @param {Partial<typeof state>} next @param {string} [selector] */
    const redraw = (next, selector) => showHelp(data, { typed: typedPilot(main), ...next }, true, selector);
    /**
     * Write, then reload the list from the records. Any preview is withdrawn,
     * because what an export would hold may have changed.
     * @param {WriteCommand} command
     * @param {Record<string, string>} body
     * @param {string} done
     */
    const act = async (command, body, done) => {
      const typed = typedPilot(main);
      main.replaceChildren(renderHelp(doc, data, { ...options, ...state, typed, busy: true }));
      const { failure } = await write(command, body);
      if (mine !== generation) return;
      if (failure) {
        showHelp(data, { typed, notice: failure }, true);
        return;
      }
      const kept = command === 'pilot-feedback-add' ? { ...typed, summary: '' } : typed;
      const fresh = await reload('pilot-feedback', mine, {}, (message) => showHelp(data, {
        typed: kept, notice: { kind: 'error', text: `${done} The list could not be refreshed (${message}); open Help and feedback again to see it.` },
      }, true));
      if (!fresh) return;
      showHelp(/** @type {import('./views.mjs').PilotFeedback} */ (fresh), { typed: kept, notice: { kind: 'ok', text: done } }, true);
    };
    /** @type {import('./views.mjs').HelpOptions} */
    const options = {
      writable,
      onAdd: (fields) => act('pilot-feedback-add', fields, 'Saved on this computer. Nothing was sent.'),
      onAskDelete: (id) => redraw({ deleting: id }, `[data-record-id="${id}"] .button-row button`),
      onCancelDelete: () => redraw({}, '#pilot-heading'),
      onDelete: (id) => act('pilot-feedback-delete', { feedback_id: id }, 'Deleted. Its text is gone.'),
      onPreview: async () => {
        const typed = typedPilot(main);
        main.replaceChildren(renderHelp(doc, data, { ...options, ...state, typed, busy: true }));
        let envelope;
        try {
          envelope = await source.call('pilot-feedback-preview');
        } catch (error) {
          if (mine !== generation) return;
          showHelp(data, { typed, notice: { kind: 'error', text: error instanceof Error ? error.message : String(error) } }, true);
          return;
        }
        if (mine !== generation) return;
        if (!envelope.ok) {
          showHelp(data, { typed, notice: { kind: 'error', text: envelope.error.message } }, true);
          return;
        }
        const preview = /** @type {import('./views.mjs').PilotFeedbackPreview} */ (envelope.data);
        showHelp(data, { typed, preview }, true, '#pilot-preview-heading');
        announce(preview.can_export
          ? 'Showing exactly what will be shared. Nothing has been saved or sent.'
          : `This cannot be exported: ${preview.reason}`);
      },
      onCancelPreview: () => redraw({}, '#pilot-share-heading'),
      onExport: async (sha) => {
        const typed = typedPilot(main);
        main.replaceChildren(renderHelp(doc, data, { ...options, ...state, typed, busy: true }));
        const { envelope, failure } = await write('pilot-feedback-export', { sha256: sha });
        if (mine !== generation) return;
        if (failure || !envelope || !envelope.ok) {
          // The preview is withdrawn: whatever changed must be reviewed again.
          showHelp(data, { typed, notice: failure }, true);
          return;
        }
        const exported = /** @type {import('./views.mjs').PilotFeedbackExport} */ (envelope.data);
        saveFile(exported.filename, exported.text);
        const fresh = await reload('pilot-feedback', mine, {}, () => { /* the export itself worked */ });
        if (mine !== generation) return;
        showHelp(/** @type {import('./views.mjs').PilotFeedback} */ (fresh ?? data), {
          typed, exported,
          notice: { kind: 'ok', text: `Saved as ${exported.filename}. Nothing was sent: give the file to your pilot team yourself.` },
        }, true);
      },
      onSaveAgain: () => {
        if (state.exported) saveFile(state.exported.filename, state.exported.text);
        announce('Saved the same file again.');
      },
    };
    const view = renderHelp(doc, data, { ...options, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
    else show(view, moveFocus);
  };

  /**
   * @param {import('./views.mjs').Memory} data
   * @param {{ busy?: boolean, notice?: import('./views.mjs').Notice, editing?: string | null, deleting?: string | null, typed?: import('./views.mjs').MemoryTyped }} state
   * @param {boolean} moveFocus
   * @param {string} [focusSelector]
   */
  const showMemory = (data, state, moveFocus, focusSelector) => {
    const mine = generation;
    const typedNow = () => typedMemory(main, state.typed);
    /** @param {Record<string, string>} edits @param {string | undefined} id */
    const without = (edits, id) => Object.fromEntries(Object.entries(edits).filter(([key]) => key !== id));
    /**
     * @param {WriteCommand} command
     * @param {Record<string, string>} body
     * @param {string} done
     */
    const act = async (command, body, done) => {
      const before = typedNow();
      const saving = command === 'memory-add' ? 'add' : body.memory_id;
      main.replaceChildren(renderMemory(doc, data, { ...options, ...state, typed: before, busy: true, saving }));
      // The submitted form is read-only while it saves; everything else stays
      // editable, so read the view again afterwards: nothing typed is lost.
      const latest = () => typedMemory(main, before);
      const { failure } = await write(command, body);
      if (mine !== generation) return;
      if (failure) {
        showMemory(data, { editing: state.editing, notice: failure, typed: latest() }, true);
        return;
      }
      // The saved form starts empty; everything else keeps what was typed in it.
      const next = () => {
        const typed = latest();
        if (command === 'memory-add') return { editing: state.editing, typed: { add: {}, edits: typed.edits } };
        const done = command === 'memory-correct' || command === 'memory-delete';
        return {
          editing: done && state.editing === body.memory_id ? null : state.editing,
          typed: { add: typed.add, edits: done ? without(typed.edits, body.memory_id) : typed.edits },
        };
      };
      // If the save worked but the refresh fails, stay on this screen with the
      // unsaved text, rather than replacing it with the error page.
      const fresh = await reload('memory', mine, {}, (message) => showMemory(data, {
        ...next(), notice: { kind: 'error', text: `${done} The list could not be refreshed (${message}); open Memory again to see it.` },
      }, true));
      // Re-render from the fresh records, so every button acts on them.
      if (!fresh) return;
      showMemory(/** @type {import('./views.mjs').Memory} */ (fresh), { ...next(), notice: { kind: 'ok', text: done } }, true);
    };
    /** @type {import('./views.mjs').MemoryOptions} */
    const options = {
      writable,
      onAdd: (fields) => act('memory-add', fields, 'Remembered. It is used with “Think with this project”.'),
      onOpenCorrect: (id) => showMemory(data, { editing: id, typed: typedNow() }, true, `#correct-${id}`),
      onCancelCorrect: () => {
        const typed = typedNow();
        showMemory(data, { typed: { add: typed.add, edits: without(typed.edits, state.editing ?? undefined) } }, true);
      },
      onCorrect: (id, content) => act('memory-correct', { memory_id: id, content }, 'Corrected.'),
      onExclude: (id) => act('memory-exclude', { memory_id: id }, 'Excluded. It is kept but never sent.'),
      onInclude: (id) => act('memory-include', { memory_id: id }, 'In use again.'),
      // Focus lands on the confirmation, so the choice is made deliberately.
      onOpenDelete: (id) => showMemory(data, { editing: state.editing, deleting: id, typed: typedNow() }, true,
        `li[data-record-id="${id}"] .button-row button`),
      onCancelDelete: () => showMemory(data, { editing: state.editing, typed: typedNow() }, true),
      onDelete: (id) => act('memory-delete', { memory_id: id }, 'Deleted for good.'),
    };
    const view = renderMemory(doc, data, { ...options, ...state });
    if (state.notice || focusSelector) showAfterAction(view, state.notice, focusSelector);
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
