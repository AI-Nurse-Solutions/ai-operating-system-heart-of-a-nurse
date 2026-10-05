// @ts-check
import { h, viewHeading } from './views.mjs';
import { PEOPLE_LABELS } from './people-rules.mjs';
/** @typedef {import('../contracts/ipc/nurse-manager-ipc').CaptureView} CaptureView */
/** @typedef {Record<string, Record<string, string>>} CaptureTyped */
/**
 * Read all drafts before a redraw, including unchecked confirmation.
 * @param {HTMLElement} root @param {CaptureTyped} [fallback]
 * @returns {CaptureTyped}
 */
export function typedCapture(root, fallback = {}) {
  const result = { ...fallback };
  for (const form of root.querySelectorAll('form[data-capture]')) {
    const key = form.getAttribute('data-capture') || '';
    const fields = { ...result[key] };
    for (const control of form.querySelectorAll('input,select,textarea')) {
      const input = /** @type {HTMLInputElement} */ (control);
      if (input.name) fields[input.name] = input.type === 'checkbox' ? (input.checked ? 'yes' : 'no') : input.value;
    }
    result[key] = fields;
  }
  return result;
}
/**
 * @typedef {object} CaptureOptions
 * @property {boolean} writable
 * @property {boolean} [busy]
 * @property {boolean} [uncertain]
 * @property {CaptureTyped} [typed]
 * @property {import('./views.mjs').Notice} [notice]
 * @property {(key:string, fields:Record<string,string>)=>void} onSave
 * @property {()=>void} onRefresh
 */
