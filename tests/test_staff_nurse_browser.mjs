import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../assets/staff-nurse-funnel.js', import.meta.url), 'utf8');

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

  elements['staff-focus'] = element({ value: 'after-shift-reset' });
  elements['staff-energy'] = element({ value: 'five-depleted' });
  elements['staff-style'] = element({ value: 'one-step' });
  elements['staff-review'] = element({ value: 'one-artifact' });
  elements['staff-practice-card'] = element();
  elements['staff-practice-card-title'] = element();
  elements['copy-staff-practice-card'] = element();
  elements['staff-practice-card-status'] = element();

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
  vm.runInNewContext(source, sandbox, { filename: 'staff-nurse-funnel.js' });
  return {
    elements,
    click: () => elements['copy-staff-practice-card'].listeners.click(),
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
  assert.ok(written.startsWith('Off-Shift AI Practice Card — Staff Nurse Community Preview'));
  assert.match(written, /No patient data or PHI/);
  assert.match(written, /No patient stories, even if names are removed/);
  assert.match(written, /No colleague, staff, or third-party identifiers/);
  assert.match(written, /No employer-confidential information, personnel records, schedules, staffing data, incident reports, or restricted organizational material/);
  assert.match(written, /Do not diagnose, triage, make patient-specific decisions, write chart content, or direct clinical care/);
  assert.match(written, /Do not make staffing, employment, disciplinary, performance, legal, labor, or regulatory decisions/);
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['staff-practice-card-status'].textContent, /provider privacy boundary/);
  harness.elements['staff-style'].value = 'coaching-questions';
  harness.change('staff-style');
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copy my off-shift card');
  assert.match(harness.elements['staff-practice-card-status'].textContent, /Card updated/);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => true
  });
  await harness.click();
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copied');
  assert.equal(harness.elements['staff-practice-card'].selectCount, 1);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: () => false });
  await harness.click();
  assert.match(harness.elements['staff-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['staff-practice-card'].selectCount, 2);
  assert.ok(harness.elements['staff-practice-card'].focusCount >= 2);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  await harness.click();
  assert.match(harness.elements['staff-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['staff-practice-card'].selectCount, 2);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => { throw new Error('fallback exploded'); }
  });
  await harness.click();
  assert.match(harness.elements['staff-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['staff-practice-card'].selectCount, 2);
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
  harness.elements['staff-focus'].value = 'learning-certification';
  harness.change('staff-focus');
  finishWrite();
  await copyPromise;
  assert.match(written, /Primary focus: After-shift reset/);
  assert.match(harness.elements['staff-practice-card'].value, /Primary focus: Learning and certification/);
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copy updated card');
  assert.match(harness.elements['staff-practice-card-status'].textContent, /changed while copying/);
}

{
  const finishes = [];
  const written = [];
  const harness = buildHarness({
    clipboard: {
      writeText(value) {
        written.push(value);
        return new Promise(resolve => { finishes.push(resolve); });
      }
    },
    execCommand: () => { throw new Error('fallback should not run after clipboard success'); }
  });
  const firstCopy = harness.click();
  harness.elements['staff-focus'].value = 'learning-certification';
  harness.change('staff-focus');
  const secondCopy = harness.click();
  finishes[1]();
  await secondCopy;
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['staff-practice-card-status'].textContent, /provider privacy boundary/);
  finishes[0]();
  await firstCopy;
  assert.match(written[0], /Primary focus: After-shift reset/);
  assert.match(written[1], /Primary focus: Learning and certification/);
  assert.equal(harness.elements['copy-staff-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['staff-practice-card-status'].textContent, /provider privacy boundary/);
  assert.doesNotMatch(harness.elements['staff-practice-card-status'].textContent, /changed while copying/);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  harness.elements['staff-focus'].value = 'shared-governance';
  harness.elements['staff-energy'].value = 'thirty-focused';
  harness.elements['staff-style'].value = 'source-first';
  harness.elements['staff-review'].value = 'source-check';
  harness.change('staff-focus');
  const card = harness.elements['staff-practice-card'].value;
  assert.equal(harness.elements['staff-practice-card-title'].textContent, 'Shared-governance preparation · 30 minutes · focused');
  assert.match(card, /Primary focus: Shared-governance preparation/);
  assert.match(card, /Available energy: 30 minutes · focused/);
  assert.match(card, /Working style: Source-first/);
  assert.match(card, /Review checkpoint: Source check before use/);
  assert.match(card, /personal-use Draft support/);
  assert.match(card, /Proposed next step/);
}

console.log('STAFF_NURSE_BROWSER_OK clipboard_paths=5 clipboard_race=1 concurrent_copy=1 copied_state_reset=1 configuration_switch=1');
