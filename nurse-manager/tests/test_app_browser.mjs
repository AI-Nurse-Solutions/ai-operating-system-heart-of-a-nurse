// The local app as a manager meets it (ADR 0003).
//
// Launches `python -m nurse_manager.app` exactly as the packaged launcher
// does (minus opening a browser), then checks, in a real browser:
// - the launch token leaves the address bar
// - the page says the app is running on this computer and offers Quit
// - first-run onboarding works by keyboard and refuses identifiers with a
//   readable reason
// - a reload keeps the session, while a tab without the token is told it
//   is not connected
// - the sample path works
// - Quit really stops the process
// - the weekly brief is drafted, reviewed, and accepted from the screens
// - AI assistance: off by default; a model on this computer is connected
//   explicitly; the preview shows exactly what is sent before anything is,
//   and the model's draft waits for the manager's acceptance
// - onboarding says what the app does and does not do, that data stays here,
//   that no model runs by default, and that the privacy screen misses names
// - pilot feedback (6.3): kept here, an identifier refused, and the saved file
//   is byte for byte the text the manager previewed; nothing leaves 127.0.0.1
// - JEV (ADR 0006): off by default; the manager's own key, never shown back;
//   every job off until turned on; routing, ordering, and the refusal check
//   each send exactly the previewed request, suggest only, and a refused
//   question never reaches the AI model
//
// CHROME_PATH=/path/to/chrome overrides the system Chrome channel (local runs).
// NURSE_AI_OS_BIN=/path/to/nurse-ai-os runs it against a packaged build.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const src = fileURLToPath(new URL('../src', import.meta.url));
const env = { ...process.env, PYTHONPATH: src };
const work = mkdtempSync(join(tmpdir(), 'nm-app-'));

/** Launch the app; resolve with { child, url, exited }. */
const launch = (home) => new Promise((resolve, reject) => {
  const args = ['--no-browser', '--print-url', '--idle-timeout', '120', '--home', home];
  // NURSE_AI_OS_BIN runs the same journey against a packaged build.
  const child = process.env.NURSE_AI_OS_BIN
    ? spawn(process.env.NURSE_AI_OS_BIN, args, { env })
    : spawn('python3', ['-m', 'nurse_manager.app', ...args], { env });
  const exited = new Promise((done) => child.on('exit', (code) => done(code)));
  let out = '';
  child.stdout.on('data', (chunk) => {
    out += chunk;
    if (out.includes('\n')) resolve({ child, url: out.split('\n')[0].trim(), exited });
  });
  child.on('error', reject);
});

