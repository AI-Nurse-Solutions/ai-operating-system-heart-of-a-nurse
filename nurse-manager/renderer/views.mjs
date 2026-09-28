// @ts-check
// Pure view functions: IPC data in, DOM out (build step 3.5).
//
// Rules this module keeps, because the plan and the contract require them:
// - Record text is only ever assigned with textContent. There is no
//   innerHTML anywhere, so a task title can never become markup.
// - Status is never carried by color alone: every badge is icon + text.
// - Empty, sample, and unavailable states say so; nothing silently vanishes.
// - No progress percentage is shown: counts are shown with their meaning.
// - Every task element carries data-record-id, the same id in every view.

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').MissionControl} MissionControl */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Board} Board */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Table} Table */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').TableRow} TableRow */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').ProjectDashboard} ProjectDashboard */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').TaskStatus} TaskStatus */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').IpcError} IpcError */
/** @typedef {'ascending' | 'descending'} SortDirection */
/** @typedef {'task' | 'project' | 'owner' | 'due_date' | 'status' | 'reviewer' | 'evidence' | 'next_action'} TableColumn */

/** @type {Record<TaskStatus, string>} */
export const STATUS_LABELS = {
  idea: 'Idea',
  ready: 'Ready',
  in_progress: 'In progress',
  needs_judgment: 'Needs my judgment',
  completed: 'Completed',
};

/** @type {Record<TableColumn, string>} */
export const COLUMN_LABELS = {
  task: 'Task',
  project: 'Project',
  owner: 'Owner',
  due_date: 'Due date',
  status: 'Status',
  reviewer: 'Reviewer',
  evidence: 'Evidence',
  next_action: 'Next action',
};

/**
 * Create an element. Children that are strings become text nodes.
 * @param {Document} doc
 * @param {string} tag
 * @param {Record<string, string>} [attrs]
 * @param {Array<Node | string | null | false>} [children]
 * @returns {HTMLElement}
 */
export function h(doc, tag, attrs = {}, children = []) {
  const el = doc.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) el.setAttribute(name, value);
  for (const child of children) {
    if (child === null || child === false) continue;
    el.append(typeof child === 'string' ? doc.createTextNode(child) : child);
  }
  return el;
}

/**
 * An icon-plus-text status badge. The icon is decorative; the text carries meaning.
 * @param {Document} doc
 * @param {string} kind
 * @param {string} icon
 * @param {string} label
 */
export function badge(doc, kind, icon, label) {
  return h(doc, 'span', { class: `badge badge--${kind}` }, [
    h(doc, 'span', { 'aria-hidden': 'true', class: 'badge__icon' }, [icon]),
    ` ${label}`,
  ]);
}

/**
 * @param {Document} doc
 * @param {string} title
 * @param {string} [subtitle]
 */
function viewHeading(doc, title, subtitle) {
  return h(doc, 'div', { class: 'view-heading' }, [
    h(doc, 'h1', { tabindex: '-1', class: 'view-title' }, [title]),
    subtitle ? h(doc, 'p', { class: 'view-subtitle' }, [subtitle]) : null,
  ]);
}

/**
 * A Mission Control section with an honest empty or unavailable state.
 * @param {Document} doc
 * @param {string} id
 * @param {string} title
 * @param {{ state: string, items: readonly unknown[], empty_message: string }} section
 * @param {() => HTMLElement} renderItems
 */
function missionSection(doc, id, title, section, renderItems) {
  const headingId = `${id}-heading`;
  let body;
  if (section.state === 'unavailable') {
    body = h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Unavailable'), ' ', section.empty_message,
    ]);
  } else if (section.state === 'empty' || section.items.length === 0) {
    body = h(doc, 'p', { class: 'section-state section-state--empty' }, [section.empty_message]);
  } else {
    body = renderItems();
  }
  return h(doc, 'section', { class: 'mc-section', id, 'aria-labelledby': headingId }, [
    h(doc, 'h2', { id: headingId }, [title]),
    body,
  ]);
}

/**
 * @param {number} n
 * @param {string} one
 * @param {string} many
 */
const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;

/**
 * Mission Control: what needs my attention?
 * @param {Document} doc
 * @param {MissionControl} data
 */
export function renderMission(doc, data) {
  const root = h(doc, 'div', { class: 'view view--mission' });
  root.append(viewHeading(doc, 'Mission Control', `Week of ${data.week_of} · Today ${data.today}`));

  const grid = h(doc, 'div', { class: 'mc-grid' });
  grid.append(
    missionSection(doc, 'priorities', "This week's priorities", data.priorities, () =>
      h(doc, 'ol', { class: 'priority-list' }, data.priorities.items.map((p) =>
        h(doc, 'li', {}, [p.text])))),

    missionSection(doc, 'judgment', 'Needs my judgment', data.needs_my_judgment, () =>
      h(doc, 'ul', { class: 'item-list' }, data.needs_my_judgment.items.map((item) => {
        const kinds = {
          task: badge(doc, 'judgment', '◇', 'Decision'),
          draft: badge(doc, 'review', '✎', 'Draft to review'),
          action: badge(doc, 'review', '!', 'Approval needed'),
        };
        return h(doc, 'li', { 'data-record-id': item.id }, [
          kinds[item.kind], ' ', h(doc, 'span', { class: 'item-title' }, [item.title]),
          item.owner ? h(doc, 'span', { class: 'item-meta' }, [` · ${item.owner}`]) : null,
        ]);
      }))),

    missionSection(doc, 'projects', 'Projects in motion', data.projects_in_motion, () =>
      h(doc, 'ul', { class: 'card-list' }, data.projects_in_motion.items.map((p) =>
        h(doc, 'li', { class: 'card', 'data-record-id': p.id }, [
          h(doc, 'h3', { class: 'card__title' }, [
            h(doc, 'a', { href: `#/project/${encodeURIComponent(p.id)}` }, [p.title]),
          ]),
          h(doc, 'p', { class: 'card__meta' }, [`Owner: ${p.owner}`]),
          p.next_milestone ? h(doc, 'p', { class: 'card__meta' }, [`Next: ${p.next_milestone}`]) : null,
          h(doc, 'p', { class: 'card__counts' }, [
            `${count(p.open_tasks, 'open task', 'open tasks')} · ${p.completed_tasks} completed`,
            p.blocked_tasks ? ' · ' : '',
            p.blocked_tasks ? badge(doc, 'blocked', '⛔', `${p.blocked_tasks} blocked`) : null,
          ]),
        ])))),

    missionSection(doc, 'follow-ups', 'Follow-ups due soon', data.follow_ups, () =>
      h(doc, 'ul', { class: 'item-list' }, data.follow_ups.items.map((f) =>
        h(doc, 'li', { 'data-record-id': f.id }, [
          h(doc, 'time', { datetime: f.due_date, class: 'item-date' }, [f.due_date]),
          ' ',
          f.overdue ? badge(doc, 'overdue', '⚠', 'Overdue') : null,
          f.overdue ? ' ' : '',
          h(doc, 'span', { class: 'item-title' }, [f.title]),
          h(doc, 'span', { class: 'item-meta' }, [` · ${f.owner}`]),
        ])))),

    missionSection(doc, 'assistants', 'Assistants at work', data.assistants_at_work, () =>
      h(doc, 'ul', {}, [])),

    missionSection(doc, 'accepted', 'Recently accepted outputs', data.recent_accepted_outputs, () =>
      h(doc, 'ul', { class: 'item-list' }, data.recent_accepted_outputs.items.map((a) =>
        h(doc, 'li', { 'data-record-id': a.id }, [
          badge(doc, 'accepted', '✓', 'Accepted'), ' ',
          h(doc, 'span', { class: 'item-title' }, [a.title]),
          h(doc, 'span', { class: 'item-meta' }, [` · ${a.accepted_by}, ${a.accepted_at}`]),
        ])))),
  );
  root.append(grid);

  const counts = data.task_counts;
  root.append(h(doc, 'section', { class: 'mc-section mc-counts', 'aria-labelledby': 'counts-heading' }, [
    h(doc, 'h2', { id: 'counts-heading' }, ['Tasks by status']),
    h(doc, 'dl', { class: 'count-list' }, /** @type {TaskStatus[]} */ (Object.keys(STATUS_LABELS)).flatMap((s) => [
      h(doc, 'dt', {}, [STATUS_LABELS[s]]),
      h(doc, 'dd', { 'data-status': s }, [String(counts[s])]),
    ])),
  ]));
  return root;
}

