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
//
// CHROME_PATH=/path/to/chrome overrides the system Chrome channel (local runs).
// NURSE_AI_OS_BIN=/path/to/nurse-ai-os runs it against a packaged build.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtempSync, rmSync } from 'node:fs';
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
  await samplePage.getByLabel('What was the contribution?').fill('Rewrote the council agenda template (synthetic)');
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
  await samplePage.getByRole('button', { name: 'Save as draft' }).click();
  await samplePage.waitForFunction(() => /Saved “Rewrote the council agenda/.test(document.activeElement?.textContent ?? ''));
  const draft = samplePage.getByRole('region', { name: 'Drafts awaiting evidence (2)' }).getByRole('listitem').filter({ hasText: 'Rewrote the council agenda' });
  assert.match(await draft.textContent(), /Project: Unit Based Council charter refresh.*Shared credit: Unit Based Council members/s);
  await draft.getByRole('button', { name: 'Verify with evidence…' }).click();
  await samplePage.waitForFunction(() => document.activeElement?.tagName === 'TEXTAREA');
  await samplePage.keyboard.type('Template adopted in the council minutes (synthetic). Ask manager@example.org');
  await samplePage.getByRole('button', { name: 'Verify', exact: true }).click();
  await samplePage.waitForSelector('.view--contributions .notice[role="alert"]');
  const evidence = samplePage.getByLabel('What shows it happened?');
  assert.match(await evidence.inputValue(), /Template adopted.*manager@example\.org/);
  await evidence.fill('Template adopted in the council minutes (synthetic).');
  await samplePage.getByRole('button', { name: 'Verify', exact: true }).click();
  await samplePage.waitForFunction(() => /Verified, with your evidence/.test(document.activeElement?.textContent ?? ''));
  assert.match(await samplePage.getByRole('region', { name: 'Verified (2)' }).textContent(),
    /Rewrote the council agenda.*Evidence.*Template adopted in the council minutes/s);
  assert.match(await samplePage.getByRole('list', { name: 'Facts' }).textContent(), /2 verified · 1 draft awaits evidence/);

  // --- AI assistance: connect a model on this computer ------------------
  const modelRequests = [];
  const model = createServer((req, res) => {
    let raw = '';
    req.on('data', (chunk) => { raw += chunk; });
    req.on('end', () => {
      const body = JSON.parse(raw);
      modelRequests.push(body);
      // A well-behaved model: keeps the headings and the cited lines.
      const kept = body.prompt.split('\n').filter((line) => line.startsWith('#') || line.includes('`'));
      const out = JSON.stringify({ response: kept.join('\n'), done: true });
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(out);
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

  console.log('nurse-manager local app: token, onboarding, session, quit, sample, weekly brief, AI assistance, project questions, feedback, library, learning, contributions pass');
} finally {
  await browser?.close();
  for (const app of apps) app.child.kill();
  rmSync(work, { recursive: true, force: true });
}
