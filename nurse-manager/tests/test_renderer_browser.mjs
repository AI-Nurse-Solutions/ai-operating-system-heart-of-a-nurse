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
    'ws.add_task(sys.argv[2], "Sample Manager", status="ready", due_date="2026-10-04")',
    'ws.close()',
  ].join('\n'), sample, INJECTED]);
  const empty = join(work, 'empty');
  python(['-m', 'nurse_manager', 'init', empty, '--name', 'Empty workspace', '--owner', 'Test Manager']);

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
  assert.equal(await page.locator('#workspace-name').textContent(), 'Sample manager workspace (synthetic)');
  for (const name of ["This week's priorities", 'Needs my judgment', 'Projects in motion',
    'Follow-ups due soon', 'Assistants at work', 'Recently accepted outputs', 'Tasks by status']) {
    assert.ok(await page.getByRole('region', { name }).isVisible(), `region "${name}" is named`);
  }
  assert.equal(await page.getByRole('region', { name: "This week's priorities" }).getByRole('listitem').count(), 3);
  const overdue = page.getByRole('region', { name: 'Follow-ups due soon' }).getByRole('listitem').filter({ hasText: 'Overdue' });
  assert.equal(await overdue.count(), 1, 'overdue is stated in text, not color alone');
  assert.match(await page.getByRole('region', { name: 'Assistants at work' }).textContent(), /Unavailable.*No assistant is connected/s);
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
  for (const route of ['mission', 'board', 'table']) {
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

  const errorPage = await open(`${missing.url}#/mission`);
  assert.match(await errorPage.getByRole('alert').textContent(), /no workspace has been created here yet/);
  assert.equal(await errorPage.getByRole('heading', { level: 1 }).textContent(), "Couldn't load Mission Control");
  await errorPage.close();

  assert.deepEqual(errors, [], 'no console errors or CSP violations');
  console.log('nurse-manager renderer: keyboard, names, ids, states, reflow, themes pass');
} finally {
  await browser?.close();
  for (const child of hosts) child.kill();
  rmSync(work, { recursive: true, force: true });
}