/**
 * Board: who owns the next action, grouped by status. Read-only here.
 * @param {Document} doc
 * @param {Board} data
 */
export function renderBoard(doc, data) {
  const root = h(doc, 'div', { class: 'view view--board' });
  root.append(viewHeading(doc, 'Board', 'Tasks grouped by status. Completing a task needs recorded evidence.'));
  const columns = h(doc, 'div', { class: 'board' });
  for (const column of data.columns) {
    const headingId = `column-${column.status}`;
    const list = column.cards.length
      ? h(doc, 'ul', { class: 'board__cards' }, column.cards.map((card) => {
        const titleId = `card-${card.id}`;
        return h(doc, 'li', {}, [
          h(doc, 'article', { class: 'card task-card', 'data-record-id': card.id, 'aria-labelledby': titleId }, [
            h(doc, 'h3', { class: 'card__title', id: titleId }, [card.title]),
            h(doc, 'p', { class: 'card__meta' }, [`Owner: ${card.owner}`]),
            h(doc, 'p', { class: 'card__meta' }, [
              'Due: ',
              card.due_date ? h(doc, 'time', { datetime: card.due_date }, [card.due_date]) : 'no date',
            ]),
            card.project ? h(doc, 'p', { class: 'card__meta' }, [`Project: ${card.project}`]) : null,
            card.blocked || card.paused
              ? h(doc, 'p', { class: 'card__badges' }, [
                card.blocked ? badge(doc, 'blocked', '⛔', `Blocked: ${card.blocked_reason}`) : null,
                card.blocked && card.paused ? ' ' : '',
                card.paused ? badge(doc, 'paused', '⏸', 'Paused') : null,
              ])
              : null,
          ]),
        ]);
      }))
      : h(doc, 'p', { class: 'section-state section-state--empty' }, ['No tasks here.']);
    columns.append(h(doc, 'section', { class: 'board__column', 'aria-labelledby': headingId, 'data-status': column.status }, [
      h(doc, 'h2', { id: headingId }, [
        column.label, ' ', h(doc, 'span', { class: 'board__count' }, [`(${count(column.count, 'task', 'tasks')})`]),
      ]),
      list,
    ]));
  }
  root.append(columns);
  return root;
}

/**
 * Sort table rows the way the core does: blanks last, then text order, then id.
 * @param {readonly TableRow[]} rows
 * @param {TableColumn} column
 * @param {SortDirection} direction
 * @returns {TableRow[]}
 */
export function sortRows(rows, column, direction) {
  /** @param {TableRow} r */
  const value = (r) => r[column];
  /** @param {TableRow} a @param {TableRow} b */
  const cmp = (a, b) => {
    const va = value(a); const vb = value(b);
    const ea = va === null || va === ''; const eb = vb === null || vb === '';
    if (ea !== eb) return ea ? 1 : -1; // blanks last, in both directions
    if (!ea && va !== vb) {
      const order = String(va) < String(vb) ? -1 : 1;
      return direction === 'ascending' ? order : -order;
    }
    return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  };
  return [...rows].sort(cmp);
}

/**
 * A sortable task table. Shared by the task list and project dashboards so a
 * task looks and sorts the same wherever it appears.
 * @param {Document} doc
 * @param {readonly TableRow[]} rows
 * @param {readonly TableColumn[]} columns
 * @param {{ column: TableColumn, direction: SortDirection }} sort
 * @param {(column: TableColumn) => void} onSort
 * @param {string} captionId
 * @param {string} captionLead e.g. "All tasks"
 */
function taskTable(doc, rows, columns, sort, onSort, captionId, captionLead) {
  const headRow = h(doc, 'tr', {}, columns.map((column) => {
    const active = sort.column === column;
    const button = h(doc, 'button', { type: 'button', class: 'sort-button', 'data-column': column }, [
      COLUMN_LABELS[column],
      h(doc, 'span', { 'aria-hidden': 'true', class: 'sort-button__icon' }, [
        active ? (sort.direction === 'ascending' ? ' ▲' : ' ▼') : ' ↕',
      ]),
    ]);
    button.addEventListener('click', () => onSort(column));
    return h(doc, 'th', { scope: 'col', 'aria-sort': active ? sort.direction : 'none' }, [button]);
  }));
  const body = h(doc, 'tbody', {}, sortRows(rows, sort.column, sort.direction).map((row) =>
    h(doc, 'tr', { 'data-record-id': row.id }, columns.map((column) => {
      if (column === 'status') {
        return h(doc, 'td', {}, [
          STATUS_LABELS[row.status],
          row.blocked ? ' ' : '', row.blocked ? badge(doc, 'blocked', '⛔', 'Blocked') : null,
          row.paused ? ' ' : '', row.paused ? badge(doc, 'paused', '⏸', 'Paused') : null,
        ]);
      }
      const value = row[column];
      return h(doc, 'td', column === 'due_date' ? { class: 'cell--date' } : {}, [
        value === null || value === '' ? '—' : String(value),
      ]);
    }))));
  const summary = `${captionLead}, sorted by ${COLUMN_LABELS[sort.column]}, ${sort.direction}`;
  // The caption names the table for assistive technology; a visible copy
  // sits outside the scroll area so it is never clipped on a narrow screen.
  return h(doc, 'div', { class: 'table-block' }, [
    h(doc, 'p', { class: 'table-summary', 'aria-hidden': 'true' }, [summary]),
    h(doc, 'div', { class: 'table-scroll', role: 'region', 'aria-labelledby': captionId, tabindex: '0' }, [
      h(doc, 'table', { class: 'task-table' }, [
        h(doc, 'caption', { id: captionId, class: 'visually-hidden' }, [summary]),
        h(doc, 'thead', {}, [headRow]),
        body,
      ]),
    ]),
  ]);
}

/**
 * Table: every task, sortable by any column.
 * @param {Document} doc
 * @param {Table} data
 * @param {{ column: TableColumn, direction: SortDirection }} sort
 * @param {(column: TableColumn) => void} onSort
 */
export function renderTable(doc, data, sort, onSort) {
  const root = h(doc, 'div', { class: 'view view--table' });
  root.append(viewHeading(doc, 'Tasks', `${count(data.rows.length, 'task', 'tasks')} in this workspace.`));
  if (data.rows.length === 0) {
    root.append(h(doc, 'p', { class: 'section-state section-state--empty' }, ['No tasks yet. Capture one to start.']));
    return root;
  }
  root.append(taskTable(doc, data.rows, /** @type {TableColumn[]} */ (data.columns), sort, onSort,
    'tasks-caption', 'All tasks'));
  return root;
}

/**
 * A dashboard section with an honest empty state.
 * @param {Document} doc
 * @param {string} id
 * @param {string} title
 * @param {boolean} empty
 * @param {string} emptyMessage
 * @param {() => HTMLElement} renderBody
 */
function dashboardSection(doc, id, title, empty, emptyMessage, renderBody) {
  const headingId = `${id}-heading`;
  return h(doc, 'section', { class: 'mc-section', id, 'aria-labelledby': headingId }, [
    h(doc, 'h2', { id: headingId }, [title]),
    empty ? h(doc, 'p', { class: 'section-state section-state--empty' }, [emptyMessage]) : renderBody(),
  ]);
}