const apps = [];
let browser;
try {
  browser = await chromium.launch(process.env.CHROME_PATH
    ? { executablePath: process.env.CHROME_PATH, headless: true }
    : { channel: 'chrome', headless: true });

  // --- First run: start my own workspace ---------------------------------
  const own = await launch(join(work, 'own')); apps.push(own);
  assert.match(own.url, /^http:\/\/127\.0\.0\.1:\d+\/#token=[A-Za-z0-9_-]{20,}$/);
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(own.url);
  await page.waitForSelector('.view--onboarding');
  assert.equal(await page.title(), 'Welcome — Nurse AI OS');
  assert.ok(!page.url().includes('token'), 'the launch token leaves the address bar');
  assert.match(await page.getByRole('contentinfo').textContent(), /running on this computer.*2 minutes/s);
  assert.ok(await page.getByRole('button', { name: 'Quit Nurse AI OS' }).isVisible());
  assert.match(await page.getByRole('note').filter({ hasText: 'Before you start' }).textContent(),
    /Keep patient information, staff performance, and confidential employer material out/);

  // What to know first: every fact, stated before anything is created.
  const about = page.getByRole('region', { name: 'What to know first' });
  const aboutText = await about.textContent();
  for (const fact of [/What it does\..*one workspace/s, /never emails, posts, or uploads anything/,
    /does not connect to your employer’s systems/, /Your data stays on this computer\..*never uploaded/s,
    /No AI model runs by default\..*No cloud AI service drafts or answers for you\. JEV, an optional classifier, is off unless you connect it/s, /sample workspace is synthetic/,
    /Your own workspace starts empty/, /It does not detect people’s names\./,
    /Passing it never means text is free of patient information/]) {
    assert.match(aboutText, fact);
  }
  assert.doesNotMatch(await page.locator('main').textContent(), /phi[- ]free|de-identified|hipaa[- ]compliant/i,
    'nothing is ever called free of patient information');

  // Keyboard onboarding, with an identifier refused first.
  await page.getByLabel('Workspace name').fill('Unit 4 planning');
  await page.getByLabel('Your name').fill('manager@example.org');
  await page.getByRole('button', { name: 'Create my workspace' }).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('[role="alert"]');
  assert.match(await page.getByRole('alert').textContent(), /Not created.*does not keep identifying details.*EMAIL_ADDRESS/s);
  await page.getByLabel('Workspace name').fill('Unit planning');
  await page.getByLabel('Your name').fill('Test Manager');
  await page.getByLabel('Your name').press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'H1'
    && document.activeElement.textContent === 'Mission Control', null, { timeout: 10000 });
  assert.equal(await page.locator('#workspace-name').textContent(), 'Unit planning');
  assert.equal(await page.getByRole('note').filter({ hasText: 'Sample workspace' }).count() === 0
    || !(await page.locator('#sample-banner').isVisible()), true, 'a real workspace is not labeled sample');
  assert.match(await page.getByRole('region', { name: "This week's priorities" }).textContent(), /No priorities set/);

  // A reload keeps the session; a fresh tab without the token is not connected.
  await page.reload();
  await page.waitForSelector('.view--mission');
  const stranger = await (await browser.newContext()).newPage();
  const base = own.url.split('#')[0];
  await stranger.goto(`${base}#/mission`);
  await stranger.waitForSelector('[role="alert"]');
  assert.match(await stranger.getByRole('alert').textContent(), /not connected to Nurse AI OS/);
  assert.equal(await stranger.locator('.view--mission').count(), 0, 'no records without the token');

  // Reflow at 320px on onboarding-free screens.
  await page.setViewportSize({ width: 320, height: 800 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 0, `mission reflows at 320px (overflow ${overflow}px)`);
  await page.setViewportSize({ width: 1280, height: 900 });

  // --- Help and feedback: pilot feedback stays here until saved as reviewed ---
  const elsewhere = [];
  page.on('request', (r) => { if (!r.url().startsWith(base) && !r.url().startsWith('blob:')) elsewhere.push(r.url()); });
  await page.getByRole('link', { name: 'Help and feedback' }).click();
  await page.waitForSelector('.view--help');
  assert.equal(await page.title(), 'Help and feedback — Nurse AI OS');
  assert.match(await page.getByRole('region', { name: 'What to know' }).textContent(), /It does not detect people’s names/);
  assert.match(await page.getByRole('region', { name: 'Getting help' }).textContent(), /Assistants at work.*stops them all/s);
  const pilot = page.getByRole('region', { name: 'Pilot feedback', exact: true });
  assert.match(await pilot.textContent(), /Nothing is sent.*does not detect names.*No pilot feedback yet/s);
  assert.equal(await page.getByRole('button', { name: 'Preview what will be shared' }).isDisabled(), true, 'nothing to share yet');
  // An identifier is refused with a readable reason, and the typed text is kept.
  await page.getByLabel('Part of the app').selectOption('weekly_brief');
  await page.getByLabel('Kind', { exact: true }).selectOption('problem');
  await page.getByLabel('What happened, or what would help?').fill('Ask me at manager@example.org about the Accept button');
  await page.getByRole('button', { name: 'Save feedback' }).click();
  await page.waitForFunction(() => /Not done/.test(document.activeElement?.textContent ?? ''));
  assert.match(await page.getByRole('alert').textContent(), /does not keep identifying details.*EMAIL_ADDRESS/s);
  assert.equal(await page.getByLabel('What happened, or what would help?').inputValue(), 'Ask me at manager@example.org about the Accept button');
  assert.equal(await page.getByLabel('Part of the app').inputValue(), 'weekly_brief');
  await page.getByLabel('What happened, or what would help?').fill('The Accept button was hard to find on a small screen.');
  await page.getByRole('button', { name: 'Save feedback' }).focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => /Saved on this computer\. Nothing was sent/.test(document.activeElement?.textContent ?? ''));
  assert.equal(await page.getByLabel('What happened, or what would help?').inputValue(), '', 'the saved form starts empty');
  assert.match(await pilot.getByRole('listitem').first().textContent(), /Weekly brief · Problem.*hard to find.*Not in an export yet/s);
  await page.getByLabel('Part of the app').selectOption('getting_started');
  await page.getByLabel('Kind', { exact: true }).selectOption('worked');
  await page.getByLabel('What happened, or what would help?').fill('Creating my workspace took a minute.');
  await page.getByRole('button', { name: 'Save feedback' }).click();
  await pilot.getByText('Creating my workspace took a minute.').waitFor();
  assert.match(await page.evaluate(() => document.activeElement?.textContent ?? ''), /Saved on this computer/);
  assert.match(await pilot.textContent(), /2 items kept here · never exported/);

  // Preview: exactly the file; the name of the workspace and its manager never cross.
  await page.getByRole('button', { name: 'Preview what will be shared' }).click();
  await page.waitForFunction(() => document.activeElement?.id === 'pilot-preview-heading');
  const shown = await page.getByLabel('Exactly what will be shared', { exact: true }).textContent();
  assert.match(shown, /^# Nurse AI OS pilot feedback\n\n- App version: .+\n- Workspace: the manager’s own\n/);
  assert.match(shown, /## 1\. Weekly brief: Problem .*hard to find.*## 2\. Getting started: Worked well/s);
  assert.doesNotMatch(shown, /Unit planning|Test Manager/);
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Save as a file' }).click(),
  ]);
  assert.match(download.suggestedFilename(), /^nurse-ai-os-pilot-feedback-\d{4}-\d{2}-\d{2}\.md$/);
  assert.equal(readFileSync(await download.path(), 'utf8'), shown, 'the saved file is exactly the preview');
  await page.waitForFunction(() => /Nothing was sent: give the file to your pilot team yourself/.test(document.activeElement?.textContent ?? ''));
  assert.match(await pilot.textContent(), /2 items kept here · last export \d{4}-\d{2}-\d{2} \(2 items\)/);
  assert.equal(await pilot.getByText(/In the export of/).count(), 2);
  const [savedAgain] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Save the file again' }).click(),
  ]);
  assert.equal(readFileSync(await savedAgain.path(), 'utf8'), shown);

  // Text that reached the records another way is caught when the export is built.
  const db = join(work, 'own', 'workspace', 'workspace.sqlite');
  const planted = spawnSync('python3', ['-c', [
    'import sqlite3, sys',
    'db = sqlite3.connect(sys.argv[1])',
    'ws = db.execute("SELECT id FROM workspaces").fetchone()[0]',
    'db.execute("INSERT INTO pilot_feedback (id, workspace_id, area, kind, summary, created_at)'
      + ' VALUES (\'plf-00000000beef\', ?, \'other\', \'question\', \'Call 555-010-4477\', \'2020-01-06T10:00:00+00:00\')", (ws,))',
    'db.commit()',
  ].join('\n'), db], { encoding: 'utf8' });
  assert.equal(planted.status, 0, planted.stderr);
  await page.reload();
  await page.waitForSelector('.view--help');
  await page.getByRole('button', { name: 'Preview what will be shared' }).click();
  await page.waitForFunction(() => document.activeElement?.id === 'pilot-preview-heading');
  assert.match(await page.getByRole('alert').textContent(), /Cannot be exported.*item 1 \(PHONE_NUMBER\)/s);
  assert.doesNotMatch(await page.getByRole('alert').textContent(), /555-010-4477/, 'the finding never repeats the identifier');
  assert.equal(await page.getByRole('button', { name: 'Save as a file' }).count(), 0);
  await page.getByRole('button', { name: 'Close' }).click();
  // Delete, with confirmation: the item and its text are gone.
  const plantedItem = page.locator('[data-record-id="plf-00000000beef"]');
  await plantedItem.getByRole('button', { name: 'Delete…' }).click();
  await page.waitForFunction(() => document.activeElement?.textContent === 'Delete for good');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => /Deleted\. Its text is gone/.test(document.activeElement?.textContent ?? ''));
  assert.equal(await plantedItem.count(), 0);
  assert.match(await pilot.textContent(), /2 items kept here/);

  await page.setViewportSize({ width: 320, height: 800 });
  const helpOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(helpOverflow <= 0, `help and feedback reflows at 320px (overflow ${helpOverflow}px)`);
  await page.setViewportSize({ width: 1280, height: 900 });
  assert.deepEqual(elsewhere, [], 'nothing was requested from anywhere but this computer');

  // Quit really stops the app.
  await page.getByRole('button', { name: 'Quit Nurse AI OS' }).click();
  await page.waitForFunction(() => document.activeElement?.textContent === 'Nurse AI OS has stopped');
  assert.equal(await page.getByRole('contentinfo').isVisible(), false);
  const code = await Promise.race([own.exited, new Promise((r) => setTimeout(() => r('still running'), 10000))]);
  assert.equal(code, 0, 'the process exits after Quit');
  assert.deepEqual(errors, [], 'no console errors on the connected page');

  // --- First run: explore the sample -------------------------------------
  const sample = await launch(join(work, 'sample')); apps.push(sample);
  const samplePage = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const sampleErrors = [];
  samplePage.on('console', (m) => { if (m.type() === 'error') sampleErrors.push(m.text()); });
  samplePage.on('pageerror', (e) => sampleErrors.push(e.message));
  const ipcCalls = [];
  samplePage.on('request', (r) => { if (r.url().includes('/ipc/')) ipcCalls.push({ url: r.url(), body: r.postData() }); });
  await samplePage.goto(sample.url);
  await samplePage.waitForSelector('.view--onboarding');
  await samplePage.getByRole('button', { name: 'Explore the sample workspace' }).click();
  await samplePage.waitForSelector('.view--mission');
  assert.ok(await samplePage.locator('#sample-banner').isVisible(), 'the sample is labeled synthetic');
  assert.equal(await samplePage.getByRole('region', { name: "This week's priorities" }).getByRole('listitem').count(), 3);

  // --- The weekly brief, from the screens ------------------------------
  const focusedText = () => samplePage.evaluate(() => document.activeElement?.textContent ?? '');
  await samplePage.getByRole('link', { name: 'Weekly brief' }).click();
  await samplePage.waitForSelector('.view--brief');
  assert.match(await samplePage.getByRole('region', { name: 'Current version' }).textContent(), /No brief for this week yet/);

  // With no model, "Draft with AI" says so and sends nothing.
  await samplePage.getByRole('button', { name: 'Draft with AI…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.id === 'preview-heading');
  const noModel = samplePage.getByRole('region', { name: 'Before anything is sent' });
  assert.match(await noModel.textContent(), /No AI model is connected/);
  await noModel.getByRole('button', { name: 'Draft from my records' }).click();
  await samplePage.waitForSelector('.notice[role="status"]');
  assert.match(await focusedText(), /composed from your records/);
  assert.match(await samplePage.locator('.brief-text').textContent(), /DRAFT — composed from your workspace records/);

  // Accept by keyboard; the acceptance is bound to the text on screen.
  await samplePage.getByRole('button', { name: /accept this version/ }).focus();
  await samplePage.keyboard.press('Enter');
  await samplePage.waitForFunction(() => /Version 1 is accepted/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.locator('.brief-text').textContent(), /Accepted\. Reviewed and accepted by Sample Manager/);

  // --- Every week: off by default; choices kept through a refused save --
  const everyWeek = samplePage.getByRole('region', { name: 'Every week' });
  assert.match(await everyWeek.textContent(), /Off.*runs only while Nurse AI OS is open on this computer/s);
  await samplePage.getByLabel('Prepare a draft every week').check();
  await samplePage.getByLabel('Day').selectOption('Wednesday');
  await samplePage.getByLabel('Time (this computer)').selectOption('06:00');
  let releaseSchedule = () => {};
  const scheduleHeld = new Promise((resolve) => { releaseSchedule = resolve; });
  await samplePage.route('**/ipc/brief-schedule-set', async (route) => {
    await scheduleHeld;
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({
      contract: 'nurse-manager-ipc@1', command: 'brief-schedule-set', ok: false,
      error: { type: 'ManagerError', message: 'the workspace is busy' } }) });
  });
  await everyWeek.getByRole('button', { name: 'Save' }).click();
  await samplePage.waitForSelector('#schedule-enabled[disabled]');
  assert.equal(await samplePage.getByLabel('Day').isEnabled(), false, 'the form is locked while it saves');
  releaseSchedule();
  await samplePage.waitForSelector('.view--brief .notice[role="alert"]');
  await samplePage.unroute('**/ipc/brief-schedule-set');
  assert.equal(await samplePage.getByLabel('Prepare a draft every week').isChecked(), true);
  assert.equal(await samplePage.getByLabel('Day').inputValue(), '2');
  assert.equal(await samplePage.getByLabel('Time (this computer)').inputValue(), '6');
  await samplePage.getByRole('region', { name: 'Every week' }).getByRole('button', { name: 'Save' }).click();
  await samplePage.waitForFunction(() => /Saved\. A draft from your records/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.getByRole('region', { name: 'Every week' }).textContent(),
    /On.*every Wednesday at 06:00\. (Next: Wednesday \d{4}-\d{2}-\d{2} at 06:00|Due now)/s);

  // --- Library: add a source through the capture rules ------------------
  await samplePage.getByRole('link', { name: 'Library' }).click();
  await samplePage.waitForSelector('.view--library');
  assert.equal(await samplePage.locator('.view--library tbody tr').count(), 3);
  await samplePage.getByLabel('Title').fill('Email me at manager@example.org');
  await samplePage.getByLabel('Where it is').fill('synthetic://refused');
  await samplePage.getByRole('button', { name: 'Add source' }).click();
  await samplePage.waitForSelector('.view--library .notice[role="alert"]');
  assert.match(await samplePage.locator('.notice').textContent(), /EMAIL_ADDRESS/);
  await samplePage.getByLabel('Title').fill('Huddle evaluation questions (synthetic)');
  await samplePage.getByLabel('Kind').selectOption('synthetic');
  await samplePage.getByLabel('Where it is').fill('synthetic://samples/huddle-evaluation');
  await samplePage.getByLabel('Project').selectOption({ label: 'Huddle format pilot' });
  await samplePage.getByRole('button', { name: 'Add source' }).click();
  await samplePage.waitForFunction(() => /Added “Huddle evaluation questions/.test(document.activeElement?.textContent ?? ''));
  assert.equal(await samplePage.locator('.view--library tbody tr').count(), 4);
  assert.match(await samplePage.locator('.view--library tbody').textContent(), /Huddle evaluation questions.*Huddle format pilot/s);

  // --- Learning and Growth: plan, start, complete with a takeaway -------
  await samplePage.getByRole('link', { name: 'Learning and Growth' }).click();
  await samplePage.waitForSelector('.view--learning');
  await samplePage.getByLabel('What will you learn?').fill('Budget basics for new managers (synthetic)');
  await samplePage.getByLabel('Continuing-education hours (optional)').fill('4');
  await samplePage.getByRole('button', { name: 'Add to my plan' }).click();
  await samplePage.waitForFunction(() => /Added “Budget basics/.test(document.activeElement?.textContent ?? ''));
  const planned = samplePage.getByRole('region', { name: 'Planned (2)' }).getByRole('listitem').filter({ hasText: 'Budget basics' });
  await planned.getByRole('button', { name: 'Start' }).click();
  await samplePage.waitForFunction(() => /Started\./.test(document.activeElement?.textContent ?? ''));
  const started = samplePage.getByRole('region', { name: 'In progress (2)' }).getByRole('listitem').filter({ hasText: 'Budget basics' });
  await started.getByRole('button', { name: 'Mark completed…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.keyboard.type('Read the variance report before the meeting.');
  await samplePage.getByRole('button', { name: 'Mark completed', exact: true }).click();
  await samplePage.waitForFunction(() => /Marked completed/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.getByRole('region', { name: 'Completed (2)' }).textContent(),
    /Budget basics.*4 h.*Takeaway.*Read the variance report/s);
  assert.match(await samplePage.getByRole('list', { name: 'This year' }).textContent(), /2 items completed this year \(7 hours\)/);

  // --- Contributions: a draft, refused identifiers, verified with evidence
  await samplePage.getByRole('link', { name: 'Contributions' }).click();
  await samplePage.waitForSelector('.view--contributions');
  // Half-typed text survives opening and cancelling another draft's evidence form.
  await samplePage.getByLabel('What was the contribution?').fill('Rewrote the council agenda template (synthetic)');
  await samplePage.getByLabel('Your part').fill('Drafted the template and tested it at two meetings.');
  const sampleDraft = samplePage.getByRole('listitem').filter({ hasText: 'Designed the five-part huddle format' });
  await sampleDraft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  assert.equal(await samplePage.getByLabel('What was the contribution?').inputValue(), 'Rewrote the council agenda template (synthetic)');
  await sampleDraft.getByRole('button', { name: 'Cancel' }).click();
  await samplePage.waitForSelector('.view--contributions textarea[id^="evidence-"]', { state: 'detached' });
  assert.equal(await samplePage.getByLabel('Your part').inputValue(), 'Drafted the template and tested it at two meetings.');

  await samplePage.getByLabel('Kind').selectOption('committee');
  await samplePage.getByLabel('Your part').fill('Drafted the template and tested it at two meetings.');
  await samplePage.getByLabel('Who shares the credit').fill('Thanks to jane.doe@example.org');
  await samplePage.getByLabel('Project (optional)').selectOption({ label: 'Unit Based Council charter refresh' });
  await samplePage.getByRole('button', { name: 'Save as draft' }).click();
  await samplePage.waitForSelector('.view--contributions .notice[role="alert"]');
  assert.match(await samplePage.locator('.notice').textContent(), /not stored.*EMAIL_ADDRESS/s);
  // The refusal keeps what was typed; only the refused field needs fixing.
  assert.equal(await samplePage.getByLabel('Your part').inputValue(), 'Drafted the template and tested it at two meetings.');
  assert.equal(await samplePage.getByLabel('Kind').inputValue(), 'committee');
  await samplePage.getByLabel('Who shares the credit').fill('Unit Based Council members');
  // While its own save is in flight, the submitted form is read-only.
  let releaseAdd = () => {};
  const addHeld = new Promise((resolve) => { releaseAdd = resolve; });
  await samplePage.route('**/ipc/contribution-add', async (route) => { await addHeld; await route.continue(); });
  await samplePage.getByRole('button', { name: 'Save as draft' }).click();
  await samplePage.waitForSelector('#contribution-title[readonly]');
  for (const label of ['What was the contribution?', 'Your part', 'Who shares the credit', 'Kind']) {
    assert.equal(await samplePage.getByLabel(label).isEditable(), false, `${label} is read-only while saving`);
  }
  releaseAdd();
  await samplePage.waitForFunction(() => /Saved “Rewrote the council agenda/.test(document.activeElement?.textContent ?? ''));
  await samplePage.unroute('**/ipc/contribution-add');
  assert.equal(await samplePage.getByLabel('What was the contribution?').isEditable(), true);
  const draft = samplePage.getByRole('region', { name: 'Drafts awaiting evidence (2)' }).getByRole('listitem').filter({ hasText: 'Rewrote the council agenda' });
  assert.match(await draft.textContent(), /Project: Unit Based Council charter refresh.*Shared credit: Unit Based Council members/s);
  // Evidence typed for one draft survives switching to another draft and back.
  await sampleDraft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.keyboard.type('Huddle notes from week one (synthetic).');
  await draft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await sampleDraft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  assert.equal(await samplePage.getByLabel('What shows it happened?').inputValue(), 'Huddle notes from week one (synthetic).');
  await draft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.keyboard.type('Template adopted in the council minutes (synthetic). Ask manager@example.org');
  await samplePage.getByRole('button', { name: 'Verify', exact: true }).click();
  await samplePage.waitForSelector('.view--contributions .notice[role="alert"]');
  const evidence = samplePage.getByLabel('What shows it happened?');
  assert.match(await evidence.inputValue(), /Template adopted.*manager@example\.org/);
  await evidence.fill('Template adopted in the council minutes (synthetic).');
  // A slow save: text typed into the add form while it is in flight is kept.
  let releaseVerify = () => {};
  const verifyHeld = new Promise((resolve) => { releaseVerify = resolve; });
  await samplePage.route('**/ipc/contribution-verify', async (route) => { await verifyHeld; await route.continue(); });
  await samplePage.getByRole('button', { name: 'Verify', exact: true }).click();
  await samplePage.getByLabel('What was the contribution?').fill('Typed while saving (synthetic)');
  releaseVerify();
  await samplePage.waitForFunction(() => /Verified, with your evidence/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.getByRole('region', { name: 'Verified (2)' }).textContent(),
    /Rewrote the council agenda.*Evidence.*Template adopted in the council minutes/s);
  assert.match(await samplePage.getByRole('list', { name: 'Facts' }).textContent(), /2 verified · 1 draft awaits evidence/);
  assert.equal(await samplePage.getByLabel('What was the contribution?').inputValue(), 'Typed while saving (synthetic)');
  await samplePage.unroute('**/ipc/contribution-verify');
  // A save that works but whose refresh fails keeps the screen and the unsaved text.
  await samplePage.getByLabel('Your part').fill('Typed before a failed refresh.');
  await samplePage.getByRole('listitem').filter({ hasText: 'Designed the five-part huddle format' })
    .getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.keyboard.type('Huddle notes from week one (synthetic).');
  const listRefresh = (/** @type {URL} */ url) => url.pathname === '/ipc/contributions';
  await samplePage.route(listRefresh, (route) => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ contract: 'nurse-manager-ipc@1', command: 'contributions', ok: false,
      error: { type: 'Unavailable', message: 'the workspace is busy' } }),
  }));
  await samplePage.getByRole('button', { name: 'Verify', exact: true }).click();
  await samplePage.waitForFunction(() => /could not be refreshed/.test(document.activeElement?.textContent ?? ''));
  await samplePage.unroute(listRefresh);
  assert.equal(await samplePage.getByLabel('Your part').inputValue(), 'Typed before a failed refresh.');
  assert.equal(await samplePage.getByLabel('What was the contribution?').inputValue(), 'Typed while saving (synthetic)');

  // --- Memory: add, correct, exclude, delete; refusals keep the text ---
  await samplePage.getByRole('link', { name: 'Memory' }).click();
  await samplePage.waitForSelector('.view--memory');
  assert.match(await samplePage.getByRole('list', { name: 'Facts' }).textContent(), /2 in use · 0 expired · 1 excluded/);
  await samplePage.getByLabel('What should the assistant remember?').fill('Send council agendas to jane.doe@example.org two days ahead.');
  await samplePage.getByLabel('For', { exact: true }).selectOption({ label: 'Unit Based Council charter refresh' });
  await samplePage.getByRole('button', { name: 'Remember this' }).click();
  await samplePage.waitForSelector('.view--memory .notice[role="alert"]');
  assert.match(await samplePage.locator('.notice').textContent(), /not stored.*EMAIL_ADDRESS/s);
  assert.equal(await samplePage.getByLabel('For', { exact: true }).inputValue() !== '', true, 'the scope is kept');
  await samplePage.getByLabel('What should the assistant remember?').fill('Council agendas go out two days ahead (synthetic).');
  await samplePage.getByRole('button', { name: 'Remember this' }).click();
  await samplePage.waitForFunction(() => /Remembered\./.test(document.activeElement?.textContent ?? ''));
  const inUse = samplePage.getByRole('region', { name: 'In use (3)' });
  const mine = inUse.getByRole('listitem').filter({ hasText: 'Council agendas go out two days ahead' });
  assert.match(await mine.textContent(), /Project: Unit Based Council charter refresh.*Written by Sample Manager on/s);
  await mine.getByRole('button', { name: 'Correct…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.getByLabel('Corrected wording').fill('Council agendas go out three days ahead (synthetic).');
  await samplePage.getByRole('button', { name: 'Save correction' }).click();
  await samplePage.waitForFunction(() => /Corrected\./.test(document.activeElement?.textContent ?? ''));
  const corrected = samplePage.getByRole('listitem').filter({ hasText: 'three days ahead' });
  assert.match(await corrected.textContent(), /Corrected by Sample Manager on/);
  await corrected.getByRole('button', { name: 'Exclude' }).click();
  await samplePage.waitForFunction(() => /Excluded\./.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.getByRole('region', { name: 'Excluded (2)' }).textContent(), /three days ahead/);
  await samplePage.getByRole('listitem').filter({ hasText: 'three days ahead' }).getByRole('button', { name: 'Use again' }).click();
  await samplePage.waitForFunction(() => /In use again\./.test(document.activeElement?.textContent ?? ''));
  const again = samplePage.getByRole('listitem').filter({ hasText: 'three days ahead' });
  await again.getByRole('button', { name: 'Delete…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.textContent === 'Delete for good');
  await samplePage.getByRole('listitem').filter({ hasText: 'three days ahead' }).getByRole('button', { name: 'Keep it' }).click();
  await samplePage.getByRole('listitem').filter({ hasText: 'three days ahead' }).getByRole('button', { name: 'Delete…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.textContent === 'Delete for good');
  await samplePage.keyboard.press('Enter');
  await samplePage.waitForFunction(() => /Deleted for good\./.test(document.activeElement?.textContent ?? ''));
  assert.equal(await samplePage.getByText('three days ahead').count(), 0);
  assert.match(await samplePage.getByRole('list', { name: 'Facts' }).textContent(), /2 in use · 0 expired · 1 excluded/);

  // --- Packs (5.4): start a draft, write it, accept exactly what was reviewed ---
  await samplePage.getByRole('link', { name: 'Packs' }).click();
  await samplePage.waitForSelector('.view--packs');
  const committee = samplePage.getByRole('region', { name: 'Committee pack 1.0.0' });
  assert.match(await committee.textContent(), /Maintained by.*Next review by2027-03-29.*never effective until it is approved/s);
  await committee.getByLabel('Template').selectOption({ label: 'Meeting Brief, Agenda, Minutes, and Action List' });
  await committee.getByLabel('For').selectOption({ label: 'Unit Based Council charter refresh' });
  await committee.getByRole('button', { name: 'Start a draft' }).click();
  await samplePage.waitForSelector('.view--document');
  assert.match(await samplePage.locator('h1').textContent(), /Meeting Brief, Agenda, Minutes, and Action List — Unit Based Council charter refresh/);
  assert.match(await samplePage.locator('.brief-text').textContent(), /DRAFT — started from a pack template.*Committee pack 1\.0\.0.*Agenda.*Write this section/s);
  await samplePage.getByRole('button', { name: 'Edit…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.id === 'document-text');
  const original = await samplePage.getByLabel('Document text (Markdown)').inputValue();
  // An identifier is refused, and the text stays as typed to fix.
  const withEmail = original.replace('_Write this section._', 'Ask chair@example.org to confirm the room.');
  await samplePage.getByLabel('Document text (Markdown)').fill(withEmail);
  await samplePage.getByRole('button', { name: 'Save as a new draft' }).click();
  await samplePage.waitForSelector('.view--document .notice[role="alert"]');
  assert.match(await samplePage.locator('.notice').textContent(), /not stored.*EMAIL_ADDRESS/s);
  assert.equal(await samplePage.getByLabel('Document text (Markdown)').inputValue(), withEmail);
  await samplePage.getByLabel('Document text (Markdown)').fill(
    original.replace('_Write this section._', 'Agree the charter dates first (synthetic).'));
  await samplePage.getByRole('button', { name: 'Save as a new draft' }).click();
  await samplePage.waitForFunction(() => /Saved as a new draft/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.locator('.brief-text').textContent(), /Agree the charter dates first/);
  assert.match(await samplePage.locator('.view--document').textContent(), /Version 2\./);
  await samplePage.getByRole('button', { name: /accept this version/ }).focus();
  await samplePage.keyboard.press('Enter');
  await samplePage.waitForFunction(() => /Version 2 is accepted/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.locator('.brief-text').textContent(), /Accepted\. Reviewed and accepted by Sample Manager/);
  await samplePage.getByRole('link', { name: '← Packs' }).click();
  await samplePage.waitForSelector('.view--packs');
  const yours = samplePage.getByRole('region', { name: 'Your documents (2)' });
  assert.match(await yours.getByRole('listitem').filter({ hasText: 'Meeting Brief' }).textContent(), /Accepted.*committee pack 1\.0\.0 · version 2/s);

  // --- AI assistance: connect a model on this computer ------------------
  const modelRequests = [];
  // While holdModel is set, the model works until the test releases it.
  let holdModel = false;
  /** @type {Array<() => void>} */
  const held = [];
  const model = createServer((req, res) => {
    let raw = '';
    req.on('data', (chunk) => { raw += chunk; });
    req.on('end', () => {
      const body = JSON.parse(raw);
      modelRequests.push(body);
      // A well-behaved model: keeps the headings and the cited lines.
      const kept = body.prompt.split('\n').filter((line) => line.startsWith('#') || line.includes('`'));
      const out = JSON.stringify({ response: kept.join('\n'), done: true });
      const answer = () => {
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(out);
      };
      if (holdModel) held.push(answer);
      else answer();
    });
  });
  await new Promise((done) => model.listen(0, '127.0.0.1', done));
  try {
    await samplePage.getByRole('link', { name: 'AI assistance' }).click();
    await samplePage.waitForSelector('.view--assistant');
    assert.match(await samplePage.getByRole('region', { name: 'Right now' }).textContent(), /No AI model.*nothing is ever sent/s);
    assert.match(await samplePage.getByRole('region', { name: 'Cloud AI service' }).textContent(), /No cloud AI service has been chosen/);
    await samplePage.getByLabel('Model name').fill('llama3.2');
    await samplePage.getByLabel('Model server address').fill(`http://127.0.0.1:${model.address().port}`);
    await samplePage.getByLabel('Model server address').press('Enter');
    await samplePage.waitForFunction(() => /Connected to the AI model/.test(document.activeElement?.textContent ?? ''));
    assert.match(await samplePage.getByRole('region', { name: 'Right now' }).textContent(), /Connected.*llama3\.2.*this computer/s);

    // The preview shows exactly what will be sent; nothing is sent until Send.
    await samplePage.getByRole('link', { name: 'Weekly brief' }).click();
    await samplePage.waitForSelector('.view--brief');
    await samplePage.getByRole('button', { name: 'Draft with AI…' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'preview-heading');
    const panel = samplePage.getByRole('region', { name: 'Before anything is sent' });
    assert.match(await panel.textContent(), /exactly what will be sent to the AI model “llama3\.2” on this computer/);
    assert.equal(await panel.getByRole('listitem').count(), 3, 'three checks are shown');
    const shownPrompt = await samplePage.getByLabel('Text from your records').textContent();
    const shownSystem = await samplePage.getByLabel('Instructions to the model').textContent();
    assert.equal(modelRequests.length, 0, 'nothing is sent by the preview');
    await panel.getByRole('button', { name: 'Send to llama3.2' }).click();
    await samplePage.waitForFunction(() => /The AI model drafted a new version/.test(document.activeElement?.textContent ?? ''), null, { timeout: 20000 });
    assert.equal(modelRequests.length, 1);
    assert.equal(modelRequests[0].prompt, shownPrompt, 'what was sent is what was shown');
    assert.equal(modelRequests[0].system, shownSystem);
    assert.match(await samplePage.locator('.brief-text').textContent(), /AI DRAFT — written by an AI model/);
    assert.match(await samplePage.getByRole('region', { name: 'Current version' }).textContent(), /AI draft — review it/);
    // Every brief action names the week on screen, so a page left open over a Monday stays on its week.
    const shownWeek = (await samplePage.locator('.view--brief .view-subtitle').textContent()).match(/\d{4}-\d{2}-\d{2}/)[0];
    const briefCalls = ipcCalls.filter((c) => /\/ipc\/(assistant-preview|brief|assistant-brief)(\?|$)/.test(c.url));
    assert.ok(briefCalls.length >= 3, 'preview, records draft, and AI draft were all called');
    for (const call of briefCalls) {
      assert.ok(call.url.includes(`week=${shownWeek}`) || (call.body ?? '').includes(`"week":"${shownWeek}"`),
        `${call.url} names the displayed week`);
    }
    assert.match(await samplePage.locator('.view--brief').textContent(), /Version 1 is the accepted one/);

    // Reflow at 320px with the long brief text.
    await samplePage.setViewportSize({ width: 320, height: 800 });
    const briefOverflow = await samplePage.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(briefOverflow <= 0, `the brief reflows at 320px (overflow ${briefOverflow}px)`);
    await samplePage.setViewportSize({ width: 1280, height: 900 });

    await samplePage.getByRole('button', { name: /accept this version/ }).click();
    await samplePage.waitForFunction(() => /Version 2 is accepted/.test(document.activeElement?.textContent ?? ''));

    // Think with a project: preview, send, and an answer that is not saved.
    await samplePage.getByRole('link', { name: 'Mission Control' }).click();
    await samplePage.waitForSelector('.view--mission');
    await samplePage.getByRole('region', { name: 'Projects in motion' }).getByRole('link').first().click();
    await samplePage.waitForSelector('.view--project');
    const think = samplePage.getByRole('region', { name: 'Think with this project' });
    await think.getByLabel('What do you want to think through?').fill('What should I do first?');
    await think.getByRole('button', { name: 'Preview what will be sent' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'think-preview-heading');
    // Editing the question withdraws the preview: the old question cannot be sent.
    await think.getByLabel('What do you want to think through?').fill('What should I do first?!');
    assert.equal(await think.getByRole('button', { name: 'Send to llama3.2' }).count(), 0, 'no Send after an edit');
    await think.getByLabel('What do you want to think through?').fill('What should I do first?');
    await think.getByRole('button', { name: 'Preview what will be sent' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'think-preview-heading');
    const thinkPrompt = await samplePage.getByLabel("Your question and this project's records").textContent();
    assert.match(thinkPrompt, /^## Question\n\nWhat should I do first\?/);
    // Memory in use is part of what is shown and sent; excluded memory never is.
    assert.match(thinkPrompt, /## What the manager asked you to remember\n\n- \(all work\) Lead with the decisions I need to make/);
    assert.doesNotMatch(thinkPrompt, /budget talks/);
    const sentBefore = modelRequests.length;
    await think.getByRole('button', { name: 'Send to llama3.2' }).click();
    await samplePage.waitForFunction(() => /The AI model answered/.test(document.activeElement?.textContent ?? ''), null, { timeout: 20000 });
    assert.equal(modelRequests.length, sentBefore + 1);
    assert.equal(modelRequests.at(-1).prompt, thinkPrompt, 'what was sent is what was shown');
    const suggestion = samplePage.getByRole('document', { name: 'AI suggestion' });
    assert.match(await suggestion.textContent(), /Title: .+prj-[0-9a-f]{12}/);
    assert.match(await think.textContent(), /Not saved/);
    assert.equal(await think.getByLabel('What do you want to think through?').inputValue(), 'What should I do first?');

    // Keep the answer: it becomes a note on the dashboard, labeled with where it came from.
    assert.match(await samplePage.getByRole('region', { name: /^Notes/ }).textContent(), /No notes yet/);
    await think.getByRole('button', { name: 'Keep as a project note' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'notes-heading');
    const notes = samplePage.getByRole('region', { name: 'Notes (1)' });
    const note = notes.getByRole('article', { name: 'What should I do first?' });
    assert.match(await note.textContent(), /Kept.*Written by the AI model “llama3\.2”; kept by Sample Manager/s);
    assert.match(await note.getByRole('document').textContent(), /Title: .+prj-[0-9a-f]{12}/);

    // Feedback: add it by keyboard, then close it with a written response.
    const openCount = async () => Number((await samplePage.locator('#feedback-heading').textContent()).match(/\((\d+) open\)/)[1]);
    const before = await openCount();
    await samplePage.getByLabel('From (a group or role)').fill('Evening huddle (synthetic)');
    await samplePage.getByLabel('Kind').selectOption('question');
    await samplePage.getByLabel('What was said').fill('Can the Dates slot cover two weeks?');
    await samplePage.getByRole('button', { name: 'Add feedback' }).focus();
    await samplePage.keyboard.press('Enter');
    await samplePage.waitForFunction(() => document.activeElement?.id === 'feedback-heading');
    assert.equal(await openCount(), before + 1);
    const added = samplePage.getByRole('listitem').filter({ hasText: 'Can the Dates slot cover two weeks?' });
    assert.match(await added.textContent(), /Question from Evening huddle \(synthetic\)/);
    await added.getByRole('button', { name: 'Mark addressed…' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
    await samplePage.keyboard.type('Yes: Dates now covers two weeks.');
    await samplePage.getByRole('button', { name: 'Mark addressed', exact: true }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'feedback-heading');
    assert.equal(await openCount(), before);
    assert.match(await samplePage.getByRole('listitem').filter({ hasText: 'Can the Dates slot cover two weeks?' }).textContent(),
      /Addressed \d{4}-\d{2}-\d{2}.*Yes: Dates now covers two weeks\./s);

    // --- Stop control (5.3): stop the model while it works ---------------
    await samplePage.getByRole('link', { name: 'Weekly brief' }).click();
    await samplePage.waitForSelector('.view--brief');
    const versionsBefore = await samplePage.locator('.view--brief .card__badges').textContent();
    await samplePage.getByRole('button', { name: 'Draft with AI…' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'preview-heading');
    holdModel = true;
    await samplePage.getByRole('region', { name: 'Before anything is sent' })
      .getByRole('button', { name: 'Send to llama3.2' }).click();
    const stopNow = samplePage.getByRole('button', { name: 'Stop assistants' });
    await stopNow.waitFor();
    assert.match(await samplePage.locator('#working').textContent(), /Waiting for the AI model/);
    assert.equal(await stopNow.isEnabled(), true, 'Stop works while everything else waits');
    // Stop only once the model has the request, so it is truly mid-work.
    for (let waited = 0; held.length === 0 && waited < 100; waited += 1) {
      await new Promise((done) => setTimeout(done, 100));
    }
    assert.equal(held.length, 1, 'the model received the request');
    const sentWhileHeld = modelRequests.length;
    // The first stop fails on its way: the button comes back so it can be tried again.
    const stopFails = (route) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({
      contract: 'nurse-manager-ipc@1', command: 'assistants-stop', ok: false,
      error: { type: 'ManagerError', message: 'the workspace is busy' } }) });
    await samplePage.route('**/ipc/assistants-stop', stopFails);
    await stopNow.click();
    await samplePage.waitForFunction(() => {
      const button = [...document.querySelectorAll('#working button')][0];
      return button && !button.disabled && button.textContent === 'Stop assistants';
    }, null, { timeout: 5000 });
    await samplePage.unroute('**/ipc/assistants-stop', stopFails);
    assert.equal(held.length, 1, 'the model is still working after the failed stop');
    await stopNow.click();
    // The request returns at once, though the model has not answered.
    await samplePage.waitForFunction(() => /You stopped assistants while the model was working/.test(document.activeElement?.textContent ?? ''),
      null, { timeout: 5000 });
    assert.equal(held.length, 1, 'the model is still working');
    assert.match(await samplePage.getByRole('region', { name: 'Current version' }).textContent(), /Draft — review it/);
    assert.doesNotMatch(await samplePage.locator('.brief-text').textContent(), /AI DRAFT/);
    assert.notEqual(await samplePage.locator('.view--brief .card__badges').textContent(), versionsBefore);
    holdModel = false;
    held.shift()(); // the model answers after all: nothing it says is used
    await new Promise((done) => setTimeout(done, 500));
    await samplePage.reload();
    await samplePage.waitForSelector('.view--brief');
    assert.doesNotMatch(await samplePage.locator('.brief-text').textContent(), /AI DRAFT/, 'the late reply was discarded');
    // While stopped, nothing is sent and the weekly draft waits.
    assert.match(await samplePage.getByRole('region', { name: 'Every week' }).textContent(), /assistants are stopped, so nothing is prepared/);
    await samplePage.getByRole('button', { name: 'Draft with AI…' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'preview-heading');
    assert.match(await samplePage.getByRole('region', { name: 'Before anything is sent' }).textContent(),
      /Will not be sent.*assistants are stopped/s);
    assert.equal(modelRequests.length, sentWhileHeld, 'nothing more was sent');

    // Mission Control says so, and only the manager lets them work again.
    await samplePage.getByRole('link', { name: 'Let them work again from Mission Control' }).click();
    await samplePage.waitForSelector('.view--mission');
    const atWork = samplePage.getByRole('region', { name: 'Assistants at work' });
    assert.match(await atWork.textContent(), /Stopped by Sample Manager.*Nothing is sent to an AI model/s);
    assert.match(await atWork.textContent(), /Recurring weekly brief.*Waiting while assistants are stopped/s);
    await atWork.getByRole('button', { name: 'Let assistants work again' }).focus();
    await samplePage.keyboard.press('Enter');
    await samplePage.waitForFunction(() => /Assistants can work again/.test(document.activeElement?.textContent ?? ''));
    assert.match(await atWork.textContent(), /A draft from your records on Wednesdays at 06:00, while this app is open/);
    await atWork.getByRole('button', { name: 'Stop all assistants' }).click();
    await samplePage.waitForFunction(() => /Assistants are stopped\. Nothing is sent/.test(document.activeElement?.textContent ?? ''));
    assert.ok(await atWork.getByRole('button', { name: 'Let assistants work again' }).isVisible());
    await atWork.getByRole('button', { name: 'Let assistants work again' }).click();
    await samplePage.waitForFunction(() => /Assistants can work again/.test(document.activeElement?.textContent ?? ''));

    // The same stop works while a project question waits for the model.
    await atWork.getByRole('button', { name: 'Stop all assistants' }).waitFor();
    await samplePage.getByRole('region', { name: 'Projects in motion' }).getByRole('link').first().click();
    await samplePage.waitForSelector('.view--project');
    const asking = samplePage.getByRole('region', { name: 'Think with this project' });
    await asking.getByLabel('What do you want to think through?').fill('What is at risk?');
    await asking.getByRole('button', { name: 'Preview what will be sent' }).click();
    await samplePage.waitForFunction(() => document.activeElement?.id === 'think-preview-heading');
    holdModel = true;
    await asking.getByRole('button', { name: 'Send to llama3.2' }).click();
    for (let waited = 0; held.length === 0 && waited < 100; waited += 1) {
      await new Promise((done) => setTimeout(done, 100));
    }
    await asking.getByRole('button', { name: 'Stop assistants' }).click();
    await samplePage.waitForFunction(() => /You stopped assistants while the model was working/.test(document.activeElement?.textContent ?? ''),
      null, { timeout: 5000 });
    assert.equal(await samplePage.getByRole('document', { name: 'AI suggestion' }).count(), 0, 'no answer is shown');
    holdModel = false;
    held.shift()();
    await samplePage.getByRole('link', { name: 'Mission Control', exact: true }).click();
    await samplePage.waitForSelector('.view--mission');
    await atWork.getByRole('button', { name: 'Let assistants work again' }).click();
    await samplePage.waitForFunction(() => /Assistants can work again/.test(document.activeElement?.textContent ?? ''));

    // Disconnect: back to no model.
    await samplePage.getByRole('link', { name: 'AI assistance' }).click();
    await samplePage.waitForSelector('.view--assistant');
    await samplePage.getByRole('button', { name: 'Disconnect the AI model' }).click();
    await samplePage.waitForFunction(() => /disconnected/.test(document.activeElement?.textContent ?? ''));
  } finally {
    model.close();
  }
  assert.deepEqual(sampleErrors, [], 'no console errors on the sample page');

  await samplePage.getByRole('button', { name: 'Quit Nurse AI OS' }).click();
  assert.equal(await Promise.race([sample.exited, new Promise((r) => setTimeout(() => r('still running'), 10000))]), 0);

  // --- JEV (ADR 0006): off by default, my own key, suggestions only -------
  // JEV is pointed at a stand-in on 127.0.0.1 and its key kept in memory by
  // a launcher that patches the module, since the app takes neither from
  // its environment. A packaged build cannot be patched, so it skips this.
  if (process.env.NURSE_AI_OS_BIN) {
    console.log('JEV journey skipped: it needs the stand-in launcher, which a packaged build has not.');
  } else {
    const JEV_KEY = 'ts-browser-test-key-0123456789';
    /** @type {string[]} */
    const jevRaw = [];
    const jevServer = createServer((req, res) => {
      let raw = '';
      req.on('data', (chunk) => { raw += chunk; });
      req.on('end', () => {
        if (req.headers.authorization !== `Bearer ${JEV_KEY}`) {
          res.writeHead(401);
          res.end();
          return;
        }
        jevRaw.push(raw);
        const body = JSON.parse(raw);
        const text = JSON.stringify(body.state).toLowerCase();
        const ids = Object.keys(body.questions);
        const answers = {};
        for (const [id, q] of Object.entries(body.questions)) {
          if (q.type === 'noul') {
            answers[id] = { type: 'noul', noul: id === 'patient_information' && text.includes('patient') ? 0.95 : 0.02 };
          } else if (q.type === 'choice') {
            const options = Object.keys(q.criteria);
            const pick = text.includes('message') && options.includes('pack_communication') ? 'pack_communication' : options[0];
            const rest = 0.1 / (options.length - 1);
            answers[id] = {
              type: 'choice', choice: pick, confidence: 0.9,
              probabilities: Object.fromEntries(options.map((o) => [o, o === pick ? 0.9 : rest])),
            };
          } else {
            // The last item is the most urgent, so the suggested order differs from the usual one.
            const level = id === ids.at(-1) ? 4 : 1;
            answers[id] = {
              type: 'score', score: level, confidence: 0.85,
              legend: Object.fromEntries(q.criteria.map((c, i) => [String(i + 1), c])),
              probabilities: Object.fromEntries([1, 2, 3, 4].map((i) => [String(i), i === level ? 0.85 : 0.05])),
            };
          }
        }
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ model: body.model, answers, usage: { input_tokens: 64, output_tokens: 0 } }));
      });
    });
    const jevModelRequests = [];
    const jevModel = createServer((req, res) => {
      let raw = '';
      req.on('data', (chunk) => { raw += chunk; });
      req.on('end', () => {
        const body = JSON.parse(raw);
        jevModelRequests.push(body);
        const kept = body.prompt.split('\n').filter((line) => line.startsWith('#') || line.includes('`'));
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ response: kept.join('\n'), done: true }));
      });
    });
    await new Promise((done) => jevServer.listen(0, '127.0.0.1', done));
    await new Promise((done) => jevModel.listen(0, '127.0.0.1', done));
    try {
      const launcher = [
        'import sys',
        'from nurse_manager import app, classifier, credentials',
        'keys = credentials.MemoryKeyStore()',
        'classifier.default_keystore = lambda: keys',
        'classifier.JEV_ENDPOINT = sys.argv[1]',
        'sys.exit(app.main(sys.argv[2:]))',
      ].join('\n');
      const jevApp = await new Promise((resolve, reject) => {
        const child = spawn('python3', ['-c', launcher, `http://127.0.0.1:${jevServer.address().port}/v1/systemone`,
          '--no-browser', '--print-url', '--idle-timeout', '120', '--home', join(work, 'jev')], { env });
        const exited = new Promise((done) => child.on('exit', (code) => done(code)));
        let out = '';
        child.stdout.on('data', (chunk) => {
          out += chunk;
          if (out.includes('\n')) resolve({ child, url: out.split('\n')[0].trim(), exited });
        });
        child.on('error', reject);
      });
      apps.push(jevApp);
      const jevBase = jevApp.url.split('#')[0];
      const jp = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
      const jevErrors = [];
      jp.on('console', (m) => { if (m.type() === 'error') jevErrors.push(m.text()); });
      jp.on('pageerror', (e) => jevErrors.push(e.message));
      const away = [];
      jp.on('request', (r) => { if (!r.url().startsWith(jevBase)) away.push(r.url()); });
      const focused = (pattern) => jp.waitForFunction((source) => new RegExp(source).test(document.activeElement?.textContent ?? ''),
        pattern.source, { timeout: 15000 });
      await jp.goto(jevApp.url);
      await jp.waitForSelector('.view--onboarding');
      await jp.getByRole('button', { name: 'Explore the sample workspace' }).click();
      await jp.waitForSelector('.view--mission');
      assert.equal(await jp.locator('#route').count(), 0, 'no JEV on Mission Control while it is off');
      assert.equal(await jp.getByRole('button', { name: 'Suggest an order with JEV' }).count(), 0);

      // Off by default; what it does, never does, and TypeSafe's terms, before any key.
      await jp.getByRole('link', { name: 'AI assistance' }).click();
      await jp.waitForSelector('.view--assistant');
      const jevRegion = jp.getByRole('region', { name: 'JEV classifier' });
      const off = await jevRegion.textContent();
      assert.match(off, /Not connected.*Nothing is ever sent to JEV/s);
      assert.match(off, /It never writes text/);
      assert.match(off, /never approves, sends, or exports anything, and never lowers a tier/);
      assert.match(off, /no business associate agreement/);
      assert.equal(await jevRegion.getByLabel('Your TypeSafe API key').getAttribute('type'), 'password');
      await jevRegion.getByLabel('Your TypeSafe API key').fill(JEV_KEY);
      await jevRegion.getByLabel('JEV requests per day, at most').fill('50');
      await jevRegion.getByRole('button', { name: 'Connect JEV' }).click();
      await focused(/JEV is connected\. Every job is off/);
      assert.ok(!(await jp.content()).includes(JEV_KEY), 'the key is never shown back');
      const on = await jevRegion.textContent();
      assert.match(on, /Connected.*JEV \(jev-1\.13\.0\).*kept in test memory/s);
      assert.match(on, /JEV requests today: 0 of 50/);
      for (const job of [/^Action review/, /^Refusal check/, /^Routing/, /^Attention order/]) {
        assert.equal(await jevRegion.getByLabel(job).isChecked(), false, `${job} starts off`);
        await jevRegion.getByLabel(job).check();
      }
      await jevRegion.getByRole('button', { name: 'Save jobs' }).click();
      await focused(/JEV's jobs are saved/);
      assert.equal(jevRaw.length, 0, 'connecting and turning jobs on sends nothing to JEV');

      // Routing: a suggestion after a byte-exact preview; the manager chooses.
      await jp.getByRole('link', { name: 'Mission Control', exact: true }).click();
      await jp.waitForSelector('.view--mission');
      const route = jp.getByRole('region', { name: 'Where does this belong?' });
      await route.getByLabel('What do you want to do?').fill('Draft a huddle message about the float process');
      await route.getByRole('button', { name: 'Preview what JEV would see' }).click();
      await jp.waitForFunction(() => document.activeElement?.id === 'route-jev-preview-heading');
      const routeSent = await route.getByLabel('The request JEV would receive').textContent();
      assert.match(routeSent, /Draft a huddle message about the float process/);
      assert.equal(jevRaw.length, 0, 'a preview sends nothing');
      await route.getByRole('button', { name: 'Ask JEV' }).click();
      await jp.waitForFunction(() => document.activeElement?.id === 'route-result');
      assert.equal(jevRaw.length, 1);
      assert.equal(jevRaw[0], routeSent, 'what JEV received is byte for byte what was shown');
      const routeResult = route.locator('#route-result');
      assert.match(await routeResult.textContent(), /JEV suggests: Communication pack.*You choose\./s);
      assert.equal(await routeResult.getByRole('link', { name: 'Communication pack' }).first().getAttribute('href'), '#/packs');
      assert.ok(await routeResult.getByRole('link', { name: 'Library' }).count() >= 1, 'every other place is a click away');

      // Attention order: every item kept, the usual order a click away, and no number shown.
      const judgment = jp.getByRole('region', { name: 'Needs my judgment' });
      const order = () => judgment.locator('li[data-record-id]').evaluateAll((els) => els.map((el) => el.getAttribute('data-record-id')));
      const usual = await order();
      assert.ok(usual.length >= 2, 'the sample has something to order');
      await judgment.getByRole('button', { name: 'Suggest an order with JEV' }).click();
      await jp.waitForFunction(() => document.activeElement?.id === 'order-jev-preview-heading');
      const orderSent = await judgment.getByLabel('The request JEV would receive').textContent();
      for (const item of JSON.parse(orderSent).state.items) {
        assert.deepEqual(Object.keys(item).sort(), ['due', 'item', 'kind', 'title'], 'no owner and no record id is sent');
      }
      await judgment.getByRole('button', { name: 'Ask JEV' }).click();
      await focused(/Shown in the order JEV suggests\. Every item is still here\./);
      assert.equal(jevRaw.at(-1), orderSent);
      assert.deepEqual(await order(), [usual.at(-1), ...usual.slice(0, -1)]);
      assert.doesNotMatch(await judgment.textContent(), /score|confiden|\d+ ?%|0\.\d/i, 'no score or confidence is shown');
      await judgment.getByRole('button', { name: 'Show my usual order' }).click();
      await focused(/Shown in your usual order/);
      assert.deepEqual(await order(), usual);

      // Refusal check: JEV's request is part of the question's preview, and a
      // question it confidently refuses never reaches the AI model.
      await jp.getByRole('link', { name: 'AI assistance' }).click();
      await jp.waitForSelector('.view--assistant');
      await jp.getByLabel('Model name').fill('llama3.2');
      await jp.getByLabel('Model server address').fill(`http://127.0.0.1:${jevModel.address().port}`);
      await jp.getByLabel('Model server address').press('Enter');
      await focused(/Connected to the AI model/);
      await jp.getByRole('link', { name: 'Mission Control', exact: true }).click();
      await jp.waitForSelector('.view--mission');
      await jp.getByRole('region', { name: 'Projects in motion' }).getByRole('link').first().click();
      await jp.waitForSelector('.view--project');
      const think = jp.getByRole('region', { name: 'Think with this project' });
      const ask = async (question) => {
        await think.getByLabel('What do you want to think through?').fill(question);
        await think.getByRole('button', { name: 'Preview what will be sent' }).click();
        await jp.waitForFunction(() => document.activeElement?.id === 'think-preview-heading');
        assert.match(await think.locator('#think-jev-check').textContent(), /JEV checks the question first.*If JEV is confident it finds one, nothing goes to the AI model/s);
        const checkSent = await think.getByLabel('The request JEV would receive').textContent();
        assert.ok(checkSent.includes(JSON.stringify(question).slice(1, -1)), 'the question is in what JEV would receive');
        await think.getByRole('button', { name: 'Send to llama3.2' }).click();
        return checkSent;
      };
      const refusedSent = await ask('Should the patient who fell get a different treatment plan?');
      await focused(/Not sent to the AI model: JEV found patient information in the question\./);
      assert.equal(jevRaw.at(-1), refusedSent);
      assert.equal(jevModelRequests.length, 0, 'the AI model never saw the refused question');
      assert.equal(await jp.getByRole('document', { name: 'AI suggestion' }).count(), 0);
      await ask('What is at risk before the next milestone?');
      await focused(/The AI model answered/);
      assert.equal(jevModelRequests.length, 1, 'a question JEV clears goes on to the AI model');

      // Disconnect: every job off and the key removed; Mission Control is as before.
      await jp.getByRole('link', { name: 'AI assistance' }).click();
      await jp.waitForSelector('.view--assistant');
      assert.match(await jevRegion.textContent(), /JEV requests today: 4 of 50/);
      await jevRegion.getByRole('button', { name: 'Disconnect JEV' }).click();
      await focused(/JEV is disconnected and your key is removed/);
      assert.match(await jevRegion.textContent(), /Not connected/);
      await jp.getByRole('link', { name: 'Mission Control', exact: true }).click();
      await jp.waitForSelector('.view--mission');
      assert.equal(await jp.locator('#route').count(), 0, 'JEV leaves Mission Control when it is disconnected');
      assert.deepEqual(away, [], 'the browser talks only to the app; JEV is reached by the app, after a preview');
      assert.deepEqual(jevErrors, [], 'no console errors on the JEV page');
      await jp.getByRole('button', { name: 'Quit Nurse AI OS' }).click();
      assert.equal(await Promise.race([jevApp.exited, new Promise((r) => setTimeout(() => r('still running'), 10000))]), 0);
    } finally {
      jevServer.close();
      jevModel.close();
    }
  }

  console.log('nurse-manager local app: token, onboarding, session, quit, sample, weekly brief, AI assistance, project questions, feedback, library, learning, contributions, recurring brief, memory, stop control, packs, help and pilot feedback, JEV classifier pass');
} finally {
  await browser?.close();
  for (const app of apps) app.child.kill();
  rmSync(work, { recursive: true, force: true });
}
