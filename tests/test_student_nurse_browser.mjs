import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../assets/student-nurse-funnel.js', import.meta.url), 'utf8');

function buildHarness({ clipboard = null, execCommand }) {
  const elements = {};
  function element(initial = {}) {
    return Object.assign({
      listeners: {},
      textContent: '',
      value: '',
      focusCount: 0,
      selectCount: 0,
      addEventListener(type, listener) { this.listeners[type] = listener; },
      focus() { this.focusCount += 1; },
      select() { this.selectCount += 1; }
    }, initial);
  }

  elements['student-task'] = element({ value: 'student-study-map' });
  elements['student-prompt'] = element();
  elements['student-prompt-title'] = element();
  elements['copy-student-workflow'] = element();
  elements['student-workflow-status'] = element();

  const document = {
    getElementById(id) { return elements[id] || null; },
    execCommand
  };
  const sandbox = {
    document,
    navigator: clipboard ? { clipboard } : {},
    window: { isSecureContext: Boolean(clipboard) },
    Boolean
  };
  vm.runInNewContext(source, sandbox, { filename: 'student-nurse-funnel.js' });
  return {
    elements,
    click: () => elements['copy-student-workflow'].listeners.click(),
    change: () => elements['student-task'].listeners.change()
  };
}

{
  let written = '';
  const harness = buildHarness({
    clipboard: { async writeText(value) { written = value; } },
    execCommand: () => { throw new Error('fallback should not run'); }
  });
  await harness.click();
  assert.ok(written.startsWith('Safety contract:'), 'clipboard receives the bounded prompt');
  assert.equal(harness.elements['copy-student-workflow'].textContent, 'Copied');
  assert.match(harness.elements['student-workflow-status'].textContent, /provider privacy boundary/);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => true
  });
  await harness.click();
  assert.equal(harness.elements['copy-student-workflow'].textContent, 'Copied');
  assert.equal(harness.elements['student-prompt'].selectCount, 1);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: () => false });
  await harness.click();
  assert.match(harness.elements['student-workflow-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['student-prompt'].selectCount, 2);
  assert.ok(harness.elements['student-prompt'].focusCount >= 2);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => { throw new Error('fallback exploded'); }
  });
  await harness.click();
  assert.match(harness.elements['student-workflow-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['student-prompt'].selectCount, 2);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  harness.elements['student-task'].value = 'student-integrity-check';
  harness.change();
  assert.equal(
    harness.elements['student-prompt-title'].textContent,
    'faculty-question prompt for AI-use rules'
  );
  assert.ok(harness.elements['student-prompt'].value.startsWith('Safety contract:'));
  assert.match(harness.elements['student-prompt'].value, /Never decide or label the use as allowed/);
}

console.log('STUDENT_NURSE_BROWSER_OK clipboard_paths=4 prompt_switch=1');