/**
 * Project dashboard: what will move this initiative forward?
 * Readiness is stated as facts; there is no score and no percentage.
 * @param {Document} doc
 * @param {ProjectDashboard} data
 * @param {{ column: TableColumn, direction: SortDirection }} sort
 * @param {(column: TableColumn) => void} onSort
 * @param {ThinkOptions} [think] the "Think with this project" section, when offered
 * @param {FeedbackOptions} [feedback] adding and addressing feedback, when offered
 */
export function renderProject(doc, data, sort, onSort, think, feedback) {
  const { project, readiness } = data;
  const root = h(doc, 'div', { class: 'view view--project' });
  root.append(h(doc, 'nav', { 'aria-label': 'Breadcrumb', class: 'breadcrumb' }, [
    h(doc, 'a', { href: '#/mission' }, ['← Mission Control']),
  ]));
  const statusLabel = { active: 'Active', paused: 'Paused', completed: 'Completed' }[project.status];
  root.append(viewHeading(doc, project.title, `Accountable owner: ${project.owner} · ${statusLabel}`));

  /** @type {HTMLElement[]} */
  const facts = [];
  facts.push(readiness.has_next_milestone
    ? h(doc, 'li', {}, [`Next milestone: ${project.next_milestone}`])
    : h(doc, 'li', {}, [badge(doc, 'review', '!', 'No next milestone'), ' Set one so the team knows what comes next.']));
  facts.push(h(doc, 'li', {}, [
    `${count(readiness.open_tasks, 'open task', 'open tasks')} · ${readiness.completed_tasks} completed`,
  ]));
  if (readiness.blocked_tasks) {
    facts.push(h(doc, 'li', {}, [badge(doc, 'blocked', '⛔', count(readiness.blocked_tasks, 'task blocked', 'tasks blocked'))]));
  }
  if (readiness.needs_judgment) {
    facts.push(h(doc, 'li', {}, [badge(doc, 'judgment', '◇', count(readiness.needs_judgment, 'decision waiting on you', 'decisions waiting on you'))]));
  }
  if (readiness.overdue_tasks) {
    facts.push(h(doc, 'li', {}, [badge(doc, 'overdue', '⚠', count(readiness.overdue_tasks, 'task overdue', 'tasks overdue'))]));
  }
  if (readiness.open_feedback) {
    facts.push(h(doc, 'li', {}, [count(readiness.open_feedback, 'feedback item is', 'feedback items are'), ' still open.']));
  }
  if (readiness.tasks_without_next_action) {
    facts.push(h(doc, 'li', {}, [
      count(readiness.tasks_without_next_action, 'active task has', 'active tasks have'), ' no next action written down.',
    ]));
  }

  const grid = h(doc, 'div', { class: 'mc-grid' });
  grid.append(
    dashboardSection(doc, 'purpose', 'Purpose', !project.purpose, 'No purpose recorded.', () =>
      h(doc, 'p', { class: 'section-state' }, [project.purpose])),
    dashboardSection(doc, 'readiness', 'Readiness', false, '', () =>
      h(doc, 'ul', { class: 'item-list' }, facts)),
    dashboardSection(doc, 'decisions', 'Decisions', data.decisions.length === 0,
      'No decisions recorded for this project yet.', () =>
        h(doc, 'ul', { class: 'item-list' }, data.decisions.map((d) =>
          h(doc, 'li', { 'data-record-id': d.id }, [
            h(doc, 'span', { class: 'item-title' }, [d.question]), ` — ${d.decision}`,
            h(doc, 'span', { class: 'item-meta' }, [` (${d.decided_by}, `,
              h(doc, 'time', { datetime: d.decided_on }, [d.decided_on]), ')']),
            d.rationale ? h(doc, 'span', { class: 'item-meta' }, [` Rationale: ${d.rationale}`]) : null,
          ])))),
    dashboardSection(doc, 'resources', 'Resources', data.resources.length === 0,
      'No resources linked to this project yet.', () =>
        h(doc, 'ul', { class: 'item-list' }, data.resources.map((r) =>
          h(doc, 'li', { 'data-record-id': r.id }, [
            h(doc, 'span', { class: 'item-title' }, [r.title]),
            h(doc, 'span', { class: 'item-meta' }, [` · ${r.kind} · ${r.reference}`]),
            r.review_overdue ? ' ' : '',
            r.review_overdue ? badge(doc, 'overdue', '⚠', `Review overdue since ${r.review_date}`) : null,
          ])))),
    dashboardSection(doc, 'evidence', 'Evidence of completed work', data.evidence.length === 0,
      'No completed tasks with recorded evidence yet.', () =>
        h(doc, 'ul', { class: 'item-list' }, data.evidence.map((e) =>
          h(doc, 'li', { 'data-record-id': e.task_id }, [
            badge(doc, 'accepted', '✓', 'Completed'), ' ',
            h(doc, 'span', { class: 'item-title' }, [e.task]),
            h(doc, 'span', { class: 'item-meta' }, [` · ${e.evidence}`]),
          ])))),
  );
  root.append(grid);

  const tasksHeading = 'project-tasks-heading';
  root.append(h(doc, 'section', { class: 'project-tasks', 'aria-labelledby': tasksHeading }, [
    h(doc, 'h2', { id: tasksHeading }, ['Tasks']),
    data.tasks.length === 0
      ? h(doc, 'p', { class: 'section-state section-state--empty' }, ['No tasks in this project yet.'])
      : taskTable(doc, data.tasks, ['task', 'owner', 'due_date', 'status', 'next_action', 'evidence'],
        sort, onSort, 'project-tasks-caption', `${project.title} tasks`),
  ]));
  root.append(feedbackSection(doc, data, feedback));
  root.append(notesSection(doc, data.notes));
  if (think) root.append(thinkSection(doc, think));
  return root;
}

/** @type {Record<'worked' | 'change' | 'question', [string, string, string]>} */
const FEEDBACK_KINDS = {
  worked: ['accepted', '✓', 'What worked'],
  change: ['review', '↻', 'Change asked for'],
  question: ['judgment', '?', 'Question'],
};

/**
 * Feedback about the project's work: from a group or role, closed only
 * with a written response.
 * @param {Document} doc
 * @param {ProjectDashboard} data
 * @param {FeedbackOptions} [options]
 */
