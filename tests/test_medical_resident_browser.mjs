import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../assets/medical-resident-funnel.js', import.meta.url), 'utf8');

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

  elements['resident-focus'] = element({ value: 'rotation-learning' });
  elements['resident-capacity'] = element({ value: 'ten-low' });
  elements['resident-style'] = element({ value: 'socratic' });
  elements['resident-review'] = element({ value: 'one-artifact' });
  elements['resident-practice-card'] = element();
  elements['resident-practice-card-title'] = element();
  elements['copy-resident-practice-card'] = element();
  elements['resident-practice-card-status'] = element();

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
  vm.runInNewContext(source, sandbox, { filename: 'medical-resident-funnel.js' });
  return {
    elements,
    click: () => elements['copy-resident-practice-card'].listeners.click(),
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
  assert.ok(written.startsWith('Resident Learning Practice Card — Medical Resident Community Preview'));
  assert.match(written, /No patient data or PHI/);
  assert.match(written, /No patient cases, case narratives, or identifiable stories, even if names are removed/);
  assert.match(written, /No EHR, sign-out, chart, consult, handoff, schedule, or incident content/);
  assert.match(written, /No evaluations, personnel records, or confidential program material/);
  assert.match(written, /Do not diagnose, triage, choose treatment, make patient-specific decisions, write chart content, or direct care/);
  assert.match(written, /Do not determine competence, entrustment, supervision level, procedural authorization, duty-hour compliance, program standing, or credentialing/);
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['resident-practice-card-status'].textContent, /provider privacy boundary/);
  harness.elements['resident-style'].value = 'challenge-assumptions';
  harness.change('resident-style');
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copy my learning card');
  assert.match(harness.elements['resident-practice-card-status'].textContent, /Card updated/);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => true
  });
  await harness.click();
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copied');
  assert.equal(harness.elements['resident-practice-card'].selectCount, 1);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: () => false });
  await harness.click();
  assert.match(harness.elements['resident-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['resident-practice-card'].selectCount, 2);
  assert.ok(harness.elements['resident-practice-card'].focusCount >= 2);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  await harness.click();
  assert.match(harness.elements['resident-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['resident-practice-card'].selectCount, 2);
}

{
  const harness = buildHarness({
    clipboard: { async writeText() { throw new Error('clipboard denied'); } },
    execCommand: () => { throw new Error('fallback exploded'); }
  });
  await harness.click();
  assert.match(harness.elements['resident-practice-card-status'].textContent, /Automatic copy was blocked/);
  assert.equal(harness.elements['resident-practice-card'].selectCount, 2);
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
  harness.elements['resident-focus'].value = 'journal-club';
  harness.change('resident-focus');
  finishWrite();
  await copyPromise;
  assert.match(written, /Primary focus: Rotation learning plan/);
  assert.match(harness.elements['resident-practice-card'].value, /Primary focus: Journal club preparation/);
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copy updated card');
  assert.match(harness.elements['resident-practice-card-status'].textContent, /changed while copying/);
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
  harness.elements['resident-focus'].value = 'journal-club';
  harness.change('resident-focus');
  const secondCopy = harness.click();
  finishes[1]();
  await secondCopy;
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['resident-practice-card-status'].textContent, /provider privacy boundary/);
  finishes[0]();
  await firstCopy;
  assert.match(written[0], /Primary focus: Rotation learning plan/);
  assert.match(written[1], /Primary focus: Journal club preparation/);
  assert.equal(harness.elements['copy-resident-practice-card'].textContent, 'Copied');
  assert.match(harness.elements['resident-practice-card-status'].textContent, /provider privacy boundary/);
  assert.doesNotMatch(harness.elements['resident-practice-card-status'].textContent, /changed while copying/);
}

{
  const harness = buildHarness({ clipboard: null, execCommand: undefined });
  harness.elements['resident-focus'].value = 'journal-club';
  harness.elements['resident-capacity'].value = 'forty-five-deep';
  harness.elements['resident-style'].value = 'source-first';
  harness.elements['resident-review'].value = 'source-verification';
  harness.change('resident-focus');
  const card = harness.elements['resident-practice-card'].value;
  assert.equal(harness.elements['resident-practice-card-title'].textContent, 'Journal club preparation · 45 minutes · deep work');
  assert.match(card, /Primary focus: Journal club preparation/);
  assert.match(card, /Available capacity: 45 minutes · deep work/);
  assert.match(card, /Working style: Source-first synthesis/);
  assert.match(card, /Review checkpoint: Source verification checkpoint/);
  assert.match(card, /personal-use educational Draft support/);
  assert.match(card, /Proposed next step/);
}

console.log('MEDICAL_RESIDENT_BROWSER_OK clipboard_paths=5 clipboard_race=1 concurrent_copy=1 copied_state_reset=1 configuration_switch=1');
