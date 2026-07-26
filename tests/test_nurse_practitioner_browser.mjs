import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../assets/nurse-practitioner-funnel.js', import.meta.url), 'utf8');

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

  elements['np-focus'] = element({ value: 'professional-writing' });
  elements['np-style'] = element({ value: 'concise-first' });
  elements['np-evidence'] = element({ value: 'source-first' });
  elements['np-review'] = element({ value: 'assumption-ledger' });
  elements['np-practice-card'] = element();
  elements['np-practice-card-title'] = element();
  elements['copy-np-practice-card'] = element();
  elements['np-practice-card-status'] = element();

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
  vm.runInNewContext(source, sandbox, { filename: 'nurse-practitioner-funnel.js' });
  return {
    elements,
    click: () => elements['copy-np-practice-card'].listeners.click(),
    change: (id) => elements[id].listeners.change()
  };
}

{
  let written = '';
  const harness = buildHarness({
    clipboard: { async writeText(value) { written = value; } },
    execCommand: () => { throw new Error('fallback should not run'); }
  });
  await harness.click();
  assert.ok(written.startsWith('Personal AI Practice Card — Community Preview'));
  assert.match(written, /No patient data or PHI/);
  assert.match(written, /No patient stories, even if names are removed/);
  assert.match(written, /No employer-confidential information/);
  assert.match(written, /Do not diagnose, prescribe, triage, code, bill, or make patient-specific decisions/);
  assert.equal(harness.elements['copy-np-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['np-practice-card-status'].textContent, /provider privacy boundary/);
  harness.elements['np-style'].value = 'socratic-challenge';
  harness.change('np-style');
  assert.equal(harness.elements['copy-np-practice-card'].textContent, 'Copy my practice card');
  assert.match(harness.elements['np-practice-card-status'].textContent, /Card updated/);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => true
  });
  await harness.click();
  assert.equal(harness.elements['copy-np-practice-card'].textContent, 'Copied');
  assert.equal(harness.elements['np-practice-card'].selectCount, 1);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: () => false });
  await harness.click();
  assert.match(harness.elements['np-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['np-practice-card'].selectCount, 2);
  assert.ok(harness.elements['np-practice-card'].focusCount >= 2);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => { throw new Error('fallback exploded'); }
  });
  await harness.click();
  assert.match(harness.elements['np-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['np-practice-card'].selectCount, 2);
}

{
  let finishWrite;
  let written = '';
  const harness = buildHarness({
    clipboard: {
      writeText(value) {
        written = value;
        return new Promise(resolve => { finishWrite = resolve; });
      }
    },
    execCommand: () => { throw new Error('fallback should not run after clipboard success'); }
  });
  const copyPromise = harness.click();
  harness.elements['np-focus'].value = 'evidence-learning';
  harness.change('np-focus');
  finishWrite();
  await copyPromise;
  assert.match(written, /Primary focus: Professional writing and communication/);
  assert.match(harness.elements['np-practice-card'].value, /Primary focus: Evidence and learning/);
  assert.equal(harness.elements['copy-np-practice-card'].textContent, 'Copy updated card');
  assert.match(harness.elements['np-practice-card-status'].textContent, /changed while copying/);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  harness.elements['np-focus'].value = 'evidence-learning';
  harness.elements['np-style'].value = 'socratic-challenge';
  harness.elements['np-evidence'].value = 'known-assumed-unknown';
  harness.elements['np-review'].value = 'challenge-reasoning';
  harness.change('np-focus');
  const card = harness.elements['np-practice-card'].value;
  assert.equal(harness.elements['np-practice-card-title'].textContent, 'Evidence and learning · Socratic challenge');
  assert.match(card, /Primary focus: Evidence and learning/);
  assert.match(card, /Interaction style: Socratic challenge/);
  assert.match(card, /Evidence discipline: Known \/ Assumed \/ Unknown \/ Decide/);
  assert.match(card, /Review pattern: Challenge my reasoning/);
  assert.match(card, /Personal-use Draft support only/);
}

console.log('NURSE_PRACTITIONER_BROWSER_OK clipboard_paths=4 clipboard_race=1 copied_state_reset=1 configuration_switch=1');