function feedbackSection(doc, data, options) {
  const busy = Boolean(options?.busy);
  const items = data.feedback;
  const open = items.filter((f) => f.status === 'open').length;
  const section = h(doc, 'section', { class: 'mc-section feedback-section', id: 'feedback', 'aria-labelledby': 'feedback-heading' }, [
    h(doc, 'h2', { id: 'feedback-heading', tabindex: '-1' }, [`Feedback (${open} open)`]),
    h(doc, 'p', { class: 'field-hint', id: 'feedback-rule' }, [
      "Feedback about the project's work, from a group or role. Not about a named person or anyone's performance.",
    ]),
  ]);
  const notice = noticeBlock(doc, options?.notice);
  if (notice) section.append(notice);
  if (items.length === 0) {
    section.append(h(doc, 'p', { class: 'section-state section-state--empty' }, ['No feedback recorded yet.']));
  } else {
    section.append(h(doc, 'ul', { class: 'card-list' }, items.map((f) => {
      const [kind, icon, label] = FEEDBACK_KINDS[f.kind];
      const item = h(doc, 'li', { class: 'card', 'data-record-id': f.id }, [
        h(doc, 'p', { class: 'card__badges' }, [
          badge(doc, kind, icon, label), ` from ${f.from_group}, ${f.received_on}`,
        ]),
        h(doc, 'p', { class: 'card__title' }, [f.summary]),
      ]);
      if (f.status === 'addressed') {
        item.append(h(doc, 'p', { class: 'card__meta' }, [
          badge(doc, 'accepted', '✓', `Addressed ${f.addressed_on ?? ''}`.trim()), ' ', f.response,
        ]));
      } else if (options?.writable) {
        if (options.addressing === f.id) {
          const response = /** @type {HTMLTextAreaElement} */ (h(doc, 'textarea', {
            id: `response-${f.id}`, rows: '2', maxlength: '1000', required: '',
          }));
          const markButton = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' }, ['Mark addressed']));
          markButton.disabled = busy;
          const form = h(doc, 'form', { class: 'onboarding-form' }, [
            h(doc, 'p', { class: 'field' }, [
              h(doc, 'label', { for: `response-${f.id}` }, ['How was it addressed?']),
              response,
            ]),
            h(doc, 'p', { class: 'button-row' }, [
              markButton,
              button(doc, 'Cancel', busy, () => options.onCancelAddress(), 'secondary-button'),
            ]),
          ]);
          form.addEventListener('submit', (event) => {
            event.preventDefault();
            options.onAddress(f.id, response.value.trim());
          });
          item.append(form);
        } else {
          item.append(h(doc, 'p', { class: 'button-row' }, [
            button(doc, 'Mark addressed…', busy, () => options.onStartAddress(f.id), 'secondary-button'),
          ]));
        }
      } else {
        item.append(h(doc, 'p', { class: 'card__meta' }, [badge(doc, 'review', '!', 'Open')]));
      }
      return item;
    })));
  }
  if (options?.writable) {
    const fromInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
      id: 'feedback-from', type: 'text', required: '', maxlength: '80', autocomplete: 'off',
      'aria-describedby': 'feedback-rule',
    }));
    const kindSelect = /** @type {HTMLSelectElement} */ (h(doc, 'select', { id: 'feedback-kind' },
      Object.entries(FEEDBACK_KINDS).map(([value, [, , label]]) => h(doc, 'option', { value }, [label]))));
    const dateInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
      id: 'feedback-date', type: 'date', required: '', max: data.today,
    }));
    dateInput.value = data.today;
    const summary = /** @type {HTMLTextAreaElement} */ (h(doc, 'textarea', {
      id: 'feedback-summary', rows: '2', required: '', maxlength: '1000',
    }));
    const submit = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' }, ['Add feedback']));
    submit.disabled = busy;
    const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'feedback-add-heading' }, [
      h(doc, 'h3', { id: 'feedback-add-heading' }, ['Add feedback']),
      h(doc, 'p', { class: 'field' }, [
        h(doc, 'label', { for: 'feedback-from' }, ['From (a group or role)']), fromInput,
      ]),
      h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'feedback-kind' }, ['Kind']), kindSelect]),
      h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'feedback-date' }, ['Received on']), dateInput]),
      h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'feedback-summary' }, ['What was said']), summary]),
      submit,
    ]);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      options.onAdd({
        from_group: fromInput.value.trim(), kind: kindSelect.value,
        received_on: dateInput.value, summary: summary.value.trim(),
      });
    });
    section.append(form);
  }
  return section;
}

/**
 * AI answers the manager chose to keep. Each says where it came from.
 * @param {Document} doc
 * @param {ProjectDashboard['notes']} notes
 */
function notesSection(doc, notes) {
  const section = h(doc, 'section', { class: 'mc-section notes-section', id: 'notes', 'aria-labelledby': 'notes-heading' }, [
    h(doc, 'h2', { id: 'notes-heading', tabindex: '-1' }, [`Notes (${notes.length})`]),
  ]);
  if (notes.length === 0) {
    section.append(h(doc, 'p', { class: 'section-state section-state--empty' }, [
      'No notes yet. Ask a question below and keep an answer you want to remember.',
    ]));
    return section;
  }
  for (const note of notes) {
    section.append(h(doc, 'article', { class: 'note', 'data-record-id': note.id, 'aria-label': note.question }, [
      h(doc, 'h3', {}, [note.question]),
      h(doc, 'p', { class: 'card__meta' }, [
        badge(doc, 'accepted', '✓', 'Kept'),
        ` Written by the AI model “${note.model}”; kept by ${note.kept_by} on ${note.kept_at.slice(0, 10)}.`,
      ]),
      markdownBlock(doc, note.body_markdown, `Note: ${note.question}`),
    ]));
  }
  return section;
}

/**
 * "Think with this project": ask the AI model a question, after seeing
 * exactly what would be sent. The answer is a suggestion and is not saved.
 * @param {Document} doc
 * @param {ThinkOptions} think
 */
function thinkSection(doc, think) {
  const busy = Boolean(think.busy);
  const section = h(doc, 'section', { class: 'mc-section think-section', id: 'think', 'aria-labelledby': 'think-heading' }, [
    h(doc, 'h2', { id: 'think-heading' }, ['Think with this project']),
    h(doc, 'p', {}, [
      'Ask the AI model a question about this project. You will see exactly what would be sent before anything is. ',
      'Answers are suggestions. Nothing is saved unless you keep an answer as a project note.',
    ]),
  ]);
  const notice = noticeBlock(doc, think.notice);
  if (notice) section.append(notice);
  if (!think.writable) {
    section.append(h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Read-only'), ' Asking is available in the Nurse AI OS app.',
    ]));
    return section;
  }
  const questionInput = /** @type {HTMLTextAreaElement} */ (h(doc, 'textarea', {
    id: 'think-question', name: 'question', rows: '3', maxlength: '500', required: '',
    'aria-describedby': 'think-question-hint',
  }));
  questionInput.value = think.question ?? '';
  // A preview is only for the question it showed: editing withdraws it, so
  // nothing can be sent until the new question is previewed.
  questionInput.addEventListener('input', () => {
    const panel = section.querySelector('#think-ai-preview');
    if (panel) {
      panel.remove();
      think.onEdit?.(questionInput.value);
    }
  });
  const submit = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' },
    ['Preview what will be sent']));
  submit.disabled = busy;
  const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'think-heading' }, [
    h(doc, 'p', { class: 'field' }, [
      h(doc, 'label', { for: 'think-question' }, ['What do you want to think through?']),
      h(doc, 'span', { class: 'field-hint', id: 'think-question-hint' }, [
        'For example: what should I do first, or what is at risk before the milestone? Leave out names of patients and staff.',
      ]),
      questionInput,
    ]),
    submit,
  ]);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    think.onPreview(questionInput.value.trim());
  });
  section.append(form);
  if (think.preview) {
    section.append(previewPanel(doc, think.preview, busy, think,
      { prefix: 'think-', level: 'h3', promptLabel: "Your question and this project's records" }));
  }
  if (think.answer && think.answer.answered_by_model) {
    section.append(h(doc, 'div', { class: 'think-answer', 'aria-labelledby': 'think-answer-heading' }, [
      h(doc, 'h3', { id: 'think-answer-heading' }, ['AI suggestion']),
      h(doc, 'p', { class: 'card__badges' }, [
        badge(doc, 'review', '!', 'Not saved'),
        ` From the AI model “${think.answer.model}”. Check it against the records it cites; you decide what to do.`,
      ]),
      markdownBlock(doc, think.answer.answer, 'AI suggestion'),
      think.onKeep
        ? h(doc, 'p', { class: 'button-row' }, [
          button(doc, 'Keep as a project note', busy, think.onKeep, 'secondary-button'),
        ])
        : null,
    ]));
  }
  return section;
}

/**
 * A truthful failure. The message comes from the core and is shown as text.
 * @param {Document} doc
 * @param {string} viewName
 * @param {IpcError} error
 */