/** @param {Document} doc @param {CaptureView} data @param {CaptureOptions} options */
export function renderCapture(doc, data, options) {
  const root = h(doc, 'div', { class: 'view view--capture' });
  root.append(viewHeading(doc, 'Add work', 'Personal planning, kept on this computer. Record a decision only after making it yourself.'));
  if (options.notice) root.append(h(doc, 'p', { class: `notice notice--${options.notice.kind}`, tabindex: '-1', role: 'status' }, [options.notice.text]));
  const refresh = /** @type {HTMLButtonElement} */ (h(doc, 'button', { type: 'button', class: 'secondary-button' }, ['Refresh records']));
  refresh.disabled = Boolean(options.busy);
  refresh.addEventListener('click', options.onRefresh);
  root.append(refresh);
  const section = (/** @type {string} */ key, /** @type {string} */ title) => {
    const el = h(doc, 'section', { class: 'mc-section', 'aria-labelledby': `capture-${key}-heading` }, [h(doc, 'h2', { id: `capture-${key}-heading` }, [title])]);
    root.append(el); return el;
  };
  const projects = section('projects', 'Projects');
  projects.append(h(doc, 'ul', { class: 'item-list' }, data.projects.length ? data.projects.map(p => h(doc, 'li', { 'data-record-id': p.id }, [h(doc, 'a', { href: `#/project/${p.id}` }, [p.title])])) : [h(doc, 'li', {}, ['No projects yet.'])]));
  const tasks = section('tasks', 'Tasks');
  tasks.append(h(doc, 'ul', { class: 'item-list' }, data.tasks.length ? data.tasks.map(t => h(doc, 'li', { 'data-record-id': t.id }, [`${t.task} · ${t.status}${t.blocked ? ' · blocked' : ''}${t.paused ? ' · paused' : ''}${t.evidence ? ` · Evidence: ${t.evidence}` : ''}`])) : [h(doc, 'li', {}, ['No tasks yet.'])]));
  const decisions = section('decisions', 'Decisions');
  decisions.append(h(doc, 'ul', { class: 'item-list' }, data.decisions.length ? data.decisions.map(d => h(doc, 'li', { 'data-record-id': d.id }, [`${d.question} → ${d.decision} · ${d.decided_by} · ${d.decided_on}${d.rationale ? ` · ${d.rationale}` : ''}`])) : [h(doc, 'li', {}, ['No decisions recorded yet.'])]));
  const priorities = section('priorities', `Priorities · week of ${data.week_of}`);
  priorities.append(h(doc, 'ol', { class: 'item-list', 'aria-label': 'Current priorities' }, data.priorities.length ? data.priorities.map(p => h(doc, 'li', {}, [p.text])) : [h(doc, 'li', {}, ['No priorities for this week.'])]));
  if (!options.writable) {
    root.append(h(doc, 'p', {}, ['This development preview is read-only. Open the local app to add or change work.'])); return root;
  }
  const disabled = Boolean(options.busy || options.uncertain);
  const projectChoices = [['', 'No project'], ...data.projects.map(p => [p.id, p.title])];
  const roles = PEOPLE_LABELS.map(label => [label, label]);
  /** @param {HTMLElement} parent @param {string} key @param {string} buttonText */
  const form = (parent, key, buttonText) => {
    const el = h(doc, 'form', { class: 'onboarding-form', 'data-capture': key });
    const set = h(doc, 'fieldset');
    if (disabled) set.setAttribute('disabled', '');
    el.append(set); parent.append(el);
    const button = h(doc, 'button', { type: 'submit', class: 'primary-button' }, [buttonText]);
    el.append(button); if (disabled) button.setAttribute('disabled', '');
    el.addEventListener('submit', event => {
      event.preventDefault();
      if (!disabled) options.onSave(key, typedCapture(root)[key]);
    });
    return { key, set };
  };
  /**
   * @param {{key:string,set:HTMLElement}} form @param {string} name @param {string} label
   * @param {{choices?:string[][],type?:string,value?:string,required?:boolean,max?:number,readOnly?:boolean}} [settings]
   */
  const field = (form, name, label, settings = {}) => {
    const id = `capture-${form.key}-${name}`;
    const value = options.typed?.[form.key]?.[name] ?? settings.value ?? settings.choices?.[0]?.[0] ?? '';
    const input = /** @type {HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement} */ (h(doc, settings.choices ? 'select' : settings.type === 'textarea' ? 'textarea' : 'input', { id, name }));
    if (settings.choices) for (const [v, text] of settings.choices) input.append(h(doc, 'option', { value: v }, [text]));
    else if (settings.type !== 'textarea') input.setAttribute('type', settings.type || 'text');
    input.value = value;
    if (settings.type === 'checkbox') /** @type {HTMLInputElement} */ (input).checked = value === 'yes';
    if (settings.required) input.setAttribute('required', '');
    if (settings.readOnly) input.setAttribute('readonly', '');
    if (settings.max) input.setAttribute('maxlength', String(settings.max));
    form.set.append(h(doc, 'p', { class: 'field' }, [h(doc, 'label', { for: id }, [label]), input]));
    return input;
  };
  const p = form(projects, 'project', 'Add project');
  field(p, 'title', 'Project title', { required: true, max: 200 });
  field(p, 'purpose', 'Purpose', { required: true, type: 'textarea', max: 2000 });
  field(p, 'owner_role', 'Project owner role', { choices: roles, value: 'me' });
  field(p, 'milestone', 'Milestone (optional)', { max: 1000 });
  const t = form(tasks, 'task', 'Add task');
  field(t, 'title', 'Task title', { required: true, max: 200 });
  field(t, 'project_id', 'Task project (optional)', { choices: projectChoices });
  field(t, 'owner_role', 'Task owner role', { choices: roles, value: 'me' });
  field(t, 'reviewer_role', 'Task reviewer role (optional)', { choices: [['', 'No reviewer'], ...roles] });
  field(t, 'due_date', 'Due date (optional)', { type: 'date' });
  const active = ['idea', 'ready', 'in_progress', 'needs_judgment'].map(s => [s, s === 'in_progress' ? 'In progress' : s === 'needs_judgment' ? 'Needs judgment' : s[0].toUpperCase() + s.slice(1)]);
  field(t, 'status', 'Initial task status', { choices: active, value: 'idea' });
  field(t, 'next_action', 'Next action (optional)', { type: 'textarea', max: 2000 });
  const d = form(decisions, 'decision', 'Record decision');
  field(d, 'question', 'Decision question', { required: true, max: 2000 });
  field(d, 'decision', 'Decision made', { required: true, type: 'textarea', max: 2000 });
  field(d, 'decision_role', 'Decision maker role', { choices: roles, value: 'me' });
  field(d, 'decided_on', 'Decision date', { required: true, type: 'date', value: data.today });
  field(d, 'rationale', 'Rationale (optional)', { type: 'textarea', max: 4000 });
  field(d, 'project_id', 'Decision project (optional)', { choices: projectChoices });
  const pr = form(priorities, 'priorities', 'Save priorities');
  field(pr, 'week', 'Priority week', { value: data.week_of, readOnly: true });
  field(pr, 'expected_sha256', '', { type: 'hidden', value: data.priorities_sha256 });
  for (let i = 1; i <= 3; i++) {
    const current = data.priorities[i - 1];
    field(pr, `item_${i}`, `Priority ${i}${i === 1 ? '' : ' (optional)'}`, { value: current?.text || '', max: 1000, required: i === 1 });
    field(pr, `project_${i}`, `Priority ${i} project (optional)`, { choices: projectChoices, value: current?.project_id || '' });
  }
  field(pr, 'replace_priorities', 'I reviewed the current list above and want to replace it with these priorities.', { type: 'checkbox', required: true, value: 'no' });
  if (data.tasks.length) {
    const changes = section('changes', 'Change a task');
    changes.append(h(doc, 'p', {}, ['The status shown here is checked again when you save. Completed or withdrawn tasks must be reopened before other changes. Completion requires evidence; reopening and withdrawal require a reason. Refresh records before changing a task if another tab may have edited it.']));
    const ch = form(changes, 'change', 'Save task change');
    field(ch, 'task_id', 'Task to change', { choices: data.tasks.map(t => [t.id, `${t.task} · ${t.status}`]), required: true, value: data.tasks[0].id });
    field(ch, 'action', 'Change', { choices: [['move', 'Move'], ['block', 'Set blocked'], ['pause', 'Set paused'], ['complete', 'Complete'], ['reopen', 'Reopen'], ['withdraw', 'Withdraw']], required: true, value: 'move' });
    field(ch, 'status', 'Target status (move or reopen)', { choices: active, value: 'ready' });
    field(ch, 'reason', 'Reason (required for blocking, reopening or withdrawal)', { type: 'textarea', max: 2000 });
    field(ch, 'evidence', 'Evidence (required for completion)', { type: 'textarea', max: 2000 });
    field(ch, 'blocked', 'Blocked value (set blocked)', { choices: [['yes','Blocked'],['no','Not blocked']] });
    field(ch, 'paused', 'Paused value (set paused)', { choices: [['yes','Paused'],['no','Not paused']] });
  }
  return root;
}
