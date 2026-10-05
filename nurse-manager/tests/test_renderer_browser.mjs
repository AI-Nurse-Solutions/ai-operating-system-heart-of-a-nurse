// Manager screens in a real browser (build step 3.5).
//
// Runs the dev host against a sample workspace, an empty workspace, and a
// directory with no workspace, then checks what a manager (and a screen
// reader) actually meets: a keyboard journey through all three views, named
// landmarks and regions, the same record ids in every view, honest empty and
// error states, record text that cannot become markup, reflow at 320px,
// Night Studio, and reduced motion. Any console error or CSP violation fails.
//
// CHROME_PATH=/path/to/chrome overrides the system Chrome channel (local runs).
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const src = fileURLToPath(new URL('../src', import.meta.url));
const env = { ...process.env, PYTHONPATH: src };
const work = mkdtempSync(join(tmpdir(), 'nm-renderer-'));
const TODAY = '2026-09-30';
const INJECTED = '<img src=x onerror="window.__injected=1">Agenda';

const python = (args) => {
  const run = spawnSync('python3', args, { env, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  return run.stdout;
};

/** Start a dev host and resolve with its base URL. */
const host = (workspace) => new Promise((resolve, reject) => {
  const child = spawn('python3', ['-m', 'nurse_manager.devhost', workspace, '--today', TODAY], { env });
  let out = '';
  child.stdout.on('data', (chunk) => {
    out += chunk;
    const line = out.split('\n')[0];
    if (out.includes('\n')) resolve({ child, url: line.trim() });
  });
  child.on('error', reject);
  child.on('exit', (code) => reject(new Error(`devhost exited ${code}`)));
});

const hosts = [];
let browser;
try {
  const sample = join(work, 'sample');
  python(['-m', 'nurse_manager', 'sample', sample]);
  python(['-c', [
    'import sys; from nurse_manager.services import ManagerWorkspace',
    'ws = ManagerWorkspace(sys.argv[1])',
    'ws.add_task(sys.argv[2], "me", status="ready", due_date="2026-10-04")',
    'ubc = ws.store.conn.execute("SELECT id FROM projects WHERE title LIKE ?", ("Unit%",)).fetchone()[0]',
    'ws.add_feedback(ubc, "Council members", "question", sys.argv[2], "2026-09-27")',
    'from nurse_manager.pilot import PilotFeedback',
    'PilotFeedback(ws).add("packs", "idea", sys.argv[2])',
    'ws.close()',
  ].join('\n'), sample, INJECTED]);
  python(['-m', 'nurse_manager', 'brief', sample, '--week', '2026-09-28', '--today', TODAY]);
  const empty = join(work, 'empty');
  python(['-m', 'nurse_manager', 'init', empty, '--name', 'Empty workspace', '--owner', 'me']);

  const main = await host(sample); hosts.push(main.child);
  const blank = await host(empty); hosts.push(blank.child);
  const missing = await host(join(work, 'no-workspace-here')); hosts.push(missing.child);

  browser = await chromium.launch(process.env.CHROME_PATH
    ? { executablePath: process.env.CHROME_PATH, headless: true }
    : { channel: 'chrome', headless: true });

  const errors = [];
  const open = async (url, options = {}) => {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, ...options });
    page.on('console', (m) => { if (m.type() === 'error') errors.push(`${url}: ${m.text()}`); });
    page.on('pageerror', (e) => errors.push(`${url}: ${e.message}`));
    await page.goto(url);
    await page.waitForSelector('main[aria-busy="false"]');
    return page;
  };

  // --- Mission Control: what needs my attention? ------------------------
  const page = await open(`${main.url}#/mission`);
  assert.equal(await page.title(), 'Mission Control — Nurse AI OS');
  assert.equal(await page.getByRole('heading', { level: 1 }).textContent(), 'Mission Control');
  assert.ok(await page.getByRole('note').filter({ hasText: 'Sample workspace' }).isVisible(), 'sample data is announced');
  assert.equal(await page.getByRole('button', { name: 'Quit Nurse AI OS' }).isVisible(), false,
    'the read-only development host offers no Quit');
  assert.equal(await page.locator('#workspace-name').textContent(), 'Sample manager workspace (synthetic)');
  for (const name of ["This week's priorities", 'Needs my judgment', 'Projects in motion',
    'Follow-ups due soon', 'Assistants at work', 'Recently accepted outputs', 'Tasks by status']) {
    assert.ok(await page.getByRole('region', { name }).isVisible(), `region "${name}" is named`);
  }
  assert.equal(await page.getByRole('region', { name: "This week's priorities" }).getByRole('listitem').count(), 3);
  const overdue = page.getByRole('region', { name: 'Follow-ups due soon' }).getByRole('listitem').filter({ hasText: 'Overdue' });
  assert.equal(await overdue.count(), 1, 'overdue is stated in text, not color alone');
  const atWork = page.getByRole('region', { name: 'Assistants at work' });
  assert.match(await atWork.textContent(), /No assistant is connected.*Read-only.*Stopping assistants is available in the Nurse AI OS app/s);
  assert.equal(await atWork.getByRole('button').count(), 0, 'the read-only host offers no stop switch');
  assert.equal(await page.locator('text=/\\d+\\s?%/').count(), 0, 'no percentages without a denominator');

  // --- Keyboard journey --------------------------------------------------
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Skip to main content');
  await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'main', 'skip link moves focus to main');
  assert.equal(new URL(page.url()).hash, '#/mission', 'the skip link does not change the route');
  for (const [linkName, heading, hash] of [['Board', 'Board', '#/board'], ['Table', 'Tasks', '#/table'], ['Mission Control', 'Mission Control', '#/mission']]) {
    await page.getByRole('link', { name: linkName, exact: true }).focus();
    await page.keyboard.press('Enter');
    try {
      await page.waitForFunction((h) => document.activeElement?.tagName === 'H1' && document.activeElement.textContent === h, heading, { timeout: 10000 });
    } catch (error) {
      const state = await page.evaluate(() => ({
        active: `${document.activeElement?.tagName}#${document.activeElement?.id} "${(document.activeElement?.textContent || '').slice(0, 40)}"`,
        hash: location.hash,
        busy: document.querySelector('main')?.getAttribute('aria-busy'),
        h1: document.querySelector('h1')?.textContent,
      }));
      throw new Error(`focus did not reach "${heading}" after ${linkName}: ${JSON.stringify(state)}; page errors: ${JSON.stringify(errors)}`, { cause: error });
    }
    assert.equal(new URL(page.url()).hash, hash);
    assert.equal(await page.getByRole('link', { name: linkName, exact: true }).getAttribute('aria-current'), 'page');
    assert.equal(await page.title(), `${heading} — Nurse AI OS`);
  }

  // --- Same ids and counts in every view ---------------------------------
  const mission = await page.evaluate(() => Object.fromEntries(
    [...document.querySelectorAll('dd[data-status]')].map((dd) => [dd.getAttribute('data-status'), Number(dd.textContent)])));
  await page.getByRole('link', { name: 'Board', exact: true }).click();
  await page.waitForSelector('.view--board');
  const boardIds = await page.$$eval('.task-card', (els) => els.map((e) => e.getAttribute('data-record-id')).sort());
  const boardCounts = await page.$$eval('.board__column', (cols) => Object.fromEntries(
    cols.map((c) => [c.getAttribute('data-status'), c.querySelectorAll('.task-card').length])));
  assert.deepEqual(boardCounts, mission, 'board and Mission Control agree on counts');
  assert.ok(await page.getByRole('region', { name: /Ready \(\d+ tasks?\)/ }).isVisible(), 'columns are named with their counts');
  const blocked = page.getByRole('article', { name: 'Book room for charter review meeting' });
  assert.match(await blocked.textContent(), /Blocked: Waiting for the cadence decision/);

  // Record text is text: the injected title renders literally and never runs.
  assert.ok(await page.getByRole('article', { name: INJECTED }).isVisible(), 'markup in a title is shown as text');
  assert.equal(await page.evaluate(() => window.__injected), undefined, 'markup in a title never executes');
  assert.equal(await page.locator('.task-card img').count(), 0);

  await page.getByRole('link', { name: 'Add work', exact: true }).click();
  await page.waitForSelector('.view--capture');
  assert.match(await page.locator('main').textContent(), /development preview is read-only/);
  assert.equal(await page.locator('form[data-capture]').count(), 0);

  // Learning and Growth: facts, not scores; read-only here.
  await page.getByRole('link', { name: 'Learning and Growth' }).click();
  await page.waitForSelector('.view--learning');
  assert.equal(await page.title(), 'Learning and Growth — Nurse AI OS');
  for (const name of ['In progress (1)', 'Planned (1)', 'Completed (1)']) {
    assert.ok(await page.getByRole('region', { name }).isVisible(), `${name} section`);
  }
  assert.match(await page.getByRole('list', { name: 'This year' }).textContent(), /1 item completed this year \(3 hours\)/);
  assert.match(await page.getByRole('region', { name: 'Completed (1)' }).textContent(), /Takeaway.*Open each meeting with its decision/s);
  assert.equal(await page.locator('.view--learning button').count(), 0, 'no learning writes on the dev host');
  assert.equal(await page.locator('main').locator('text=/\\d+\\s?%/').count(), 0, 'no percentages');

  // Contributions: drafts then verified, shared credit shown, read-only here.
  await page.getByRole('link', { name: 'Contributions' }).click();
  await page.waitForSelector('.view--contributions');
  assert.equal(await page.title(), 'Contributions — Nurse AI OS');
  const drafts = page.getByRole('region', { name: 'Drafts awaiting evidence (1)' });
  assert.match(await drafts.textContent(), /Designed the five-part huddle format.*Project: Huddle format pilot.*Shared credit: Charge nurse; Educator/s);
  assert.match(await page.getByRole('region', { name: 'Verified (1)' }).textContent(), /Evidence.*Session outline and sign-in count/s);
  assert.match(await page.getByRole('list', { name: 'Facts' }).textContent(), /1 contribution from this year verified/);
  await drafts.getByRole('link', { name: 'Huddle format pilot' }).waitFor();
  assert.equal(await page.locator('.view--contributions button').count(), 0, 'no contribution writes on the dev host');
  assert.equal(await page.locator('main').locator('text=/\\d+\\s?%/').count(), 0, 'no percentages');

  // Help and feedback: what to know, and pilot feedback that is read-only here.
  await page.getByRole('link', { name: 'Help and feedback' }).click();
  await page.waitForSelector('.view--help');
  assert.equal(await page.title(), 'Help and feedback — Nurse AI OS');
  assert.equal(await page.locator('[data-route="help"]').getAttribute('aria-current'), 'page');
  assert.match(await page.getByRole('region', { name: 'What to know' }).textContent(),
    /No AI model runs by default.*It does not detect people’s names\./s);
  const pilotHere = page.getByRole('region', { name: 'Pilot feedback', exact: true });
  assert.match(await pilotHere.textContent(), /Packs · Idea.*Not in an export yet.*Read-only.*available in the Nurse AI OS app/s);
  assert.match(await pilotHere.getByRole('list', { name: 'Your pilot feedback' }).textContent(),
    /<img src=x onerror="window\.__injected=1">Agenda/, 'feedback text is shown as text');
  assert.equal(await page.locator('.view--help button, .view--help form').count(), 0, 'no pilot feedback writes on the dev host');
  assert.equal(await page.evaluate(() => window.__injected), undefined, 'markup in feedback never executes');

  // Memory: in use, expired, excluded, with who wrote it; read-only here.
  await page.getByRole('link', { name: 'Memory' }).click();
  await page.waitForSelector('.view--memory');
  assert.equal(await page.title(), 'Memory — Nurse AI OS');
  assert.match(await page.getByRole('region', { name: 'In use (2)' }).textContent(), /Lead with the decisions.*All work.*Written by me.*Huddles stay at five minutes.*Project: Huddle format pilot/s);
  assert.match(await page.getByRole('region', { name: 'Excluded (1)' }).textContent(), /budget talks/);
  assert.equal(await page.locator('.view--memory button').count(), 0, 'no memory changes on the dev host');

  // Packs: maintainer and review dates for each; documents open read-only here.
  await page.getByRole('link', { name: 'Packs' }).click();
  await page.waitForSelector('.view--packs');
  assert.equal(await page.title(), 'Packs — Nurse AI OS');
  for (const name of ['Committee pack 1.0.0', 'Communication pack 1.0.0', 'Education pack 1.0.0']) {
    const pack = page.getByRole('region', { name });
    assert.match(await pack.textContent(), /Current.*Maintained by.*Project steward \(GOVERNANCE\.md\).*Last reviewed.*Next review by/s, name);
  }
  assert.equal(await page.getByRole('button', { name: 'Start a draft' }).count(), 0, 'no drafts started on the dev host');
  const packDocs = page.getByRole('region', { name: 'Your documents (1)' });
  await packDocs.getByRole('link', { name: 'Education Plan / Lesson Plan — Fall education calendar' }).click();
  await page.waitForSelector('.view--document');
  assert.equal(await page.title(), 'Education Plan / Lesson Plan — Fall education calendar — Nurse AI OS');
  assert.equal(await page.getByRole('link', { name: 'Packs', exact: true }).getAttribute('aria-current'), 'page');
  assert.match(await page.locator('.brief-text').textContent(), /SYNTHETIC EXAMPLE.*DRAFT — started from a pack template.*Before you use this.*Needs assessment/s);
  assert.equal(await page.locator('.view--document button').count(), 0, 'no edits or acceptance on the dev host');
  await page.goto(`${main.url}#/document/art-000000000000`);
  await page.waitForSelector('.view--error');
  assert.match(await page.getByRole('alert').textContent(), /not in this workspace/);

  // The Library: every source, overdue reviews first, read-only here.
  await page.getByRole('link', { name: 'Library' }).click();
  await page.waitForSelector('.view--library');
  assert.equal(await page.title(), 'Library — Nurse AI OS');
  const libraryRows = page.locator('.view--library tbody tr');
  assert.equal(await libraryRows.count(), 3);
  assert.match(await libraryRows.first().textContent(), /Council charter template.*Review overdue since 2026-09-01/s);
  assert.match(await page.locator('.view--library').textContent(), /1 source is past its review date/);
  assert.match(await page.locator('.view--library').textContent(), /Whole workspace/);
  assert.equal(await page.getByLabel('Title').count(), 0, 'no add-source form on the dev host');
  assert.equal(await page.locator('.view--library a[href^="http"], .view--library a[href^="synthetic"]').count(), 0,
    'references are text, never links');
  await page.setViewportSize({ width: 320, height: 800 });
  const libraryOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(libraryOverflow <= 0, `library reflows at 320px (overflow ${libraryOverflow}px)`);
  await page.setViewportSize({ width: 1280, height: 900 });
  await libraryRows.first().getByRole('link').click();
  await page.waitForSelector('.view--project');
  assert.match(await page.locator('h1').textContent(), /Unit Based Council charter refresh/);

  // The weekly brief is read-only here, and its record text stays text.
  await page.getByRole('link', { name: 'Weekly brief' }).click();
  await page.waitForSelector('.view--brief');
  assert.equal(await page.title(), 'Weekly brief — Nurse AI OS');
  assert.match(await page.locator('.view--brief').textContent(), /Read-only.*available in the Nurse AI OS app/s);
  assert.equal(await page.getByRole('button', { name: 'Draft from my records' }).count(), 0, 'no writes on the dev host');
  assert.match(await page.getByRole('region', { name: 'Every week' }).textContent(),
    /Off.*runs only while Nurse AI OS is open on this computer.*never an AI model/s);
  assert.equal(await page.locator('#schedule-enabled').count(), 0, 'no schedule settings on the dev host');
  const briefDoc = page.getByRole('document', { name: 'Weekly brief, version 1' });
  assert.match(await briefDoc.textContent(), /<img src=x onerror="window\.__injected=1">Agenda/);
  assert.equal(await briefDoc.locator('img').count(), 0);
  assert.ok(await briefDoc.getByRole('heading', { name: "This week's priorities" }).isVisible(), 'Markdown headings render as headings');
  assert.equal(await page.evaluate(() => window.__injected), undefined, 'markup in the brief never executes');
  await page.getByRole('link', { name: 'AI assistance' }).click();
  await page.waitForSelector('.view--assistant');
  assert.equal(await page.getByLabel('Model name').count(), 0, 'no AI settings form on the dev host');
  assert.match(await page.getByRole('region', { name: 'Right now' }).textContent(), /No AI model/);
  // JEV (ADR 0006): its facts are readable here; connecting it is not.
  const jev = page.getByRole('region', { name: 'JEV classifier' });
  assert.match(await jev.textContent(), /Not connected.*It never writes text.*TypeSafe.*Read-only/s);
  assert.equal(await page.getByLabel('Your TypeSafe API key').count(), 0, 'no key field on the dev host');
  await page.getByRole('link', { name: 'Board', exact: true }).click();
  await page.waitForSelector('.view--board');

  await page.getByRole('link', { name: 'Table', exact: true }).click();
  await page.waitForSelector('.view--table');
  const tableIds = await page.$$eval('tbody tr', (rows) => rows.map((r) => r.getAttribute('data-record-id')).sort());
  assert.deepEqual(tableIds, boardIds, 'board and table show the same task ids');

  // --- Table sorting by keyboard, announced by aria-sort -----------------
  const table = page.getByRole('table', { name: /All tasks, sorted by Due date, ascending/ });
  assert.ok(await table.isVisible(), 'the table is named by its caption');
  const dueHeader = page.getByRole('columnheader', { name: /Due date/ });
  assert.equal(await dueHeader.getAttribute('aria-sort'), 'ascending');
  const dueDates = async () => page.$$eval('tbody tr td.cell--date', (tds) => tds.map((t) => t.textContent));
  const ascending = await dueDates();
  assert.equal(ascending.at(-1), '—', 'tasks without a date sort last');
  await page.getByRole('button', { name: /Due date/ }).focus();
  await page.keyboard.press('Enter');
  assert.equal(await dueHeader.getAttribute('aria-sort'), 'descending');
  assert.ok(await page.evaluate(() => document.activeElement?.getAttribute('data-column') === 'due_date'), 'focus stays on the sort button');
  const descending = await dueDates();
  assert.equal(descending.at(-1), '—', 'blanks stay last when descending');
  assert.deepEqual(descending.slice(0, -1), [...ascending.slice(0, -1)].reverse());
  await page.getByRole('button', { name: /^Owner/ }).click();
  assert.equal(await page.getByRole('columnheader', { name: /Owner/ }).getAttribute('aria-sort'), 'ascending');
  assert.equal(await dueHeader.getAttribute('aria-sort'), 'none');

  // --- Project dashboard: what will move this initiative forward? --------
  await page.getByRole('link', { name: 'Mission Control', exact: true }).click();
  await page.waitForSelector('.view--mission');
  const projectLink = page.getByRole('link', { name: 'Unit Based Council charter refresh' });
  await projectLink.focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'H1'
    && document.activeElement.textContent === 'Unit Based Council charter refresh', null, { timeout: 10000 });
  assert.match(new URL(page.url()).hash, /^#\/project\/prj-[0-9a-f]{12}$/);
  assert.equal(await page.title(), 'Unit Based Council charter refresh — Nurse AI OS');
  assert.ok(await page.getByRole('navigation', { name: 'Breadcrumb' }).isVisible());
  for (const name of ['Purpose', 'Readiness', 'Decisions', 'Resources', 'Evidence of completed work', 'Tasks']) {
    assert.ok(await page.getByRole('region', { name, exact: true }).isVisible(), `dashboard region "${name}" is named`);
  }
  assert.match(await page.locator('.view-subtitle').first().textContent(), /Accountable owner: me/);
  const readiness = await page.getByRole('region', { name: 'Readiness', exact: true }).textContent();
  assert.match(readiness, /Next milestone: Charter draft to council on 2026-10-07/);
  assert.match(readiness, /3 open tasks · 0 completed/);
  assert.match(readiness, /1 task blocked/);
  assert.match(readiness, /1 decision waiting on you/);
  assert.match(readiness, /1 active task has no next action written down/);
  assert.equal(await page.locator('main').locator('text=/\\d+\\s?%/').count(), 0, 'readiness is facts, not a percentage');
  assert.match(await page.getByRole('region', { name: 'Resources', exact: true }).textContent(), /Review overdue since 2026-09-01/);
  assert.match(await page.getByRole('region', { name: 'Decisions', exact: true }).textContent(), /No decisions recorded/);
  const projectIds = await page.$$eval('.view--project tbody tr', (rows) => rows.map((r) => r.getAttribute('data-record-id')));
  assert.equal(projectIds.length, 3);
  assert.ok(projectIds.every((id) => boardIds.includes(id)), 'dashboard tasks are the same records as the board');
  assert.match(await page.getByRole('region', { name: 'Think with this project' }).textContent(),
    /Read-only.*Asking is available in the Nurse AI OS app/s);
  assert.equal(await page.getByLabel('What do you want to think through?').count(), 0, 'no question box on the dev host');
  assert.match(await page.getByRole('region', { name: 'Notes (0)' }).textContent(), /No notes yet/);
  const feedbackRegion = page.getByRole('region', { name: /^Feedback \(\d+ open\)$/ });
  assert.match(await feedbackRegion.textContent(), /Council members.*<img src=x onerror/s, 'feedback text stays text');
  assert.equal(await feedbackRegion.locator('img').count(), 0);
  assert.equal(await feedbackRegion.getByRole('button').count(), 0, 'no feedback writes on the dev host');
  assert.match(readiness, /feedback items? (is|are) still open/);
  const projectTable = page.getByRole('table', { name: /Unit Based Council charter refresh tasks, sorted by Due date, ascending/ });
  assert.ok(await projectTable.isVisible());
  await page.getByRole('button', { name: /^Task/ }).click();
  assert.equal(await page.getByRole('columnheader', { name: /^Task/ }).getAttribute('aria-sort'), 'ascending');
  await page.getByRole('link', { name: '← Mission Control' }).focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'H1'
    && document.activeElement.textContent === 'Mission Control', null, { timeout: 10000 });

  // --- Night Studio and reduced motion -----------------------------------
  const toggle = page.getByRole('button', { name: 'Night Studio' });
  await toggle.click();
  assert.equal(await toggle.getAttribute('aria-pressed'), 'true');
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'night');
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--nm-canvas').trim()), '#10201E');
  await page.reload();
  await page.waitForSelector('main[aria-busy="false"]');
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'night', 'the choice persists');
  await toggle.click();
  await page.close();

  const calm = await open(`${main.url}#/board`, { reducedMotion: 'reduce' });
  assert.equal(await calm.$eval('.task-card', (el) => getComputedStyle(el).transitionDuration), '0s');
  await calm.close();

  // --- Reflow at 320px (WCAG 1.4.10) --------------------------------------
  const reflowProject = await open(`${main.url}#/mission`);
  const someProject = await reflowProject.$eval('.card__title a', (a) => a.getAttribute('href'));
  await reflowProject.close();
  for (const route of ['mission', 'board', 'table', 'help', 'capture', someProject.replace('#/', '')]) {
    const narrow = await open(`${main.url}#/${route}`, { viewport: { width: 320, height: 800 } });
    const overflow = await narrow.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 0, `${route} reflows at 320px (overflow ${overflow}px)`);
    await narrow.close();
  }

  // --- Honest empty and error states -------------------------------------
  const emptyPage = await open(`${blank.url}#/mission`);
  assert.equal(await emptyPage.getByRole('note').isVisible(), false, 'no sample banner for a real workspace');
  assert.match(await emptyPage.getByRole('region', { name: "This week's priorities" }).textContent(), /No priorities set/);
  assert.match(await emptyPage.getByRole('region', { name: 'Projects in motion' }).textContent(), /No active projects/);
  await emptyPage.getByRole('link', { name: 'Table', exact: true }).click();
  await emptyPage.waitForSelector('.view--table');
  assert.match(await emptyPage.locator('main').textContent(), /No tasks yet/);
  await emptyPage.close();

  // Withdrawn is a terminal state, visible on the board and table without
  // implying that the work was completed or needs follow-up.
  python(['-c', [
    'import sys; from nurse_manager.services import ManagerWorkspace',
    'ws = ManagerWorkspace(sys.argv[1])',
    'task = ws.add_task("Withdrawn planning exercise", "me", status="ready")',
    'ws.withdraw_task(task, "The exercise ended")',
    'ws.close()',
  ].join('\n'), empty]);
  for (const width of [1280, 320]) {
    const withdrawnBoard = await open(`${blank.url}#/board`, { viewport: { width, height: 800 } });
    assert.ok(await withdrawnBoard.getByRole('heading', { name: 'Withdrawn (1 task)', exact: true }).isVisible());
    assert.match(await withdrawnBoard.locator('main').textContent(), /Withdrawn planning exercise/);
    assert.ok(await withdrawnBoard.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
    await withdrawnBoard.getByRole('link', { name: 'Table', exact: true }).click();
    await withdrawnBoard.waitForSelector('.view--table');
    assert.match(await withdrawnBoard.locator('tbody').textContent(), /Withdrawn planning exercise.*Withdrawn/s);
    await withdrawnBoard.close();
  }

  const unknownProject = await open(`${main.url}#/project/prj-000000000000`);
  assert.match(await unknownProject.getByRole('alert').textContent(), /not in this workspace/);
  assert.equal(await unknownProject.getByRole('heading', { level: 1 }).textContent(), "Couldn't load Project");
  await unknownProject.close();
  const malformed = await browser.newPage();
  const malformedErrors = [];
  malformed.on('pageerror', (e) => malformedErrors.push(e.message));
  await malformed.goto(`${main.url}#/project/not-an-id`);
  await malformed.waitForSelector('main[aria-busy="false"]');
  assert.match(await malformed.getByRole('alert').textContent(), /id must be a project record id/, 'a malformed id is refused, not guessed');
  assert.deepEqual(malformedErrors, []);
  // A broken percent escape is refused like any other malformed id, never a page error.
  for (const route of ['document', 'project']) {
    await malformed.goto(`${main.url}#/${route}/%`);
    await malformed.reload();
    await malformed.waitForSelector('main[aria-busy="false"]');
    assert.match(await malformed.getByRole('alert').textContent(), new RegExp(`id must be a ${route} record id`), route);
  }
  assert.deepEqual(malformedErrors, [], 'no page error for a broken escape');
  await malformed.close();

  // Opened directly on Packs or a document, a sample workspace still says it is one.
  for (const route of ['#/packs', '#/document/' + await (async () => {
    const listing = await (await fetch(new URL("/ipc/packs", main.url))).json();
    return listing.data.documents[0].id;
  })()]) {
    const direct = await open(`${main.url}${route}`);
    await direct.waitForSelector('main[aria-busy="false"]');
    assert.ok(await direct.getByRole('note').filter({ hasText: 'Sample workspace' }).isVisible(), `${route} announces sample data`);
    await direct.close();
  }

  const errorPage = await open(`${missing.url}#/mission`);
  assert.match(await errorPage.getByRole('alert').textContent(), /no workspace has been created here yet/);
  assert.equal(await errorPage.getByRole('heading', { level: 1 }).textContent(), "Couldn't load Mission Control");
  await errorPage.close();

  assert.deepEqual(errors, [], 'no console errors or CSP violations');
  console.log('nurse-manager renderer: keyboard, names, ids, project dashboard, states, reflow, themes, packs, help pass');
} finally {
  await browser?.close();
  for (const child of hosts) child.kill();
  rmSync(work, { recursive: true, force: true });
}