export function renderError(doc, viewName, error) {
  return h(doc, 'div', { class: 'view view--error' }, [
    viewHeading(doc, `Couldn't load ${viewName}`),
    h(doc, 'p', { role: 'alert', class: 'error-message' }, [
      badge(doc, 'error', '✕', 'Error'), ' ', error.message,
    ]),
    h(doc, 'p', { class: 'view-subtitle' }, [`Nothing was changed. (${error.type})`]),
  ]);
}

/**
 * First run in the local app: try the synthetic sample, or start your own.
 * The data rules are stated before anything is typed.
 * @param {Document} doc
 * @param {{ onSample: () => void, onCreate: (name: string, owner: string) => void }} handlers
 * @param {{ busy?: boolean, error?: string }} [state]
 */
export function renderOnboarding(doc, handlers, state = {}) {
  const busy = Boolean(state.busy);
  const root = h(doc, 'div', { class: 'view view--onboarding' });
  root.append(viewHeading(doc, 'Welcome to Nurse AI OS',
    'Organize your manager work in one place. Everything stays on this computer.'));
  root.append(h(doc, 'p', { class: 'onboarding-rules', role: 'note' }, [
    badge(doc, 'review', '!', 'Before you start'), ' ',
    'This workspace is for your own planning with public, synthetic, or your own permitted material. ',
    'Keep patient information, staff performance, and confidential employer material out of it.',
  ]));
  if (state.error) {
    root.append(h(doc, 'p', { role: 'alert', class: 'error-message' }, [
      badge(doc, 'error', '✕', 'Not created'), ' ', state.error,
    ]));
  }

  const sampleButton = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'button', class: 'primary-button' },
    ['Explore the sample workspace']));
  sampleButton.disabled = busy;
  sampleButton.addEventListener('click', () => handlers.onSample());

  const nameInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
    id: 'ws-name', name: 'name', type: 'text', required: '', maxlength: '200', autocomplete: 'off',
  }));
  const ownerInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
    id: 'ws-owner', name: 'owner', type: 'text', required: '', maxlength: '200', autocomplete: 'name',
  }));
  const createButton = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' },
    ['Create my workspace']));
  createButton.disabled = busy;
  const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'own-heading' }, [
    h(doc, 'p', { class: 'field' }, [
      h(doc, 'label', { for: 'ws-name' }, ['Workspace name']),
      nameInput,
    ]),
    h(doc, 'p', { class: 'field' }, [
      h(doc, 'label', { for: 'ws-owner' }, ['Your name']),
      h(doc, 'span', { class: 'field-hint', id: 'owner-hint' }, [
        'You are the accountable manager for this workspace.',
      ]),
      ownerInput,
    ]),
    createButton,
  ]);
  ownerInput.setAttribute('aria-describedby', 'owner-hint');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    handlers.onCreate(nameInput.value.trim(), ownerInput.value.trim());
  });

  root.append(h(doc, 'div', { class: 'mc-grid' }, [
    h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'sample-heading' }, [
      h(doc, 'h2', { id: 'sample-heading' }, ['Try the sample']),
      h(doc, 'p', { class: 'section-state' }, [
        'A synthetic week of a manager\'s projects, tasks, and decisions. Nothing in it is real.',
      ]),
      sampleButton,
    ]),
    h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'own-heading' }, [
      h(doc, 'h2', { id: 'own-heading' }, ['Start your own workspace']),
      form,
    ]),
  ]));
  return root;
}

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').WeeklyBrief} WeeklyBrief */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').AssistantStatus} AssistantStatus */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').AssistantPreview} AssistantPreview */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').AssistantDraft} AssistantDraft */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Revision} Revision */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').ProjectQuestionPreview} ProjectQuestionPreview */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').ProjectAnswer} ProjectAnswer */
/**
 * @typedef {object} ThinkOptions
 * @property {boolean} writable
 * @property {boolean} [busy]
 * @property {string} [question]
 * @property {ProjectQuestionPreview | null} [preview]
 * @property {ProjectAnswer | null} [answer]
 * @property {Notice} [notice]
 * @property {(question: string) => void} onPreview
 * @property {(sha: string) => void} onSend
 * @property {() => void} onCancel
 * @property {(question: string) => void} [onEdit] the question changed after a preview
 * @property {() => void} [onKeep] keep the shown answer as a project note
 */
/**
 * @typedef {object} FeedbackOptions
 * @property {boolean} writable
 * @property {boolean} [busy]
 * @property {Notice} [notice]
 * @property {string | null} [addressing] the feedback id whose response form is open
 * @property {(fields: Record<string, string>) => void} onAdd
 * @property {(id: string) => void} onStartAddress
 * @property {() => void} onCancelAddress
 * @property {(id: string, response: string) => void} onAddress
 */

/**
 * @typedef {object} Notice
 * @property {'ok' | 'fallback' | 'unanswered' | 'error'} kind
 * @property {string} text
 */

/** @param {Document} doc @param {Notice} [notice] */
function noticeBlock(doc, notice) {
  if (!notice) return null;
  const icons = {
    ok: ['accepted', '✓', 'Done'],
    fallback: ['review', '!', 'Drafted from your records'],
    unanswered: ['review', '!', 'No AI answer'],
    error: ['error', '✕', 'Not done'],
  };
  const [kind, icon, label] = icons[notice.kind];
  return h(doc, 'p', { class: 'notice', role: notice.kind === 'ok' ? 'status' : 'alert' }, [
    badge(doc, kind, icon, label), ' ', notice.text,
  ]);
}

/** @param {Document} doc @param {string} label @param {boolean} disabled @param {() => void} onClick @param {string} [kind] */
function button(doc, label, disabled, onClick, kind = 'primary-button') {
  const el = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'button', class: kind }, [label]));
  el.disabled = disabled;
  el.addEventListener('click', () => onClick());
  return el;
}

/**
 * Inline Markdown: **bold**, `code`, and _emphasis_, as elements with text
 * children only. Anything else stays literal text.
 * @param {Document} doc
 * @param {string} text
 * @returns {Array<Node | string>}
 */
function inline(doc, text) {
  /** @type {Array<Node | string>} */
  const out = [];
  const pattern = /\*\*([^*]+)\*\*|`([^`]+)`|(?<![A-Za-z0-9])_([^_]+)_(?![A-Za-z0-9])/g;
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    const at = match.index ?? 0;
    if (at > last) out.push(text.slice(last, at));
    if (match[1] !== undefined) out.push(h(doc, 'strong', {}, [match[1]]));
    else if (match[2] !== undefined) out.push(h(doc, 'code', {}, [match[2]]));
    else out.push(h(doc, 'em', {}, [match[3]]));
    last = at + match[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

/**
 * The small Markdown the brief uses — headings, quotes, lists, paragraphs —
 * rendered as elements with text children only. There is no HTML parsing,
 * so record text can never become markup.
 * @param {Document} doc
 * @param {string} markdown
 * @param {string} label
 */
export function markdownBlock(doc, markdown, label) {
  const root = h(doc, 'div', { class: 'brief-text', role: 'document', tabindex: '0', 'aria-label': label });
  /** @type {HTMLElement | null} */
  let list = null;
  for (const line of markdown.split('\n')) {
    const heading = /^(#{1,3}) (.*)$/.exec(line);
    const bullet = /^- (.*)$/.exec(line);
    const numbered = /^\d+\. (.*)$/.exec(line);
    if (bullet || numbered) {
      const tag = bullet ? 'ul' : 'ol';
      if (!list || list.tagName.toLowerCase() !== tag) {
        list = h(doc, tag, {});
        root.append(list);
      }
      list.append(h(doc, 'li', {}, inline(doc, (bullet || numbered || [])[1] ?? '')));
      continue;
    }
    list = null;
    if (!line.trim()) continue;
    if (heading) root.append(h(doc, `h${heading[1].length + 2}`, {}, inline(doc, heading[2])));
    else if (line.startsWith('> ')) root.append(h(doc, 'blockquote', {}, [h(doc, 'p', {}, inline(doc, line.slice(2)))]));
    else root.append(h(doc, 'p', {}, inline(doc, line)));
  }
  return root;
}

const GATE_LABELS = { data_rules: 'Data rules', edena: 'EDENA policy', budget: 'Budget' };

/**
 * The preview: exactly what asking the model would send, before anything is sent.
 * @param {Document} doc
 * @param {AssistantPreview | ProjectQuestionPreview} preview
 * @param {boolean} busy
 * @param {{ onSend: (sha: string) => void, onCancel: () => void, onRecords?: () => void }} handlers
 * @param {{ prefix?: string, level?: string, promptLabel?: string }} [layout]
 */
function previewPanel(doc, preview, busy, handlers, layout = {}) {
  const prefix = layout.prefix ?? '';
  const level = layout.level ?? 'h2';
  const sub = level === 'h2' ? 'h3' : 'h4';
  const promptLabel = layout.promptLabel ?? 'Text from your records';
  /** @param {string} label */
  const fallbackRow = (label) => h(doc, 'p', { class: 'button-row' }, [
    handlers.onRecords ? button(doc, label, busy, handlers.onRecords) : null,
    button(doc, 'Cancel', busy, handlers.onCancel, 'secondary-button'),
  ]);
  const panel = h(doc, 'section', { class: 'mc-section preview-panel', id: `${prefix}ai-preview`, 'aria-labelledby': `${prefix}preview-heading` }, [
    h(doc, level, { id: `${prefix}preview-heading`, tabindex: '-1' }, ['Before anything is sent']),
  ]);
  if (preview.provider === 'none') {
    panel.append(
      h(doc, 'p', { class: 'section-state' }, [badge(doc, 'unavailable', '○', 'No AI model'), ' ', preview.reason]),
      h(doc, 'p', {}, [h(doc, 'a', { href: '#/assistant' }, ['Set up AI assistance']), ' to connect a model on this computer.']),
      fallbackRow('Draft from my records'),
    );
    return panel;
  }
  panel.append(h(doc, 'p', {}, [
    `This is exactly what will be sent to the AI model “${preview.model}” on ${preview.runs_on}. Nothing has been sent yet.`,
  ]));
  panel.append(h(doc, 'ul', { class: 'check-list', 'aria-label': 'Checks before sending' }, preview.checks.map((check) =>
    h(doc, 'li', {}, [
      check.passed ? badge(doc, 'accepted', '✓', `${GATE_LABELS[check.gate]}: passed`)
        : badge(doc, 'blocked', '✕', `${GATE_LABELS[check.gate]}: stopped`),
      ' ', check.detail,
    ]))));
  panel.append(
    h(doc, sub, {}, ['Instructions to the model']),
    h(doc, 'pre', { class: 'sent-text', tabindex: '0', 'aria-label': 'Instructions to the model' }, [preview.system]),
    h(doc, sub, {}, [promptLabel]),
    h(doc, 'pre', { class: 'sent-text', tabindex: '0', 'aria-label': promptLabel }, [preview.prompt]),
  );
  if (preview.will_send) {
    panel.append(h(doc, 'p', { class: 'button-row' }, [
      button(doc, `Send to ${preview.model}`, busy, () => handlers.onSend(preview.prompt_sha256)),
      button(doc, 'Cancel', busy, handlers.onCancel, 'secondary-button'),
    ]));
  } else {
    panel.append(
      h(doc, 'p', { class: 'error-message' }, [badge(doc, 'blocked', '✕', 'Will not be sent'), ' ', preview.reason]),
      fallbackRow('Draft from my records'),
    );
  }
  return panel;
}

/**
 * The weekly brief: draft it (from records, or with AI after a preview), review it, accept it.
 * @param {Document} doc
 * @param {WeeklyBrief} data
 * @param {{
 *   writable: boolean, busy?: boolean, notice?: Notice, preview?: AssistantPreview | null,
 *   onRecords: () => void, onPreview: () => void, onSend: (sha: string) => void,
 *   onCancel: () => void, onAccept: (revision: Revision) => void,
 * }} options
 */
export function renderBrief(doc, data, options) {
  const busy = Boolean(options.busy);
  const root = h(doc, 'div', { class: 'view view--brief' });
  root.append(viewHeading(doc, 'Weekly brief', `Week of ${data.week_of}. Drafts are never final until you accept them.`));
  const notice = noticeBlock(doc, options.notice);
  if (notice) root.append(notice);

  if (options.writable) {
    root.append(h(doc, 'p', { class: 'button-row' }, [
      button(doc, 'Draft from my records', busy, options.onRecords),
      button(doc, 'Draft with AI…', busy, options.onPreview, 'secondary-button'),
    ]));
  } else {
    root.append(h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Read-only'), ' Drafting and accepting are available in the Nurse AI OS app.',
    ]));
  }
  if (options.preview) root.append(previewPanel(doc, options.preview, busy, options));

  const current = data.current;
  const section = h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'current-heading' }, [
    h(doc, 'h2', { id: 'current-heading' }, ['Current version']),
  ]);
  if (!current) {
    section.append(h(doc, 'p', { class: 'section-state section-state--empty' }, [
      'No brief for this week yet. Draft one from your records to start.',
    ]));
  } else {
    const rev = current.revision;
    const byAI = rev.created_by.startsWith('assistant:');
    const status = rev.status === 'accepted' ? badge(doc, 'accepted', '✓', 'Accepted')
      : rev.status === 'draft' ? badge(doc, 'review', '!', byAI ? 'AI draft — review it' : 'Draft — review it')
        : badge(doc, 'paused', '○', 'Superseded');
    section.append(
      h(doc, 'p', { class: 'card__badges' }, [status, ` Version ${rev.revision_no}.`]),
      markdownBlock(doc, current.markdown, `Weekly brief, version ${rev.revision_no}`),
    );
    if (options.writable && rev.status === 'draft') {
      section.append(h(doc, 'p', { class: 'button-row' }, [
        button(doc, 'I have reviewed it — accept this version', busy, () => options.onAccept(rev)),
      ]));
    }
  }
  root.append(section);
  if (data.accepted && current && data.accepted.id !== current.revision.id) {
    root.append(h(doc, 'p', { class: 'section-state' }, [
      `Version ${data.accepted.revision_no} is the accepted one until you accept a newer version.`,
    ]));
  }
  return root;
}

/**
 * AI assistance: off by default; a model on this computer if the manager connects one.
 * @param {Document} doc
 * @param {AssistantStatus} data
 * @param {{
 *   writable: boolean, busy?: boolean, notice?: Notice,
 *   onConnect: (model: string, endpoint: string) => void, onDisconnect: () => void,
 * }} options
 */
export function renderAssistant(doc, data, options) {
  const busy = Boolean(options.busy);
  const root = h(doc, 'div', { class: 'view view--assistant' });
  root.append(viewHeading(doc, 'AI assistance', 'Optional. Everything in Nurse AI OS works without it.'));
  const notice = noticeBlock(doc, options.notice);
  if (notice) root.append(notice);

  const connected = data.provider !== 'none';
  root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'now-heading' }, [
    h(doc, 'h2', { id: 'now-heading' }, ['Right now']),
    h(doc, 'p', { class: 'section-state' }, connected
      ? [badge(doc, 'accepted', '✓', 'Connected'), ` The AI model “${data.model}” on ${data.runs_on}. Text never leaves this computer.`]
      : [badge(doc, 'unavailable', '○', 'No AI model'), ' Nothing is connected, so nothing is ever sent anywhere.']),
    h(doc, 'p', {}, [`AI requests today: ${data.requests_today} of ${data.daily_request_limit}.`]),
    options.writable && connected
      ? h(doc, 'p', {}, [button(doc, 'Disconnect the AI model', busy, options.onDisconnect, 'secondary-button')])
      : null,
  ]));

  if (options.writable) {
    const modelInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
      id: 'ai-model', name: 'model', type: 'text', required: '', maxlength: '100', autocomplete: 'off',
      'aria-describedby': 'ai-model-hint',
    }));
    modelInput.value = data.model;
    const endpointInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
      id: 'ai-endpoint', name: 'endpoint', type: 'text', maxlength: '200', autocomplete: 'off',
      'aria-describedby': 'ai-endpoint-hint',
    }));
    endpointInput.value = data.endpoint || 'http://127.0.0.1:11434';
    const submit = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' },
      [connected ? 'Save' : 'Connect']));
    submit.disabled = busy;
    const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'local-heading' }, [
      h(doc, 'p', { class: 'field' }, [
        h(doc, 'label', { for: 'ai-model' }, ['Model name']),
        h(doc, 'span', { class: 'field-hint', id: 'ai-model-hint' }, ['As your model server lists it, for example llama3.2.']),
        modelInput,
      ]),
      h(doc, 'p', { class: 'field' }, [
        h(doc, 'label', { for: 'ai-endpoint' }, ['Model server address']),
        h(doc, 'span', { class: 'field-hint', id: 'ai-endpoint-hint' }, ['Must be on this computer. Most people keep the default.']),
        endpointInput,
      ]),
      submit,
    ]);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      options.onConnect(modelInput.value.trim(), endpointInput.value.trim());
    });
    root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'local-heading' }, [
      h(doc, 'h2', { id: 'local-heading' }, ['A model on this computer']),
      h(doc, 'p', {}, [
        'For privacy, Nurse AI OS can use an AI model that runs on your own computer, through a local model server such as Ollama. ',
        'How well it works depends on your computer.',
      ]),
      form,
    ]));
  } else {
    root.append(h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Read-only'), ' Settings can be changed in the Nurse AI OS app.',
    ]));
  }

  root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'cloud-heading' }, [
    h(doc, 'h2', { id: 'cloud-heading' }, ['Cloud AI service']),
    h(doc, 'p', { class: 'section-state' }, [badge(doc, 'unavailable', '○', 'Not available'), ' ', data.cloud.reason]),
  ]));
  root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'gates-heading' }, [
    h(doc, 'h2', { id: 'gates-heading' }, ['What every AI model must pass']),
    h(doc, 'ol', { class: 'item-list' }, data.gates.map((gate) => h(doc, 'li', {}, [gate]))),
  ]));
  return root;
}

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Library} Library */

const SOURCE_KINDS = { public: 'Public', synthetic: 'Synthetic', personal_permitted: 'My own, permitted' };
const DATA_CLASSES = { D0: 'D0 · public or synthetic', D1: 'D1 · my own professional material' };

/**
 * The Library: every source in the workspace, overdue reviews first.
 * References are shown as text; the app never opens them.
 * @param {Document} doc
 * @param {Library} data
 * @param {{ writable: boolean, busy?: boolean, notice?: Notice, onAdd: (fields: Record<string, string>) => void }} options
 */
export function renderLibrary(doc, data, options) {
  const busy = Boolean(options.busy);
  const root = h(doc, 'div', { class: 'view view--library' });
  root.append(viewHeading(doc, 'Library',
    'Every source in this workspace, whichever project it belongs to. Sources due for review come first.'));
  const notice = noticeBlock(doc, options.notice);
  if (notice) root.append(notice);

  const section = h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'sources-heading' }, [
    h(doc, 'h2', { id: 'sources-heading', tabindex: '-1' }, [`Sources (${data.items.length})`]),
  ]);
  if (data.items.length === 0) {
    section.append(h(doc, 'p', { class: 'section-state section-state--empty' }, ['No sources yet.']));
  } else {
    const summary = data.review_overdue
      ? `${count(data.review_overdue, 'source is', 'sources are')} past its review date.`
      : 'Every source is within its review date.';
    section.append(h(doc, 'p', { class: 'table-summary' }, [summary]));
    const rows = data.items.map((item) => h(doc, 'tr', { 'data-record-id': item.id }, [
      h(doc, 'th', { scope: 'row' }, [
        h(doc, 'span', { class: 'cell-title' }, [item.title]),
        h(doc, 'br'),
        h(doc, 'code', { class: 'reference' }, [item.reference]),
      ]),
      h(doc, 'td', {}, [SOURCE_KINDS[item.kind]]),
      h(doc, 'td', {}, [item.data_class]),
      h(doc, 'td', {}, [item.project_id
        ? h(doc, 'a', { href: `#/project/${encodeURIComponent(item.project_id)}` }, [item.project ?? item.project_id])
        : 'Whole workspace']),
      h(doc, 'td', { class: 'cell--date' }, [item.review_overdue
        ? badge(doc, 'overdue', '!', `Review overdue since ${item.review_date}`)
        : item.review_date ?? 'No review date']),
    ]));
    section.append(h(doc, 'div', { class: 'table-scroll' }, [
      h(doc, 'table', { class: 'task-table' }, [
        h(doc, 'caption', { class: 'visually-hidden' }, [`Library: ${data.items.length} sources`]),
        h(doc, 'thead', {}, [h(doc, 'tr', {}, ['Source', 'Kind', 'Data class', 'Project', 'Review']
          .map((label) => h(doc, 'th', { scope: 'col' }, [label])))]),
        h(doc, 'tbody', {}, rows),
      ]),
    ]));
  }
  root.append(section);

  if (!options.writable) {
    root.append(h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Read-only'), ' Adding sources is available in the Nurse AI OS app.',
    ]));
    return root;
  }
  /** @param {string} id @param {Record<string, string>} choices @param {string} [first] */
  const select = (id, choices, first) => {
    const el = /** @type {HTMLSelectElement} */ (h(doc, 'select', { id }, [
      first !== undefined ? h(doc, 'option', { value: '' }, [first]) : null,
      ...Object.entries(choices).map(([value, label]) => h(doc, 'option', { value }, [label])),
    ]));
    return el;
  };
  const title = /** @type {HTMLInputElement} */ (h(doc, 'input', { id: 'source-title', type: 'text', required: '', maxlength: '200', autocomplete: 'off' }));
  const kind = select('source-kind', SOURCE_KINDS);
  const reference = /** @type {HTMLInputElement} */ (h(doc, 'input', {
    id: 'source-reference', type: 'text', required: '', maxlength: '500', autocomplete: 'off',
    'aria-describedby': 'source-reference-hint',
  }));
  const dataClass = select('source-class', DATA_CLASSES);
  const project = select('source-project',
    Object.fromEntries(data.projects.map((p) => [p.id, p.title])), 'Whole workspace');
  const review = /** @type {HTMLInputElement} */ (h(doc, 'input', {
    id: 'source-review', type: 'date', min: data.today, 'aria-describedby': 'source-review-hint',
  }));
  const submit = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' }, ['Add source']));
  submit.disabled = busy;
  /** @param {string} id @param {string} label @param {HTMLElement} control @param {string} [hint] */
  const field = (id, label, control, hint) => h(doc, 'p', { class: 'field' }, [
    h(doc, 'label', { for: id }, [label]),
    hint ? h(doc, 'span', { class: 'field-hint', id: `${id}-hint` }, [hint]) : null,
    control,
  ]);
  const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'add-source-heading' }, [
    field('source-title', 'Title', title),
    field('source-kind', 'Kind', kind),
    field('source-reference', 'Where it is', reference, 'A web address, a folder, or a book. It is kept as text.'),
    field('source-class', 'Data class', dataClass),
    field('source-project', 'Project', project),
    field('source-review', 'Review by (optional)', review, 'When to check it is still current.'),
    submit,
  ]);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    options.onAdd({
      title: title.value.trim(), kind: kind.value, reference: reference.value.trim(),
      data_class: dataClass.value, project_id: project.value, review_date: review.value,
    });
  });
  root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'add-source-heading' }, [
    h(doc, 'h2', { id: 'add-source-heading' }, ['Add a source']),
    h(doc, 'p', { class: 'onboarding-rules', role: 'note' }, [
      badge(doc, 'review', '!', 'Data rules'), ' ',
      'Public, synthetic, or your own permitted material only. Keep patient information, staff performance, ',
      'and confidential employer material out.',
    ]),
    form,
  ]));
  return root;
}

/** @typedef {import('../contracts/ipc/nurse-manager-ipc').Learning} Learning */
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').LearningItem} LearningItem */
/**
 * @typedef {object} LearningOptions
 * @property {boolean} writable
 * @property {boolean} [busy]
 * @property {Notice} [notice]
 * @property {string | null} [completing] the item whose completion form is open
 * @property {(fields: Record<string, string>) => void} onAdd
 * @property {(id: string) => void} onStart
 * @property {(id: string) => void} onOpenComplete
 * @property {() => void} onCancelComplete
 * @property {(id: string, fields: Record<string, string>) => void} onComplete
 */

const LEARNING_KINDS = {
  course: 'Course', reading: 'Reading', conference: 'Conference',
  certification: 'Certification', mentoring: 'Mentoring',
};

/**
 * Learning and Growth: the manager's own learning. Stated facts, never a score.
 * @param {Document} doc
 * @param {Learning} data
 * @param {LearningOptions} options
 */
export function renderLearning(doc, data, options) {
  const busy = Boolean(options.busy);
  const root = h(doc, 'div', { class: 'view view--learning' });
  root.append(viewHeading(doc, 'Learning and Growth',
    'Your own professional learning. Keep patient and colleague details out.'));
  const notice = noticeBlock(doc, options.notice);
  if (notice) root.append(notice);
  const hoursText = data.hours_this_year === 1 ? '1 hour' : `${data.hours_this_year} hours`;
  root.append(h(doc, 'ul', { class: 'item-list', 'aria-label': 'This year' }, [
    h(doc, 'li', {}, [`${data.in_progress} in progress · ${data.planned} planned`]),
    h(doc, 'li', {}, [`${count(data.completed_this_year, 'item', 'items')} completed this year (${hoursText})`]),
    data.past_target
      ? h(doc, 'li', {}, [badge(doc, 'overdue', '!', count(data.past_target, 'item is', 'items are')), ' past its target date.'])
      : null,
  ]));

  /** @param {LearningItem} item */
  const card = (item) => {
    const meta = [LEARNING_KINDS[item.kind]];
    if (item.status !== 'completed' && item.target_date) meta.push(`target ${item.target_date}`);
    if (item.hours !== null) meta.push(`${item.hours} h`);
    if (item.status === 'completed') meta.push(`completed ${item.completed_on}`);
    const el = h(doc, 'li', { class: 'card', 'data-record-id': item.id }, [
      h(doc, 'p', { class: 'card__title' }, [item.title]),
      h(doc, 'p', { class: 'card__meta' }, [meta.join(' · ')]),
    ]);
    if (item.status === 'completed') {
      el.append(h(doc, 'p', {}, [badge(doc, 'accepted', '✓', 'Takeaway'), ' ', item.takeaway]));
    } else if (options.writable && options.completing === item.id) {
      const takeaway = /** @type {HTMLTextAreaElement} */ (h(doc, 'textarea', {
        id: `takeaway-${item.id}`, rows: '2', required: '', maxlength: '1000',
      }));
      const date = /** @type {HTMLInputElement} */ (h(doc, 'input', {
        id: `completed-${item.id}`, type: 'date', required: '', max: data.today,
      }));
      date.value = data.today;
      const hoursInput = /** @type {HTMLInputElement} */ (h(doc, 'input', {
        id: `hours-${item.id}`, type: 'text', inputmode: 'decimal', maxlength: '6',
      }));
      hoursInput.value = item.hours === null ? '' : String(item.hours);
      const done = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' }, ['Mark completed']));
      done.disabled = busy;
      const form = h(doc, 'form', { class: 'onboarding-form' }, [
        h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: `takeaway-${item.id}` }, ['What did you take away?']), takeaway]),
        h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: `completed-${item.id}` }, ['Completed on']), date]),
        h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: `hours-${item.id}` }, ['Hours (optional)']), hoursInput]),
        h(doc, 'p', { class: 'button-row' }, [done, button(doc, 'Cancel', busy, options.onCancelComplete, 'secondary-button')]),
      ]);
      form.addEventListener('submit', (event) => {
        event.preventDefault();
        options.onComplete(item.id, {
          takeaway: takeaway.value.trim(), completed_on: date.value, hours: hoursInput.value.trim(),
        });
      });
      el.append(form);
    } else if (options.writable) {
      el.append(h(doc, 'p', { class: 'button-row' }, [
        item.status === 'planned' ? button(doc, 'Start', busy, () => options.onStart(item.id), 'secondary-button') : null,
        button(doc, 'Mark completed…', busy, () => options.onOpenComplete(item.id), 'secondary-button'),
      ]));
    }
    return el;
  };

  for (const [status, title, empty] of /** @type {const} */ ([
    ['in_progress', 'In progress', 'Nothing in progress.'],
    ['planned', 'Planned', 'Nothing planned yet.'],
    ['completed', 'Completed', 'Nothing completed yet.'],
  ])) {
    const items = data.items.filter((i) => i.status === status);
    const headingId = `learning-${status}-heading`;
    root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': headingId }, [
      h(doc, 'h2', { id: headingId, tabindex: '-1' }, [`${title} (${items.length})`]),
      items.length
        ? h(doc, 'ul', { class: 'card-list' }, items.map(card))
        : h(doc, 'p', { class: 'section-state section-state--empty' }, [empty]),
    ]));
  }

  if (!options.writable) {
    root.append(h(doc, 'p', { class: 'section-state' }, [
      badge(doc, 'unavailable', '○', 'Read-only'), ' Planning learning is available in the Nurse AI OS app.',
    ]));
    return root;
  }
  const title = /** @type {HTMLInputElement} */ (h(doc, 'input', { id: 'learning-title', type: 'text', required: '', maxlength: '200', autocomplete: 'off' }));
  const kind = /** @type {HTMLSelectElement} */ (h(doc, 'select', { id: 'learning-kind' },
    Object.entries(LEARNING_KINDS).map(([value, label]) => h(doc, 'option', { value }, [label]))));
  const target = /** @type {HTMLInputElement} */ (h(doc, 'input', { id: 'learning-target', type: 'date' }));
  const hours = /** @type {HTMLInputElement} */ (h(doc, 'input', { id: 'learning-hours', type: 'text', inputmode: 'decimal', maxlength: '6' }));
  const submit = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'submit', class: 'primary-button' }, ['Add to my plan']));
  submit.disabled = busy;
  const form = h(doc, 'form', { class: 'onboarding-form', 'aria-labelledby': 'learning-add-heading' }, [
    h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'learning-title' }, ['What will you learn?']), title]),
    h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'learning-kind' }, ['Kind']), kind]),
    h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'learning-target' }, ['Target date (optional)']), target]),
    h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: 'learning-hours' }, ['Continuing-education hours (optional)']), hours]),
    submit,
  ]);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    options.onAdd({ title: title.value.trim(), kind: kind.value, target_date: target.value, hours: hours.value.trim() });
  });
  root.append(h(doc, 'section', { class: 'mc-section', 'aria-labelledby': 'learning-add-heading' }, [
    h(doc, 'h2', { id: 'learning-add-heading' }, ['Plan something new']), form,
  ]));
  return root;
}
